import uuid
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from PIL import Image

from config import EMBEDDING_DIMENSION, SEARCH_MODE
from gradcam import GradCAM
from labels import get_imagenet_labels, index_to_label
from logger import log
from metrics import Stopwatch, TimingMetrics, compare_inferences
from noise import (
    apply_blur,
    apply_gaussian_noise,
    apply_salt_and_pepper,
    apply_speckle_noise,
    adjust_brightness,
    adjust_contrast,
)
from persistence import (
    AuditTrail,
    ClassLabel,
    DatabaseClient,
    Embedding,
    Experiment,
    GradCam,
    Image as ImageModel,
    Inference,
    MediaAsset,
    NoiseProfile,
    PerturbationComparison,
    QdrantClient,
    SimilarityRecord,
)
from pipeline import (
    extract_embedding,
    generate_gradcam,
    preprocess_image,
    run_inference,
    save_gradcam_heatmap,
    gradcam_stats,
)
from reproducibility import ExperimentMetadata, get_metadata
from search import contextual_retrieval, search_similar_embeddings
from storage import MinIOClient


NOISE_VARIANTS = [
    {'noise_type': 'none', 'intensity': 0.0, 'parameters': {}},
    {'noise_type': 'gaussian', 'intensity': 0.08, 'parameters': {'sigma': 0.08}},
    {'noise_type': 'blur', 'intensity': 2.0, 'parameters': {'radius': 2.0}, 'kernel_size': 'gaussian'},
    {'noise_type': 'brightness', 'intensity': 0.2, 'parameters': {'factor': 1.2}},
]


@dataclass
class VariantResult:
    inference_id: str
    noise_type: str
    predicted_class: int
    predicted_label: str
    confidence: float
    embedding: list[float]
    gradcam_map: torch.Tensor
    gradcam_asset_uri: str
    image_asset_uri: str
    timing: TimingMetrics = field(default_factory=TimingMetrics)


@dataclass
class ProcessingResult:
    experiment_id: str
    image_id: str
    baseline: VariantResult
    variants: list[VariantResult]
    comparisons: list[dict]
    timing: TimingMetrics
    similar_hits: list[dict]
    metadata: Optional[ExperimentMetadata] = None


def apply_variant(image: Image.Image, noise_type: str, intensity: float) -> Image.Image:
    if noise_type == 'none':
        return image.copy()
    if noise_type == 'gaussian':
        return apply_gaussian_noise(image, sigma=intensity)
    if noise_type == 'salt_pepper':
        return apply_salt_and_pepper(image, amount=intensity)
    if noise_type == 'speckle':
        return apply_speckle_noise(image, sigma=intensity)
    if noise_type == 'blur':
        return apply_blur(image, radius=intensity)
    if noise_type == 'brightness':
        return adjust_brightness(image, factor=1.0 + intensity)
    if noise_type == 'contrast':
        return adjust_contrast(image, factor=1.0 + intensity)
    raise ValueError(f'Noise type {noise_type} not supported')


# Cache de labels para evitar queries repetidas
_label_cache: dict[str, ClassLabel] = {}

def get_or_create_label(db: DatabaseClient, class_index: int, labels: list[str]) -> ClassLabel:
    label_name = index_to_label(class_index, labels)
    if label_name in _label_cache:
        return _label_cache[label_name]
    from sqlalchemy import select
    existing = db.scalar(select(ClassLabel).where(ClassLabel.label_name == label_name))
    if existing:
        _label_cache[label_name] = existing
        return existing
    record = ClassLabel(
        label_id=str(uuid.uuid4()),
        label_name=label_name,
        hierarchy_path=f'imagenet/{class_index}',
        description=f'ImageNet class index {class_index}',
    )
    result = db.insert_record(record)
    _label_cache[label_name] = result
    return result


