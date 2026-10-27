"""
Avaliacao de risco de interpretabilidade.

Este modulo fornece funcoes para avaliar o risco associado
as explicacoes do modelo sob diferentes perturbacoes.

Niveis de risco:
    - CRITICAL: classe alterada sob perturbacao
    - HIGH: explicacao instavel (overlap < 0.4)
    - MODERATE: confianca degradou significativamente
    - LOW: decisao estavel
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RiskAssessment:
    """Avaliacao de risco para uma variante perturbada.
    
    Atributos:
        noise_type: tipo de ruido aplicado
        gradcam_overlap: IoU entre Grad-CAM baseline e perturbado
        confidence_delta: variacao de confianca
        class_changed: se a classe foi alterada
        embedding_similarity: similaridade dos embeddings
        risk_level: nivel de risco (CRITICAL, HIGH, MODERATE, LOW)
        recommendation: recomendacao baseada no risco
    """
    noise_type: str
    gradcam_overlap: float
    confidence_delta: float
    class_changed: bool
    embedding_similarity: float
    risk_level: str
    recommendation: str


# Limiares para classificacao de risco
RISK_THRESHOLDS = {
    "CRITICAL": {"overlap": 0.0, "delta": 0.0, "class_changed": True},
    "HIGH": {"overlap": 0.4, "delta": -0.3, "class_changed": False},
    "MODERATE": {"overlap": 0.6, "delta": -0.15, "class_changed": False},
    "LOW": {"overlap": 1.0, "delta": 0.0, "class_changed": False},
}


def assess_risk(
    noise_type: str,
    gradcam_overlap: float,
    confidence_delta: float,
    class_changed: bool,
    embedding_similarity: float,
) -> RiskAssessment:
    if class_changed:
        return RiskAssessment(
            noise_type=noise_type,
            gradcam_overlap=gradcam_overlap,
            confidence_delta=confidence_delta,
            class_changed=True,
            embedding_similarity=embedding_similarity,
            risk_level="CRITICAL",
            recommendation="Revisão humana obrigatória — classe alterada sob perturbação",
        )
    if gradcam_overlap < 0.4:
        return RiskAssessment(
            noise_type=noise_type,
            gradcam_overlap=gradcam_overlap,
            confidence_delta=confidence_delta,
            class_changed=False,
            embedding_similarity=embedding_similarity,
            risk_level="HIGH",
            recommendation="Revisão humana recomendada — explicação instável",
        )
    if confidence_delta < -0.3 or gradcam_overlap < 0.6:
        return RiskAssessment(
            noise_type=noise_type,
            gradcam_overlap=gradcam_overlap,
            confidence_delta=confidence_delta,
            class_changed=False,
            embedding_similarity=embedding_similarity,
            risk_level="MODERATE",
            recommendation="Revisão recomendada — confiança degradou significativamente",
        )
    return RiskAssessment(
        noise_type=noise_type,
        gradcam_overlap=gradcam_overlap,
        confidence_delta=confidence_delta,
        class_changed=False,
        embedding_similarity=embedding_similarity,
        risk_level="LOW",
        recommendation="Decisão estável — automático aceitável",
    )


def assess_all(comparisons: list[dict]) -> list[RiskAssessment]:
    return [
        assess_risk(
            noise_type=c["noise_type"],
            gradcam_overlap=c["gradcam_overlap"],
            confidence_delta=c["confidence_delta"],
            class_changed=c["class_changed"],
            embedding_similarity=c["embedding_similarity"],
        )
        for c in comparisons
    ]


def summary(assessments: list[RiskAssessment]) -> dict:
    total = len(assessments)
    if total == 0:
        return {"total": 0}
    by_level = {}
    for a in assessments:
        by_level[a.risk_level] = by_level.get(a.risk_level, 0) + 1
    return {
        "total": total,
        "by_level": by_level,
        "critical_pct": round(by_level.get("CRITICAL", 0) / total * 100, 1),
        "high_pct": round(by_level.get("HIGH", 0) / total * 100, 1),
        "requires_review": by_level.get("CRITICAL", 0) + by_level.get("HIGH", 0),
        "avg_overlap": round(sum(a.gradcam_overlap for a in assessments) / total, 4),
        "avg_confidence_delta": round(sum(a.confidence_delta for a in assessments) / total, 4),
    }
