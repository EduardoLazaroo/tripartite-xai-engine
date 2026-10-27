"""
Funcoes de aplicacao de ruido e perturbacoes em imagens.

Este modulo implementa as transformacoes utilizadas para gerar
variantes perturbadas das imagens originais. Cada funcao recebe
uma imagem PIL e retorna uma nova imagem com a perturbacao aplicada.

Tipos de perturbacao implementados:
    - Gaussiana: ruido aditivo com distribuicao normal
    - Salt & Pepper: pixels aleatorios pretos e brancos
    - Speckle: ruido multiplicativo
    - Blur: desfoque gaussiano
    - Brilho: ajuste de luminosidade
    - Contraste: ajuste de contraste
"""

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance


def apply_gaussian_noise(image: Image.Image, sigma: float = 0.1) -> Image.Image:
    """Aplica ruido gaussiano aditivo a imagem.
    
    Args:
        image: imagem PIL de entrada
        sigma: desvio padrao do ruido (0.0 a 1.0)
    
    Returns:
        Imagem com ruido gaussiano aplicado
    """
    array = np.asarray(image).astype(np.float32) / 255.0
    noise = np.random.normal(loc=0.0, scale=sigma, size=array.shape)
    noisy = np.clip(array + noise, 0.0, 1.0)
    return Image.fromarray((noisy * 255).astype(np.uint8))


def apply_salt_and_pepper(image: Image.Image, amount: float = 0.04) -> Image.Image:
    """Aplica ruido salt & pepper (pixels pretos e brancos aleatorios).
    
    Args:
        image: imagem PIL de entrada
        amount: proporcao de pixels afetados (0.0 a 1.0)
    
    Returns:
        Imagem com ruido salt & pepper aplicado
    """
    array = np.asarray(image).copy()
    num_salt = np.ceil(amount * array.size * 0.5).astype(int)
    num_pepper = np.ceil(amount * array.size * 0.5).astype(int)

    coords = [
        np.random.randint(0, i - 1, num_salt)
        for i in array.shape[:2]
    ]
    array[coords[0], coords[1]] = 255
    coords = [
        np.random.randint(0, i - 1, num_pepper)
        for i in array.shape[:2]
    ]
    array[coords[0], coords[1]] = 0
    return Image.fromarray(array)


def apply_speckle_noise(image: Image.Image, sigma: float = 0.1) -> Image.Image:
    """Aplica ruido speckle (multiplicativo) a imagem.
    
    Args:
        image: imagem PIL de entrada
        sigma: desvio padrao do ruido
    
    Returns:
        Imagem com ruido speckle aplicado
    """
    array = np.asarray(image).astype(np.float32) / 255.0
    noise = np.random.normal(loc=0.0, scale=sigma, size=array.shape)
    noisy = array + array * noise
    noisy = np.clip(noisy, 0.0, 1.0)
    return Image.fromarray((noisy * 255).astype(np.uint8))


def apply_blur(image: Image.Image, radius: float = 2.0) -> Image.Image:
    """Aplica desfoque gaussiano a imagem.
    
    Args:
        image: imagem PIL de entrada
        radius: raio do kernel gaussiano
    
    Returns:
        Imagem com desfoque aplicado
    """
    return image.filter(ImageFilter.GaussianBlur(radius))


def adjust_brightness(image: Image.Image, factor: float = 1.2) -> Image.Image:
    """Ajusta o brilho da imagem.
    
    Args:
        image: imagem PIL de entrada
        factor: multiplicador de brilho (1.0 = original)
    
    Returns:
        Imagem com brilho ajustado
    """
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(factor)


def adjust_contrast(image: Image.Image, factor: float = 1.25) -> Image.Image:
    """Ajusta o contraste da imagem.
    
    Args:
        image: imagem PIL de entrada
        factor: multiplicador de contraste (1.0 = original)
    
    Returns:
        Imagem com contraste ajustado
    """
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)