def persist_media_asset(
    db: DatabaseClient,
    storage: MinIOClient,
    image: Image.Image,
    asset_type: str,
    inference_id: str,
    experiment_id: str = "",
) -> MediaAsset:
    if experiment_id:
        object_name = f'experiments/{experiment_id}/{inference_id}/{asset_type}.png'
    else:
        object_name = f'{inference_id}/{asset_type}.png'
    storage_uri = storage.upload_image(image, object_name)
    record = MediaAsset(
        media_asset_id=str(uuid.uuid4()),
        asset_type=asset_type,
        storage_uri=storage_uri,
        format='PNG',
        width=image.width,
        height=image.height,
    )
    return db.insert_record(record)


def log_audit(db: DatabaseClient, entity_type: str, entity_id: str, action: str, details: dict):
    db.insert_record(AuditTrail(
        audit_id=str(uuid.uuid4()),
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        performed_by='automated-runner',
        details=details,
    ))


def process_variant(
    db: DatabaseClient,
    vector_db: QdrantClient,
    storage: MinIOClient,
    model: torch.nn.Module,
    gradcam: GradCAM,
    labels: list[str],
    base_image: Image.Image,
    image_record: ImageModel,
    experiment: Experiment,
    noise_spec: dict,
    original_image: Image.Image,
    flush: bool = False,
) -> VariantResult:
    timing = TimingMetrics()
    sw = Stopwatch()

    noise_type = noise_spec['noise_type']
    log.substep(f"Aplicando perturbacao: {noise_type} (intensidade={noise_spec.get('intensity', 0.0)})")
    variant_image = apply_variant(base_image, noise_type, noise_spec.get('intensity', 0.0))

    noise_record = None
    if noise_type != 'none':
        noise_record = NoiseProfile(
            noise_id=str(uuid.uuid4()),
            noise_type=noise_type,
            intensity=noise_spec.get('intensity'),
            kernel_size=noise_spec.get('kernel_size'),
            parameters=noise_spec.get('parameters', {}),
        )
        db.insert_record(noise_record)

    log.substep("Executando inferencia do modelo")
    input_tensor = preprocess_image(variant_image)
    inference_result = run_inference(model, input_tensor)
    timing.inference_ms = sw.elapsed_ms()
    sw.reset()
    log.substep(f"Inferencia concluida: classe={inference_result['predicted_index']}, confianca={inference_result['confidence']:.4f}, tempo={timing.inference_ms}ms")

    predicted_idx = inference_result['predicted_index']
    label_record = get_or_create_label(db, predicted_idx, labels)

    inference = Inference(
        inference_id=str(uuid.uuid4()),
        image_id=image_record.image_id,
        experiment_id=experiment.experiment_id,
        noise_id=noise_record.noise_id if noise_record else None,
        predicted_label_id=label_record.label_id,
        confidence=inference_result['confidence'],
        probabilities=inference_result['probabilities'],
        preprocessing_steps=[{'step': 'resize'}, {'step': 'normalize'}],
        model_version='resnet50-imagenet1k-v2',
        inference_duration_ms=inference_result['inference_duration_ms'],
    )
    db.insert_record(inference)

    log.substep("Persistindo imagem perturbada no armazenamento")
    asset_type = 'original' if noise_type == 'none' else f'noisy_{noise_type}'
    image_asset = persist_media_asset(
        db, storage, variant_image, asset_type, inference.inference_id,
        experiment_id=experiment.experiment_id
    )

    log.substep("Extraindo embedding e indexando no Qdrant")
    sw.reset()
    embedding_tensor = extract_embedding(model, input_tensor)
    embedding_vector = embedding_tensor.numpy().tolist()[:EMBEDDING_DIMENSION]
    vector_db.insert_embedding(
        str(inference.inference_id),
        embedding_vector,
        payload={
            'inference_id': inference.inference_id,
            'image_id': image_record.image_id,
            'experiment_id': experiment.experiment_id,
            'noise_type': noise_type,
            'predicted_label': label_record.label_name,
            'confidence': inference_result['confidence'],
        },
    )
    db.insert_record(Embedding(
        embedding_id=str(uuid.uuid4()),
        inference_id=inference.inference_id,
        vector_db_id=str(inference.inference_id),
        dimension=len(embedding_vector),
        norm=float(np.linalg.norm(embedding_vector)),
        embedding_metadata={'source': 'resnet50_penultimate', 'noise_type': noise_type},
    ))
    timing.embedding_ms = sw.elapsed_ms()
    sw.reset()
    log.substep(f"Embedding indexado: dimensao={len(embedding_vector)}, tempo={timing.embedding_ms}ms")

    log.substep("Gerando mapa Grad-CAM")
    gradcam_map = generate_gradcam(model, gradcam, input_tensor, predicted_idx)
    gradcam_image = save_gradcam_heatmap(original_image, gradcam_map)
    activation_distribution, region_stats = gradcam_stats(gradcam_map)
    log.substep(f"Grad-CAM gerado: ativacao_media={activation_distribution['mean']:.4f}, regiao_ativada={region_stats['high_activation_ratio']:.2%}")

    log.substep("Persistindo Grad-CAM no armazenamento")
    gradcam_asset = persist_media_asset(
        db, storage, gradcam_image, 'gradcam', inference.inference_id,
        experiment_id=experiment.experiment_id
    )
    db.insert_record(GradCam(
        gradcam_id=str(uuid.uuid4()),
        inference_id=inference.inference_id,
        media_asset_id=gradcam_asset.media_asset_id,
        activation_distribution=activation_distribution,
        region_stats=region_stats,
    ))
    timing.gradcam_ms = sw.elapsed_ms()
    timing.persistence_ms = timing.embedding_ms + timing.gradcam_ms
    log.substep(f"Variante {noise_type} concluida: tempo_total={timing.inference_ms + timing.persistence_ms}ms")

    return VariantResult(
        inference_id=inference.inference_id,
        noise_type=noise_type,
        predicted_class=predicted_idx,
        predicted_label=label_record.label_name,
        confidence=inference_result['confidence'],
        embedding=embedding_vector,
        gradcam_map=gradcam_map,
        gradcam_asset_uri=gradcam_asset.storage_uri,
        image_asset_uri=image_asset.storage_uri,
        timing=timing,
    )


