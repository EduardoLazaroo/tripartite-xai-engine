import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

import argparse
import json
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from torchvision import models

from config import (
    DATABASE_DSN,
    MINIO_ACCESS_KEY,
    MINIO_BUCKET,
    MINIO_ENDPOINT,
    MINIO_SECRET_KEY,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    QDRANT_URL,
)
from interpretability_report import assess_all, summary
from logger import log
from persistence import BenchmarkRun, DatabaseClient, QdrantClient
from processor import NOISE_VARIANTS, process_image
from reproducibility import get_metadata
from storage import MinIOClient

BATCH_SIZE = 4


def collect_storage_bytes(storage: MinIOClient) -> int:
    total = 0
    for obj in storage.client.list_objects(MINIO_BUCKET, recursive=True):
        total += obj.size or 0
    return total


def run_benchmark(image_paths: list[Path], output_dir: Path, seed: int = 42,
                  audit_mode: bool = False, domain: str = 'imagenet',
                  max_workers: int = 4) -> dict:
    total_images = len(image_paths)
    total_batches = (total_images + BATCH_SIZE - 1) // BATCH_SIZE
    noise_types = [n['noise_type'] for n in NOISE_VARIANTS]

    log.section("BENCHMARK DE PERSISTENCIA E RECUPERACAO")
    log.start(f"{total_images} imagens, {len(NOISE_VARIANTS)} variantes ({', '.join(noise_types)}), {max_workers} workers")
    log.info(f"Total de inferencias previstas: {total_images * len(NOISE_VARIANTS)}")
    log.info(f"Batches: {total_batches} (tamanho {BATCH_SIZE})")

    output_dir.mkdir(parents=True, exist_ok=True)

    log.step("Inicializando infraestrutura")
    log.substep("Conectando ao MySQL")
    db = DatabaseClient(DATABASE_DSN)
    db.create_schema()
    log.substep("Conectando ao Qdrant")
    vector_db = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, collection_name=QDRANT_COLLECTION)
    log.substep("Conectando ao MinIO")
    storage = MinIOClient(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        bucket=MINIO_BUCKET,
    )
    log.info("Infraestrutura inicializada com sucesso")

    log.step("Carregando modelo ResNet50 (IMAGENET1K_V2)")
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
    model.eval()
    log.info("Modelo carregado com sucesso")

    benchmark_id = str(uuid.uuid4())
    metadata = get_metadata(
        experiment_name='benchmark-run',
        seed=seed,
        dataset_path=str(image_paths[0].parent) if image_paths else '',
        num_images=total_images,
        noise_types=noise_types,
        noise_intensities={n['noise_type']: n['intensity'] for n in NOISE_VARIANTS},
    )
    metadata.experiment_id = benchmark_id

    storage_before = collect_storage_bytes(storage)
    results = []
    total_persistence_ms = 0
    retrieval_times = []
    all_comparisons = []
    processed = 0

    def process_single_image(idx: int, image_path: Path):
        img_metadata = get_metadata(
            experiment_name=f'benchmark-img-{idx}',
            seed=seed + idx,
            dataset_path=str(image_path.parent),
            num_images=1,
            noise_types=noise_types,
            noise_intensities={n['noise_type']: n['intensity'] for n in NOISE_VARIANTS},
        )
        result = process_image(
            image_path=image_path,
            db=db,
            vector_db=vector_db,
            storage=storage,
            model=model,
            experiment_name=f'benchmark-run-{benchmark_id[:8]}',
            experiment_description=f'Benchmark em {datetime.now().isoformat()}',
            seed=seed + idx,
            metadata=img_metadata,
            domain=domain,
        )
        return idx, result

    log.step(f"Processamento de imagens ({total_batches} batches)")
    for batch_start in range(0, total_images, BATCH_SIZE):
        batch_num = batch_start // BATCH_SIZE + 1
        batch_end = min(batch_start + BATCH_SIZE, total_images)
        batch = list(enumerate(image_paths[batch_start:batch_end], start=batch_start))

        log.info(f"Batch {batch_num}/{total_batches}: imagens {batch_start + 1}-{batch_end} de {total_images}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_single_image, idx, path): idx for idx, path in batch}
            batch_results = []
            for future in as_completed(futures):
                idx, result = future.result()
                batch_results.append((idx, result))

            batch_results.sort(key=lambda x: x[0])

            for idx, result in batch_results:
                processed += 1
                total_persistence_ms += result.timing.persistence_ms
                if result.timing.retrieval_ms:
                    retrieval_times.append(result.timing.retrieval_ms)
                all_comparisons.extend(result.comparisons)

                results.append({
                    'image': str(image_paths[idx]),
                    'experiment_id': result.experiment_id,
                    'baseline_label': result.baseline.predicted_label,
                    'baseline_confidence': result.baseline.confidence,
                    'timing_ms': {
                        'total': result.timing.total_ms,
                        'inference': result.timing.inference_ms,
                        'persistence': result.timing.persistence_ms,
                        'retrieval': result.timing.retrieval_ms,
                    },
                    'baseline_image_uri': result.baseline.image_asset_uri,
                    'baseline_gradcam_uri': result.baseline.gradcam_asset_uri,
                    'variants': [
                        {
                            'noise_type': v.noise_type,
                            'predicted_label': v.predicted_label,
                            'confidence': v.confidence,
                            'image_uri': v.image_asset_uri,
                            'gradcam_uri': v.gradcam_asset_uri,
                        }
                        for v in result.variants
                    ],
                    'comparisons': result.comparisons,
                })

        log.progress(processed, total_images, f"imagens processadas ({processed * len(NOISE_VARIANTS)} inferencias)")

    log.step("Gerando relatorio de risco")
    storage_after = collect_storage_bytes(storage)
    storage_delta = storage_after - storage_before
    avg_retrieval = sum(retrieval_times) / len(retrieval_times) if retrieval_times else 0.0
    log.info(f"Armazenamento: {round(storage_delta / (1024 * 1024), 2)} MB adicionados")
    log.info(f"Tempo medio de recuperacao: {avg_retrieval:.1f}ms")

    metadata.results = {
        'num_images': total_images,
        'total_inferences': total_images * len(NOISE_VARIANTS),
        'total_persistence_ms': total_persistence_ms,
        'avg_retrieval_ms': avg_retrieval,
        'storage_bytes_delta': storage_delta,
    }

    risk_summary = summary(assess_all(all_comparisons)) if all_comparisons else {}
    log.info(f"Risco: {risk_summary.get('by_level', {})}")

    summary_data = {
        'benchmark_id': metadata.experiment_id,
        'metadata': metadata.to_dict(),
        'num_images': total_images,
        'num_variants_per_image': len(NOISE_VARIANTS),
        'total_inferences': total_images * len(NOISE_VARIANTS),
        'total_persistence_ms': total_persistence_ms,
        'avg_persistence_ms_per_image': total_persistence_ms / total_images if total_images else 0,
        'avg_retrieval_ms': avg_retrieval,
        'storage_bytes_delta': storage_delta,
        'storage_mb_delta': round(storage_delta / (1024 * 1024), 2),
        'risk_summary': risk_summary,
        'results': results,
    }

    log.step("Persistindo resultados no MySQL")
    db.insert_record(BenchmarkRun(
        benchmark_id=metadata.experiment_id,
        experiment_id=results[-1]['experiment_id'] if results else None,
        num_images=total_images,
        num_variants=len(NOISE_VARIANTS),
        total_persistence_ms=total_persistence_ms,
        avg_retrieval_ms=avg_retrieval,
        total_storage_bytes=storage_delta,
        metrics=summary_data,
    ))
    log.info("Resultados persistidos no banco de dados")

    log.step("Salvando relatorios em disco")
    report_path = output_dir / f'benchmark_{metadata.experiment_id[:8]}.json'
    report_path.write_text(json.dumps(summary_data, indent=2, ensure_ascii=False), encoding='utf-8')
    log.info(f"Relatorio salvo: {report_path}")

    metadata_path = output_dir / f'metadata_{metadata.experiment_id[:8]}.json'
    metadata.save(metadata_path)
    log.info(f"Metadados salvos: {metadata_path}")

    summary_data['report_path'] = str(report_path)
    summary_data['metadata_path'] = str(metadata_path)
    summary_data['audit_mode'] = audit_mode

    if audit_mode:
        log.step(f"Gerando relatorios de auditoria ({len(results)} experimentos)")
        from audit_report import generate_audit_report, format_text_report, save_report
        audit_success = 0
        audit_failures = 0
        for i, result in enumerate(results, 1):
            log.progress(i, len(results), f"Auditoria: {result['image']}")
            try:
                audit = generate_audit_report(result['experiment_id'], db=db, storage=storage)
                text_report = format_text_report(audit)
                print(text_report)
                save_report(audit, output_dir / 'audits')
                audit_success += 1
            except Exception as e:
                log.warn(f"Falha na auditoria de {result['image']}: {e}")
                audit_failures += 1
        log.info(f"Auditoria concluida: {audit_success} sucesso, {audit_failures} falhas")

    log.done(f"Benchmark concluido: {total_images} imagens, {total_images * len(NOISE_VARIANTS)} inferencias, {round(storage_delta / (1024 * 1024), 1)} MB armazenados")

    return summary_data


def discover_images(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    return sorted(p for p in path.iterdir() if p.suffix.lower() in extensions)


def main():
    parser = argparse.ArgumentParser(description='Benchmark de persistência e recuperação')
    parser.add_argument('--input', type=str, required=True, help='Imagem ou diretório de imagens')
    parser.add_argument('--output', type=str, default='reports', help='Diretório de saída')
    parser.add_argument('--seed', type=int, default=42, help='Seed para reprodutibilidade (padrão: 42)')
    parser.add_argument('--audit-mode', action='store_true',
                        help='Ativa modo auditoria — gera relatórios de risco por experimento')
    parser.add_argument('--domain', type=str, default='imagenet',
                        choices=['imagenet', 'medical', 'industrial'],
                        help='Domínio da aplicação')
    parser.add_argument('--workers', type=int, default=1,
                        help='Número de workers para processamento paralelo (padrão: 1)')
    parser.add_argument('--quiet', action='store_true',
                        help='Modo silencioso — exibe apenas resultado final')
    args = parser.parse_args()

    if args.quiet:
        log.verbose = False

    log.step("Descobrindo imagens")
    images = discover_images(Path(args.input))
    if not images:
        log.error(f'Nenhuma imagem encontrada em {args.input}')
        raise SystemExit(f'Nenhuma imagem encontrada em {args.input}')
    log.info(f"{len(images)} imagens encontradas em {args.input}")

    summary = run_benchmark(images, Path(args.output), seed=args.seed,
                             audit_mode=args.audit_mode, domain=args.domain,
                             max_workers=args.workers)

    print(json.dumps({
        'benchmark_id': summary['benchmark_id'],
        'num_images': summary['num_images'],
        'total_inferences': summary['total_inferences'],
        'avg_persistence_ms_per_image': summary['avg_persistence_ms_per_image'],
        'avg_retrieval_ms': summary['avg_retrieval_ms'],
        'storage_mb_delta': summary['storage_mb_delta'],
        'risk_summary': summary.get('risk_summary', {}),
        'report_path': summary['report_path'],
        'metadata_path': summary.get('metadata_path', ''),
        'audit_mode': summary.get('audit_mode', False),
    }, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
