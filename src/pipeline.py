"""
Pipeline de processamento de imagens e inferencia.

Este modulo contem as funcoes de baixo nivel para:
    - Preprocessamento de imagens (resize, normalizacao)
    - Inferencia do modelo ResNet50
    - Extracao de embeddings
    - Geracao de mapas Grad-CAM
    - Aplicacao de perfis de ruido
"""

import time
from pathlib import Path
from typing import Dict

import matplotlib.cm as cm
import numpy as np
import torch
from PIL import Image
from torchvision import transforms as T

from config import IMAGE_TARGET_SIZE
from gradcam import GradCAM
from noise import (
    apply_blur,
    apply_gaussian_noise,
    apply_salt_and_pepper,
    apply_speckle_noise,
    adjust_brightness,
    adjust_contrast,
)


def preprocess_image(image: Image.Image) -> torch.Tensor:
    """Preprocessa imagem para inferencia no modelo.
    
    Aplica resize, conversao para tensor e normalizacao
    com estatisticas do ImageNet.
    
    Args:
        image: imagem PIL de entrada
    
    Returns:
        Tensor preprocessado com dimensao (1, 3, 224, 224)
    """
    transform = T.Compose([
        T.Resize(IMAGE_TARGET_SIZE),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    return transform(image).unsqueeze(0)


def apply_noise_profile(image: Image.Image, noise_type: str, intensity: float) -> Image.Image:
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
    raise ValueError(f'Noise type {noise_type} not implemented')


def save_asset(image: Image.Image, target_path: Path) -> str:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(target_path, format='PNG')
    return str(target_path)


def run_inference(model: torch.nn.Module, input_tensor: torch.Tensor) -> Dict[str, object]:
    model.eval()
    start = time.time()
    with torch.no_grad():
        logits = model(input_tensor)
        probabilities = torch.softmax(logits[0], dim=0)

    inference_duration_ms = int((time.time() - start) * 1000)
    confidence, predicted_index = torch.max(probabilities, dim=0)
    return {
        'logits': logits,
        'probabilities': probabilities.tolist(),
        'confidence': float(confidence.item()),
        'predicted_index': int(predicted_index.item()),
        'inference_duration_ms': inference_duration_ms,
    }


def extract_embedding(model: torch.nn.Module, input_tensor: torch.Tensor) -> torch.Tensor:
    features = model.conv1(input_tensor)
    features = model.bn1(features)
    features = model.relu(features)
    features = model.maxpool(features)
    features = model.layer1(features)
    features = model.layer2(features)
    features = model.layer3(features)
    features = model.layer4(features)
    pooled = model.avgpool(features)
    embedding = torch.flatten(pooled, 1)
    normalized = torch.nn.functional.normalize(embedding, p=2, dim=1)
    return normalized.detach().cpu().squeeze(0)


def generate_gradcam(
    model: torch.nn.Module,
    gradcam: GradCAM,
    input_tensor: torch.Tensor,
    target_class: int,
) -> torch.Tensor:
    return gradcam.generate(input_tensor, target_class)


def save_gradcam_heatmap(base_image: Image.Image, gradcam_map: torch.Tensor, colormap: str = 'jet') -> Image.Image:
    """Gera mapa de calor Grad-CAM com colormap JET ou Turbo sobreposto à imagem original.
    
    Args:
        base_image: imagem PIL original
        gradcam_map: tensor Grad-CAM normalizado [0, 1]
        colormap: 'jet' ou 'turbo'
    
    Returns:
        Imagem com heatmap overlay aplicado
    """
    heatmap = gradcam_map.squeeze().detach().cpu().numpy()
    
    # Aplica colormap JET ou Turbo
    try:
        import matplotlib
        cmap = matplotlib.colormaps[colormap]
    except Exception:
        cmap = cm.get_cmap(colormap)
    heatmap_colored = cmap(heatmap)  # RGBA [0, 1]
    heatmap_colored = (heatmap_colored[:, :, :3] * 255).astype(np.uint8)
    
    # Redimensiona para o tamanho da imagem original
    heatmap_pil = Image.fromarray(heatmap_colored).resize(base_image.size, Image.BILINEAR)
    
    # Sobreposição com alpha blending (50% heatmap, 50% imagem original)
    base = np.asarray(base_image).astype(np.float32)
    heat = np.asarray(heatmap_pil).astype(np.float32)
    
    alpha = 0.5
    overlay = (base * (1 - alpha) + heat * alpha).clip(0, 255).astype(np.uint8)
    
    return Image.fromarray(overlay)


def gradcam_stats(gradcam_map: torch.Tensor) -> tuple[dict, dict]:
    arr = gradcam_map.squeeze().detach().cpu().numpy()
    activation_distribution = {
        'mean': float(arr.mean()),
        'std': float(arr.std()),
        'max': float(arr.max()),
        'min': float(arr.min()),
    }
    region_stats = {
        'high_activation_ratio': float((arr > 0.5).mean()),
    }
    return activation_distribution, region_stats