def persist_similarity_results(
    db: DatabaseClient,
    query: VariantResult,
    baseline_gradcam: Optional[torch.Tensor] = None,
    top_k: int = 5,
    filter_by_class: bool = True,
) -> list[dict]:
    """Persiste resultados de busca por similaridade.
    
    Args:
        db: cliente do banco relacional
        query: resultado da variante consulta
        baseline_gradcam: mapa Grad-CAM da baseline (opcional)
        top_k: numero de resultados
        filter_by_class: se True, recupera apenas imagens da mesma classe prevista
    
    Returns:
        Lista de hits encontrados
    """
    # Define filtro por classe prevista quando modo filtered
    filter_metadata = None
    if filter_by_class and SEARCH_MODE == "filtered":
        filter_metadata = {'predicted_label': query.predicted_label}
        log.substep(f"Busca filtrada por classe: {query.predicted_label}")

    hits = search_similar_embeddings(
        query.embedding,
        top_k=top_k,
        filter_metadata=filter_metadata,
    )
    query.timing.retrieval_ms = hits[0]['retrieval_time_ms'] if hits else 0

    stored = []
    same_class_count = 0
    for hit in hits:
        if hit['id'] == query.inference_id:
            continue

        # Verifica se o hit pertence à mesma classe (para métricas)
        hit_class = hit['payload'].get('predicted_label', '')
        if hit_class == query.predicted_label:
            same_class_count += 1

        gradcam_overlap_value = None
        if baseline_gradcam is not None and hit['payload'].get('noise_type') != 'none':
            pass

        record = SimilarityRecord(
            similarity_id=str(uuid.uuid4()),
            query_inference_id=query.inference_id,
            target_inference_id=hit['id'],
            embedding_similarity=hit['score'],
            gradcam_overlap=gradcam_overlap_value,
            distance_metric='cosine',
            rank=hit['rank'],
            retrieval_time_ms=hit['retrieval_time_ms'],
        )
        db.insert_record(record)
        stored.append(hit)

    # Log de consistência da busca
    if hits:
        consistency = same_class_count / len(hits) * 100
        log.substep(f"Consistencia da busca: {consistency:.0f}% dos hits na mesma classe")
    return stored


