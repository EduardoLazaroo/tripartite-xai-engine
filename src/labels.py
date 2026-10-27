"""
Utilitarios para rotulos de classes ImageNet.

Este modulo fornece funcoes para obter e converter rotulos
de classes do dataset ImageNet, utilizado pelo modelo ResNet50.
"""

from torchvision import models


def get_imagenet_labels() -> list[str]:
    """Retorna a lista de 1000 rotulos de classes ImageNet.
    
    Returns:
        Lista com nomes das classes ImageNet1K
    """
    weights = models.ResNet50_Weights.IMAGENET1K_V2
    return list(weights.meta['categories'])


def index_to_label(index: int, labels: list[str] | None = None) -> str:
    """Converte um indice numerico para nome da classe.
    
    Args:
        index: indice da classe (0-999)
        labels: lista de rotulos (opcional, carrega se nao fornecido)
    
    Returns:
        Nome da classe correspondente ao indice
    """
    labels = labels or get_imagenet_labels()
    if 0 <= index < len(labels):
        return labels[index]
    return f'unknown_{index}'
