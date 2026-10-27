import argparse
import json
import sys
from pathlib import Path

from torchvision import models

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

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
from logger import log
from persistence import DatabaseClient, QdrantClient
from processor import NOISE_VARIANTS, process_image
from storage import MinIOClient


DOMAIN_LABELS = {
    'imagenet': None,
    'medical': 'medical',
    'industrial': 'industrial',
}


def load_model():
    log.step("Carregando modelo ResNet50 (IMAGENET1K_V2)")
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
    model.eval()
    log.info("Modelo carregado com sucesso")
    return model


def print_summary(result):
    print('\n=== Processamento concluido ===')
    print(f'Experiment ID: {result.experiment_id}')
    print(f'Image ID:      {result.image_id}')
    print(f'\nBaseline:')
    print(f'  Classe:     {result.baseline.predicted_label}')
    print(f'  Confianca:  {result.baseline.confidence:.4f}')
    print(f'\nComparacoes de perturbacao ({len(result.comparisons)} variantes):')
    for comp in result.comparisons:
        changed = 'SIM' if comp['class_changed'] else 'nao'
        print(
            f"  {comp['noise_type']:14s} | dconf={comp['confidence_delta']:+.4f} | "
            f"Grad-CAM IoU={comp['gradcam_overlap']:.3f} | "
            f"emb.sim={comp['embedding_similarity']:.3f} | classe alterada: {changed}"
        )
    print(f'\nTiming (ms):')
    print(f'  Total:        {result.timing.total_ms}')
    print(f'  Inferencia:   {result.timing.inference_ms}')
    print(f'  Persistencia: {result.timing.persistence_ms}')
    print(f'  Recuperacao:  {result.timing.retrieval_ms}')
    if result.similar_hits:
        print(f'\nTop similar (embedding):')
        for hit in result.similar_hits[:3]:
            payload = hit.get('payload', {})
            print(
                f"  rank={hit['rank']} score={hit['score']:.3f} "
                f"noise={payload.get('noise_type')} label={payload.get('predicted_label')}"
            )


def main():
    parser = argparse.ArgumentParser(
        description='Pipeline de evidencias explicativas com perturbacoes e recuperacao contextual'
    )
    parser.add_argument('--image', type=str, required=True, help='Caminho da imagem de entrada')
    parser.add_argument('--json', action='store_true', help='Imprimir resumo em JSON')
    parser.add_argument('--domain', type=str, default='imagenet',
                        choices=['imagenet', 'medical', 'industrial'],
                        help='Dominio da aplicacao (contexto de auditoria)')
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        raise SystemExit(f'Imagem nao encontrada: {image_path}')

    log.section("PIPELINE DE EVIDENCIAS EXPLICATIVAS")
    log.start(f"Imagem: {image_path.name}")
    log.info(f"Dominio: {args.domain}")
    log.info(f"Variantes de perturbacao: {len(NOISE_VARIANTS)} ({', '.join(n['noise_type'] for n in NOISE_VARIANTS)})")

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

    model = load_model()

    log.step("Iniciando processamento da imagem")
    result = process_image(
        image_path=image_path,
        db=db,
        vector_db=vector_db,
        storage=storage,
        model=model,
        domain=args.domain,
    )

    log.step("Gerando saida de resultados")
    if args.json:
        output = {
            'experiment_id': result.experiment_id,
            'image_id': result.image_id,
            'domain': args.domain,
            'baseline': {
                'inference_id': result.baseline.inference_id,
                'label': result.baseline.predicted_label,
                'confidence': result.baseline.confidence,
            },
            'comparisons': result.comparisons,
            'timing_ms': {
                'total': result.timing.total_ms,
                'inference': result.timing.inference_ms,
                'persistence': result.timing.persistence_ms,
                'retrieval': result.timing.retrieval_ms,
            },
            'num_variants': len(NOISE_VARIANTS),
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print_summary(result)

    log.done(f"Pipeline concluido para {image_path.name}")


if __name__ == '__main__':
    main()
