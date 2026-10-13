# Apresentação Profissional - Persistência Híbrida para XAI

## Identidade e Valor

Este projeto reúne a produção científica e os artefatos de um artigo acadêmico de pós-graduação (UNESP) que propõe uma **arquitetura híbrida de persistência e recuperação de evidências explicativas** em sistemas de visão computacional baseados em Deep Learning. O trabalho resolve o problema do descarte efêmero de mapas Grad-CAM e perturbações, unificando metadados relacionais (MySQL), embeddings semânticos (Qdrant) e armazenamento de objetos (MinIO) para auditoria e governança de IA.

## Texto para Publicação

> Modelos de visão computacional como a ResNet-50 geram mapas de atenção visual (Grad-CAM), mas na quase totalidade dos sistemas essas explicações são descartadas logo após a inferência, inviabilizando auditorias futuras. Neste artigo acadêmico desenvolvido na pós-graduação da UNESP, propus e validei uma arquitetura híbrida de persistência que conecta MySQL (metadados, predições e riscos), Qdrant (busca vetorial por similaridade de atenção) e MinIO (armazenamento escalável de imagens e mapas brutos). Os resultados experimentais com 400 inferências demonstram que é possível consultar casos semelhantes em apenas 31,35 ms, criando uma base concreta para rastreabilidade e conformidade regulatória em IA Explicável (XAI).

## Evidências Visuais Recomendadas

1. Diagrama da arquitetura híbrida de três camadas (`evidencias/figure_3.png`).
2. Comparativo de mapa Grad-CAM original e sob ruído Gaussiano (`evidencias/02_gradcam_original.png`, `evidencias/04_gradcam_gaussian.png`).
3. Impacto de perturbação de desfoque óptico (`evidencias/06_gradcam_blur.png`).
4. Artigo científico completo compilado em PDF (`Artigo_Banco_Dados_Eduardo_Lazaro.pdf`).
5. Relatório Executivo Word diagramado (`Artigo_BD_Relatorio_Publicacao.docx`).

## Prompt para Imagem Complementar

```text
Diagrama conceitual de persistência híbrida para inteligência artificial explicável: uma imagem de animal entra em um modelo de visão computacional, produzindo Grad-CAM; setas distribuem os dados para três blocos: banco relacional MySQL (tabelas e metadados), banco vetorial Qdrant (vetores de similaridade) e storage MinIO (imagens e mapas em nuvem); estilo de paper científico internacional, fundo branco, azul escuro e verde-água, sem logotipos.
```
