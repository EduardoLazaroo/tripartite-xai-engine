"""
Implementacao do Grad-CAM (Gradient-weighted Class Activation Mapping).

Este modulo implementa a tecnica Grad-CAM para gerar mapas de
ativacao que regiao da imagem foi mais relevante para a decisao
do modelo.

Referencia: Selvaraju et al. (2017) - "Grad-CAM: Visual Explanations
from Deep Networks via Gradient-based Localization"
"""

import torch
import torch.nn.functional as F
from torch import nn


class GradCAM:
    """Gerador de mapas Grad-CAM para modelos PyTorch.
    
    Utiliza hooks para capturar ativacoes e gradientes da camada
    alvo durante a forward/backward pass.
    """
    
    def __init__(self, model: nn.Module, target_layer_name: str):
        """Inicializa Grad-CAM com modelo e camada alvo.
        
        Args:
            model: modelo PyTorch (ex: ResNet50)
            target_layer_name: nome da camada para gerar o mapa (ex: 'layer4')
        """
        self.model = model
        self.target_layer_name = target_layer_name
        self.activations = None
        self.gradients = None
        self._register_hooks()

    def _register_hooks(self):
        """Registra forward e backward hooks na camada alvo."""
        for name, module in self.model.named_modules():
            if name == self.target_layer_name:
                module.register_forward_hook(self._forward_hook)
                module.register_full_backward_hook(self._backward_hook)
                return
        raise ValueError(f"Target layer {self.target_layer_name} not found")

    def _forward_hook(self, module, input, output):
        """Captura ativacoes durante forward pass."""
        self.activations = output.detach()

    def _backward_hook(self, module, grad_in, grad_out):
        """Captura gradientes durante backward pass."""
        self.gradients = grad_out[0].detach()

    def generate(self, input_tensor: torch.Tensor, target_class: int) -> torch.Tensor:
        """Gera mapa Grad-CAM para a classe alvo.
        
        Args:
            input_tensor: tensor de entrada (1, C, H, W)
            target_class: indice da classe para gerar o mapa
        
        Returns:
            Mapa Grad-CAM normalizado (H, W) com valores em [0, 1]
        """
        self.model.eval()
        self.model.zero_grad()

        output = self.model(input_tensor)
        loss = output[0, target_class]
        loss.backward(retain_graph=True)

        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        gradcam_map = F.relu((weights * self.activations).sum(dim=1, keepdim=True))
        gradcam_map = gradcam_map.squeeze(0)
        gradcam_map = F.interpolate(gradcam_map.unsqueeze(0), size=input_tensor.shape[2:], mode='bilinear', align_corners=False)
        gradcam_map = gradcam_map.squeeze(0)
        gradcam_map = gradcam_map - gradcam_map.min()
        if gradcam_map.max() != 0:
            gradcam_map = gradcam_map / gradcam_map.max()
        return gradcam_map
