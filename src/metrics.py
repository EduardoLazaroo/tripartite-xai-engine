"""
Metricas de desempenho e comparacao de inferencias.

Este modulo fornece:
    - Metricas de tempo (TimingMetrics, Stopwatch)
    - Comparacao de mapas Grad-CAM (IoU, correlacao)
    - Similaridade de embeddings (cosseno)
    - Comparacao completa entre inferencias baseline e perturbadas
"""

import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import torch


@dataclass
class TimingMetrics:
    """Armazena tempos de execucao das diferentes etapas do pipeline.
    
    Atributos:
        inference_ms: tempo de inferencia do modelo
        persistence_ms: tempo de persistencia no banco
        embedding_ms: tempo de extracao de embedding
        gradcam_ms: tempo de geracao do Grad-CAM
        retrieval_ms: tempo de recuperacao vetorial
        total_ms: tempo total de processamento
        details: informacoes adicionais
    """
    inference_ms: int = 0
    persistence_ms: int = 0
    embedding_ms: int = 0
    gradcam_ms: int = 0
    retrieval_ms: int = 0
    total_ms: int = 0
    details: dict = field(default_factory=dict)


class Stopwatch:
    """Cronometro para medicao de tempo de execucao.
    
    Utiliza time.perf_counter() para alta precisao.
    """
    
    def __init__(self):
        self._start = time.perf_counter()

    def elapsed_ms(self) -> int:
        """Retorna tempo decorrido em milissegundos."""
        return int((time.perf_counter() - self._start) * 1000)

    def reset(self):
        """Reinicia o cronometro."""
        self._start = time.perf_counter()


def gradcam_overlap(
    map_a: torch.Tensor,
    map_b: torch.Tensor,
    threshold: float = 0.5,
) -> dict[str, float]:
    a = map_a.squeeze().detach().cpu().numpy()
    b = map_b.squeeze().detach().cpu().numpy()

    if a.shape != b.shape:
        from PIL import Image
        b_img = Image.fromarray((b * 255).astype(np.uint8))
        b_img = b_img.resize((a.shape[1], a.shape[0]), Image.BILINEAR)
        b = np.asarray(b_img).astype(np.float32) / 255.0

    a_norm = (a - a.min()) / (a.max() - a.min() + 1e-8)
    b_norm = (b - b.min()) / (b.max() - b.min() + 1e-8)

    mask_a = a_norm >= threshold
    mask_b = b_norm >= threshold
    intersection = np.logical_and(mask_a, mask_b).sum()
    union = np.logical_or(mask_a, mask_b).sum()
    iou = float(intersection / union) if union > 0 else 0.0

    flat_a = a_norm.flatten()
    flat_b = b_norm.flatten()
    if flat_a.std() > 0 and flat_b.std() > 0:
        correlation = float(np.corrcoef(flat_a, flat_b)[0, 1])
    else:
        correlation = 0.0

    return {
        'gradcam_overlap': iou,
        'gradcam_correlation': correlation,
        'high_activation_ratio_a': float(mask_a.mean()),
        'high_activation_ratio_b': float(mask_b.mean()),
    }


def embedding_cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    a = np.asarray(vec_a, dtype=np.float32)
    b = np.asarray(vec_b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def compare_inferences(
    baseline_confidence: float,
    baseline_class: int,
    perturbed_confidence: float,
    perturbed_class: int,
    baseline_gradcam: torch.Tensor,
    perturbed_gradcam: torch.Tensor,
    baseline_embedding: list[float],
    perturbed_embedding: list[float],
) -> dict:
    overlap = gradcam_overlap(baseline_gradcam, perturbed_gradcam)
    return {
        'confidence_delta': perturbed_confidence - baseline_confidence,
        'class_changed': baseline_class != perturbed_class,
        'baseline_class': baseline_class,
        'perturbed_class': perturbed_class,
        'embedding_similarity': embedding_cosine_similarity(baseline_embedding, perturbed_embedding),
        **overlap,
    }
