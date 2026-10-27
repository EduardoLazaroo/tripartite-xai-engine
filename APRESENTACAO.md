# Apresentacao profissional

## Identidade e valor

Este e um pipeline de pesquisa para persistir, recuperar e auditar explicacoes de modelos de visao computacional. A arquitetura combina PyTorch/Torchvision, MySQL, Qdrant, MinIO, SQLAlchemy e FastAPI, com orquestracao em Docker. O estudo documenta Grad-CAM, perturbacoes e recuperacao contextual/vetorial sobre imagens Oxford-IIIT Pet.

## Texto para publicacao

> Este projeto de mestrado investiga como explicacoes de modelos de visao computacional podem deixar de ser artefatos descartaveis e passar a compor uma base consultavel de evidencias. A arquitetura integra metadados relacionais, vetores semanticos e armazenamento de objetos para relacionar imagens, predicoes, mapas Grad-CAM e testes de perturbacao. O desafio foi conectar rastreabilidade experimental e recuperacao eficiente em um unico fluxo reproduzivel por containers. Os benchmarks e relatorios incluidos devem ser rerunados para qualquer uso comparativo, mas o projeto oferece uma base concreta para pesquisa em XAI e engenharia de dados.

## Evidencias visuais recomendadas

1. Servicos Docker em execucao.
2. Mapa Grad-CAM e sua evidencia persistida.
3. Figura de benchmark em `reports/figures/`.
4. Recuperacao top-5 de explicacoes semelhantes.

## Prompt para imagem complementar

```text
Diagrama cientifico de uma plataforma de auditoria de IA explicavel: imagens de animais entram em um modelo ResNet50, produzem predicao e Grad-CAM; MySQL recebe metadados, Qdrant recebe embeddings, MinIO recebe artefatos; uma API consulta e audita as evidencias, estilo paper academico, fundo branco, setas claras, sem logos.
```
