"""
Geracao de relatorios de auditoria de IA.

Este modulo gera relatorios de auditoria que avaliam:
    - Robustez do modelo sob perturbacoes
    - Estabilidade das explicacoes (Grad-CAM)
    - Conformidade com requisitos de rastreabilidade
    - Recomendacoes para melhoria

Os relatorios podem ser gerados em formato texto ou JSON.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import select

from config import DATABASE_DSN, MINIO_ACCESS_KEY, MINIO_BUCKET, MINIO_ENDPOINT, MINIO_SECRET_KEY
from persistence import (
    AuditTrail, DatabaseClient, Embedding, Experiment, GradCam,
    Image as ImageModel, Inference, MediaAsset, PerturbationComparison, SimilarityRecord,
)
from storage import MinIOClient


@dataclass
class AuditFinding:
    """Achado individual de auditoria.
    
    Atributos:
        severity: nivel de severidade (CRITICAL, HIGH, MODERATE, LOW)
        category: categoria do achado
        message: descricao do achado
        inference_id: ID da inferencia relacionada
        details: detalhes adicionais
    """
    severity: str
    category: str
    message: str
    inference_id: Optional[str] = None
    details: dict = field(default_factory=dict)


@dataclass
class AuditReport:
    """Relatorio completo de auditoria de um experimento.
    
    Contem informacoes sobre robustez, conformidade,
    achados e recomendacoes.
    """
    experiment_id: str
    generated_at: str
    experiment_name: str = ""
    dataset_name: str = ""
    model_version: str = "resnet50-imagenet1k-v2"
    total_images: int = 0
    total_inferences: int = 0
    total_variants: int = 0
    storage: dict = field(default_factory=dict)
    robustness: dict = field(default_factory=dict)
    findings: list = field(default_factory=list)
    compliance: dict = field(default_factory=dict)
    recommendations: list = field(default_factory=list)


def _count_rows(db: DatabaseClient, model) -> int:
    from sqlalchemy import func
    result = db.scalar(select(func.count()).select_from(model))
    return result or 0


def _storage_bytes(storage: MinIOClient) -> int:
    total = 0
    for obj in storage.client.list_objects(MINIO_BUCKET, recursive=True):
        total += obj.size or 0
    return total


def generate_audit_report(
    experiment_id: str,
    db: Optional[DatabaseClient] = None,
    storage: Optional[MinIOClient] = None,
) -> AuditReport:
    db = db or DatabaseClient(DATABASE_DSN)
    storage = storage or MinIOClient(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        bucket=MINIO_BUCKET,
    )

    exp_row = db.scalar(select(Experiment).where(Experiment.experiment_id == experiment_id))
    if not exp_row:
        raise ValueError(f"Experiment {experiment_id} not found")

    images = db.query(
        select(ImageModel).where(
            ImageModel.image_id.in_(
                select(Inference.image_id).where(Inference.experiment_id == experiment_id)
            )
        )
    )
    image_ids = [img[0].image_id for img in images]

    inferences = db.query(
        select(Inference).where(Inference.experiment_id == experiment_id)
    )
    inference_ids = [inf[0].inference_id for inf in inferences]

    comparisons = db.query(
        select(PerturbationComparison).where(
            PerturbationComparison.baseline_inference_id.in_(inference_ids)
        )
    )

    storage_bytes = _storage_bytes(storage)
    embedding_count = _count_rows(db, Embedding)
    gradcam_count = _count_rows(db, GradCam)
    media_count = _count_rows(db, MediaAsset)
    audit_count = _count_rows(db, AuditTrail)
    similarity_count = _count_rows(db, SimilarityRecord)

    noise_stats = {}
    for comp in comparisons:
        c = comp[0]
        nt = c.noise_type
        if nt not in noise_stats:
            noise_stats[nt] = {"total": 0, "class_changed": 0, "overlap_sum": 0.0, "conf_delta_sum": 0.0}
        noise_stats[nt]["total"] += 1
        noise_stats[nt]["class_changed"] += 1 if c.class_changed else 0
        noise_stats[nt]["overlap_sum"] += c.gradcam_overlap or 0
        noise_stats[nt]["conf_delta_sum"] += c.confidence_delta or 0

    for nt in noise_stats:
        n = noise_stats[nt]["total"]
        noise_stats[nt]["class_change_pct"] = round(noise_stats[nt]["class_changed"] / n * 100, 1) if n else 0
        noise_stats[nt]["avg_overlap"] = round(noise_stats[nt]["overlap_sum"] / n, 4) if n else 0
        noise_stats[nt]["avg_conf_delta"] = round(noise_stats[nt]["conf_delta_sum"] / n, 4) if n else 0

    findings = []
    for comp in comparisons:
        c = comp[0]
        if c.class_changed:
            findings.append(AuditFinding(
                severity="CRITICAL",
                category="class_instability",
                message=f"Classe alterada sob {c.noise_type}",
                inference_id=c.perturbed_inference_id,
                details={"noise_type": c.noise_type, "overlap": c.gradcam_overlap},
            ))
        elif (c.gradcam_overlap or 0) < 0.4:
            findings.append(AuditFinding(
                severity="HIGH",
                category="explanation_instability",
                message=f"Explicação instável sob {c.noise_type} (overlap={c.gradcam_overlap:.3f})",
                inference_id=c.perturbed_inference_id,
                details={"noise_type": c.noise_type, "overlap": c.gradcam_overlap},
            ))
        elif (c.confidence_delta or 0) < -0.3:
            findings.append(AuditFinding(
                severity="MODERATE",
                category="confidence_degradation",
                message=f"Confiança degradou sob {c.noise_type} (delta={c.confidence_delta:.3f})",
                inference_id=c.perturbed_inference_id,
                details={"noise_type": c.noise_type, "delta": c.confidence_delta},
            ))

    critical = sum(1 for f in findings if f.severity == "CRITICAL")
    high = sum(1 for f in findings if f.severity == "HIGH")

    compliance = {
        "audit_trail_complete": audit_count > 0,
        "all_gradcams_persisted": gradcam_count >= len(inference_ids),
        "all_embeddings_persisted": embedding_count >= len(inference_ids),
        "all_media_persisted": media_count >= len(inference_ids) * 2,
        "audit_entries": audit_count,
    }

    recommendations = []
    if critical > 0:
        recommendations.append(f"{critical} inferências com mudança de classe — revisão humana obrigatória")
    if high > 0:
        recommendations.append(f"{high} inferências com explicação instável — revisão recomendada")
    unstable = [nt for nt, s in noise_stats.items() if s["avg_overlap"] < 0.5]
    if unstable:
        recommendations.append(f"Perturbações com baixa estabilidade explicativa: {', '.join(unstable)}")
    if not compliance["audit_trail_complete"]:
        recommendations.append("Ativar auditoria completa para rastreabilidade")

    # Verifica modo de busca utilizado nos registros de auditoria
    search_mode_used = "unknown"
    audit_entries = db.query(
        select(AuditTrail).where(
            AuditTrail.entity_type == 'experiment',
            AuditTrail.action == 'completed',
            AuditTrail.entity_id == experiment_id,
        )
    )
    if audit_entries:
        details = audit_entries[0][0].details or {}
        search_mode_used = details.get('search_mode', 'global')

    return AuditReport(
        experiment_id=experiment_id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        experiment_name=exp_row.name,
        dataset_name="custom",
        total_images=len(image_ids),
        total_inferences=len(inference_ids),
        total_variants=len(noise_stats),
        storage={
            "total_bytes": storage_bytes,
            "total_mb": round(storage_bytes / (1024 * 1024), 2),
            "embeddings": embedding_count,
            "gradcams": gradcam_count,
            "media_assets": media_count,
        },
        robustness={
            "by_noise_type": noise_stats,
            "total_comparisons": len(comparisons),
            "critical_findings": critical,
            "high_findings": high,
            "search_mode": search_mode_used,
        },
        findings=[{
            "severity": f.severity,
            "category": f.category,
            "message": f.message,
            "inference_id": f.inference_id,
            "details": f.details,
        } for f in findings],
        compliance=compliance,
        recommendations=recommendations,
    )


def format_text_report(report: AuditReport) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("RELATORIO DE AUDITORIA DE IA")
    lines.append("=" * 60)
    lines.append(f"Experimento: {report.experiment_name} ({report.experiment_id})")
    lines.append(f"Gerado em:   {report.generated_at}")
    lines.append(f"Modelo:      {report.model_version}")
    lines.append("")
    lines.append("RESUMO OPERACIONAL")
    lines.append("-" * 40)
    lines.append(f"  Imagens processadas:    {report.total_images}")
    lines.append(f"  Total de inferências:  {report.total_inferences}")
    lines.append(f"  Variantes testadas:     {report.total_variants}")
    lines.append(f"  Armazenamento total:    {report.storage.get('total_mb', 0)} MB")
    lines.append(f"  Embeddings indexados:   {report.storage.get('embeddings', 0)}")
    lines.append(f"  Grad-CAMs persistidos:  {report.storage.get('gradcams', 0)}")
    lines.append("")
    lines.append("ROBUSTEZ EXPLICATIVA")
    lines.append("-" * 40)
    search_mode = report.robustness.get("search_mode", "unknown")
    lines.append(f"  Modo de busca:         {search_mode}")
    if search_mode == "filtered":
        lines.append("  (filtrado por classe prevista - comparacoes consistentes)")
    elif search_mode == "global":
        lines.append("  (busca global - avaliacao de embeddings entre categorias)")
    lines.append("")
    by_noise = report.robustness.get("by_noise_type", {})
    for nt, stats in by_noise.items():
        lines.append(f"  {nt}:")
        lines.append(f"    Overlap médio:       {stats['avg_overlap']}")
        lines.append(f"    Δ Confiança médio:   {stats['avg_conf_delta']}")
        lines.append(f"    Mudança de classe:    {stats['class_change_pct']}%")
    lines.append("")
    lines.append("ACHADOS")
    lines.append("-" * 40)
    if not report.findings:
        lines.append("  Nenhum achado crítico.")
    for f in report.findings:
        lines.append(f"  [{f['severity']}] {f['message']}")
    lines.append("")
    lines.append("CONFORMIDADE")
    lines.append("-" * 40)
    for k, v in report.compliance.items():
        status = "SIM" if v else "NAO"
        if isinstance(v, int):
            status = str(v)
        lines.append(f"  {k}: {status}")
    lines.append("")
    lines.append("RECOMENDAÇÕES")
    lines.append("-" * 40)
    if not report.recommendations:
        lines.append("  Nenhuma recomendação adicional.")
    for r in report.recommendations:
        lines.append(f"  - {r}")
    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def save_report(report: AuditReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "experiment_id": report.experiment_id,
        "generated_at": report.generated_at,
        "experiment_name": report.experiment_name,
        "model_version": report.model_version,
        "total_images": report.total_images,
        "total_inferences": report.total_inferences,
        "total_variants": report.total_variants,
        "storage": report.storage,
        "robustness": report.robustness,
        "findings": report.findings,
        "compliance": report.compliance,
        "recommendations": report.recommendations,
    }
    path = output_dir / f"audit_{report.experiment_id[:8]}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