def process_image(
    image_path: str | Path,
    db: DatabaseClient,
    vector_db: QdrantClient,
    storage: MinIOClient,
    model: torch.nn.Module,
    experiment_name: str = 'cv-xai-perturbation-study',
    experiment_description: str = 'Estudo de perturbações visuais e evidências explicativas',
    seed: int = 42,
    metadata: Optional[ExperimentMetadata] = None,
    domain: str = 'imagenet',
) -> ProcessingResult:
    total_sw = Stopwatch()
    image_path = Path(image_path)
    image_name = image_path.name

    labels = get_imagenet_labels()
    gradcam = GradCAM(model, target_layer_name='layer4')
    original_image = Image.open(image_path).convert('RGB')

    if metadata is None:
        metadata = get_metadata(
            experiment_name=experiment_name,
            seed=seed,
            dataset_path=str(image_path.parent),
            num_images=1,
            noise_types=[n['noise_type'] for n in NOISE_VARIANTS],
            noise_intensities={n['noise_type']: n['intensity'] for n in NOISE_VARIANTS},
        )

    experiment = Experiment(
        experiment_id=metadata.experiment_id,
        name=experiment_name,
        description=experiment_description,
        created_by='automated-runner',
    )
    db.insert_record(experiment, flush=True)

    image_record = ImageModel(
        image_id=str(uuid.uuid4()),
        dataset_name=domain,
        source_uri=str(image_path),
        original_width=original_image.width,
        original_height=original_image.height,
        checksum='',
        format=image_path.suffix.lstrip('.').upper() or 'PNG',
    )
    db.insert_record(image_record, flush=True)

    variant_results: list[VariantResult] = []
    total_variants = len(NOISE_VARIANTS)
    for v_idx, noise_spec in enumerate(NOISE_VARIANTS, 1):
        result = process_variant(
            db=db,
            vector_db=vector_db,
            storage=storage,
            model=model,
            gradcam=gradcam,
            labels=labels,
            base_image=original_image,
            image_record=image_record,
            experiment=experiment,
            noise_spec=noise_spec,
            original_image=original_image,
            flush=(v_idx == total_variants),  # Flush apenas na última variante
        )
        variant_results.append(result)

    baseline = variant_results[0]
    comparisons: list[dict] = []

    # Garantir que todas as inferencias estao commitadas antes das comparacoes
    db.flush()

    for comp_idx, variant in enumerate(variant_results[1:], 1):
        log.substep(f"Comparando variante {comp_idx}/{len(variant_results) - 1}: {variant.noise_type}")
        metrics = compare_inferences(
            baseline_confidence=baseline.confidence,
            baseline_class=baseline.predicted_class,
            perturbed_confidence=variant.confidence,
            perturbed_class=variant.predicted_class,
            baseline_gradcam=baseline.gradcam_map,
            perturbed_gradcam=variant.gradcam_map,
            baseline_embedding=baseline.embedding,
            perturbed_embedding=variant.embedding,
        )
        db.insert_record(PerturbationComparison(
            comparison_id=str(uuid.uuid4()),
            baseline_inference_id=baseline.inference_id,
            perturbed_inference_id=variant.inference_id,
            noise_type=variant.noise_type,
            confidence_delta=metrics['confidence_delta'],
            class_changed=bool(metrics['class_changed']),
            gradcam_overlap=metrics['gradcam_overlap'],
            gradcam_correlation=metrics['gradcam_correlation'],
            embedding_similarity=metrics['embedding_similarity'],
        ), flush=True)
        comp_dict = {'noise_type': variant.noise_type, **metrics}
        comparisons.append(comp_dict)

        status = "CLASSE ALTERADA" if metrics['class_changed'] else f"delta_conf={metrics['confidence_delta']:+.4f}"
        log.substep(f"Resultado: {status}, IoU={metrics['gradcam_overlap']:.3f}, sim_emb={metrics['embedding_similarity']:.3f}")

        if metrics['class_changed']:
            log_audit(db, 'inference', variant.inference_id, 'class_changed', {
                'baseline_class': baseline.predicted_label,
                'perturbed_class': variant.predicted_label,
                'noise_type': variant.noise_type,
                'confidence_delta': metrics['confidence_delta'],
            })
        elif metrics['gradcam_overlap'] < 0.4:
            log_audit(db, 'gradcam', variant.inference_id, 'unstable_explanation', {
                'overlap': metrics['gradcam_overlap'],
                'noise_type': variant.noise_type,
                'risk_level': 'HIGH',
            })
        elif metrics['confidence_delta'] < -0.3:
            log_audit(db, 'inference', variant.inference_id, 'low_confidence', {
                'confidence': variant.confidence,
                'delta': metrics['confidence_delta'],
                'noise_type': variant.noise_type,
            })

    # Garante que os embeddings acumulados no batch sejam gravados no Qdrant
    vector_db.flush()

    # Busca por similaridade com filtro de classe (padrão para auditoria)
    similar_hits = persist_similarity_results(db, baseline, top_k=5, filter_by_class=True)

    # Busca contextual: combina filtro de experimento com classe prevista
    contextual_filter = {
        'experiment_id': experiment.experiment_id,
        'predicted_label': baseline.predicted_label,
    }
    contextual = contextual_retrieval(
        query_vector=baseline.embedding,
        filter_metadata=contextual_filter,
        top_k=10,
    )

    metadata.results = {
        'image_id': image_record.image_id,
        'baseline_inference_id': baseline.inference_id,
        'baseline_label': baseline.predicted_label,
        'baseline_confidence': baseline.confidence,
        'variants': [v.noise_type for v in variant_results],
        'comparisons': comparisons,
        'contextual_results_count': len(contextual['results']),
        'search_mode': SEARCH_MODE,
    }

    log_audit(db, 'experiment', experiment.experiment_id, 'completed', {
        'image_id': image_record.image_id,
        'baseline_inference_id': baseline.inference_id,
        'variants': [v.noise_type for v in variant_results],
        'comparisons': comparisons,
        'contextual_results_count': len(contextual['results']),
        'metadata': metadata.to_dict(),
    })

    total_timing = TimingMetrics(
        total_ms=total_sw.elapsed_ms(),
        inference_ms=sum(v.timing.inference_ms for v in variant_results),
        persistence_ms=sum(v.timing.persistence_ms for v in variant_results),
        embedding_ms=sum(v.timing.embedding_ms for v in variant_results),
        gradcam_ms=sum(v.timing.gradcam_ms for v in variant_results),
        retrieval_ms=similar_hits[0]['retrieval_time_ms'] if similar_hits else 0,
        details={
            'num_variants': len(variant_results),
            'contextual_hits': len(contextual['results']),
        },
    )

    log.image_done(image_name, baseline.predicted_label, baseline.confidence, total_timing.total_ms)

    return ProcessingResult(
        experiment_id=experiment.experiment_id,
        image_id=image_record.image_id,
        baseline=baseline,
        variants=variant_results,
        comparisons=comparisons,
        timing=total_timing,
        similar_hits=similar_hits,
        metadata=metadata,
    )
