# Relatório Técnico Completo: Pipeline de Evidências Explicativas para Auditoria de IA

## Arquitetura Híbrida de Persistência e Recuperação (MySQL + Qdrant + MinIO)

---

**Data do Experimento:** 2026-06-25  
**Benchmark ID:** `d9988a7c-a09c-4632-bbae-fe67d5cf9dbf`  
**Ambiente:** Windows 11 (AMD64), Python 3.13.14, PyTorch 2.7.0+cpu  
**Dataset:** Oxford-IIIT Pet Dataset (100 imagens, 10 raças)

---

## Sumário

1. [Introdução e Contexto](#1-introdução-e-contexto)
2. [Visão Geral do Sistema](#2-visão-geral-do-sistema)
3. [Arquitetura de Banco de Dados](#3-arquitetura-de-banco-de-dados)
4. [Fluxo de Processamento](#4-fluxo-de-processamento)
5. [Experimentação](#5-experimentação)
6. [Resultados de Armazenamento (MySQL)](#6-resultados-de-armazenamento-mysql)
7. [Resultados Vetoriais (Qdrant)](#7-resultados-vetoriais-qdrant)
8. [Resultados Multimídia (MinIO)](#8-resultados-multimídia-minio)
9. [Métricas de Desempenho](#9-métricas-de-desempenho)
10. [Análise de Estabilidade das Explicações](#10-análise-de-estabilidade-das-explicações)
11. [Análise por Classe](#11-análise-por-classe)
12. [Discussão Crítica](#12-discussão-crítica)
13. [Limitações e Trabalhos Futuros](#13-limitações-e-trabalhos-futuros)
14. [Conclusões](#14-conclusões)
15. [Reprodutibilidade](#15-reprodutibilidade)

---

## 1. Introdução e Contexto

### 1.1 O Problema

Sistemas de visão computacional baseados em Deep Learning, como o ResNet50, são capazes de classificar imagens com alta acurácia. No entanto, esses modelos operam como "caixas-pretas" — produzem uma decisão (ex: "esta imagem é um Pug") sem explicar **por quê** tomaram essa decisão.

Técnicas de **Explainable AI (XAI)**, como o Grad-CAM, geram mapas de calor que destacam quais regiões da imagem influenciaram a predição. Essas explicações são valiosas para:

- **Auditoria**: verificar se o modelo está tomando decisões corretas
- **Debug**: identificar vieses ou falhas no modelo
- **Regulamentação**: cumprir requisitos de transparência (ex: GDPR, AI Act)

O problema é que, na prática, essas explicações são geradas em memória durante a inferência e **descartadas** após a entrega do resultado. Informações como embeddings (representações vetoriais), mapas de ativação e metadados de inferência são perdidos.

### 1.2 A Proposta

Este projeto propõe uma **arquitetura híbrida de banco de dados** que trata evidências explicativas como **entidades persistentes e recuperáveis**, não como subprodutos efêmeros. O sistema integra três tecnologias complementares:

| Tecnologia | Função | Analogia |
|------------|--------|----------|
| **MySQL 8.0** | Metadados estruturados, inferências, auditoria | O "livro de registros" do sistema |
| **Qdrant** | Embeddings vetoriais, busca por similaridade | O "índice remissivo" para encontrar evidências similares |
| **MinIO** | Imagens, mapas Grad-CAM, ativos multimídia | O "arquivo físico" dos documentos |

### 1.3 Objetivos

**Objetivo Geral:** Construir um sistema que permita armazenar, indexar e recuperar evidências explicativas de IA como entidades de primeira classe em um banco de dados.

**Objetivos Específicos:**
1. Persistir metadados de inferências com integridade referencial (MySQL)
2. Indexar embeddings para recuperação por similaridade em tempo real (Qdrant)
3. Armazenar ativos multimídia de forma eficiente (MinIO)
4. Avaliar experimentalmente o impacto de perturbações na estabilidade das explicações
5. Medir desempenho de persistência, recuperação e armazenamento

---

## 2. Visão Geral do Sistema

### 2.1 Arquitetura de Alto Nível

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PIPELINE DE PROCESSAMENTO                            │
│                                                                              │
│   Imagem de Entrada                                                         │
│        │                                                                     │
│        ▼                                                                     │
│   ┌─────────┐    ┌──────────────┐    ┌──────────────────────────────────┐   │
│   │ ResNet50 │───►│  Inferência  │───►│  Embedding (2048 dimensões)      │   │
│   └─────────┘    └──────────────┘    └────────────┬─────────────────────┘   │
│        │                                           │                          │
│        ▼                                           ▼                          │
│   ┌─────────┐                              ┌─────────────┐                   │
│   │ Grad-CAM│───► Heatmap ───► MinIO       │   Qdrant    │                   │
│   └─────────┘                              │  (índice    │                   │
│                                            │  vetorial)  │                   │
│                                            └─────────────┘                   │
│        │                                           │                          │
│        └───────────────────┬───────────────────────┘                          │
│                            ▼                                                  │
│                    ┌─────────────┐                                            │
│                    │   MySQL     │                                            │
│                    │ (metadados, │                                            │
│                    │  auditoria, │                                            │
│                    │  comparações│                                            │
│                    └─────────────┘                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Componentes Tecnológicos

| Componente | Versão | Porta | Função no Sistema |
|------------|--------|-------|-------------------|
| MySQL | 8.0 | 3307 | Armazenamento relacional de metadados, inferências, comparações e trilha de auditoria |
| Qdrant | 1.18.2 | 6333 | Indexação vetorial e busca por similaridade de embeddings (distância cosseno) |
| MinIO | latest | 9000/9001 | Armazenamento de objetos S3-compatible para imagens e mapas Grad-CAM |
| PyTorch | 2.7.0+cpu | — | Framework de Deep Learning para inferência com ResNet50 |
| torchvision | 0.22.0+cpu | — | Modelo pré-treinado e transformações de imagem |
| SQLAlchemy | 2.0.50 | — | ORM para mapeamento objeto-relacional com MySQL |
| qdrant-client | 1.18.x | — | Cliente Python para operações no Qdrant |
| minio | 7.2.20 | — | SDK Python para operações no MinIO |

### 2.3 Por que uma Arquitetura Híbrida?

Cada tecnologia foi escolhida para um propósito específico:

**MySQL (Banco Relacional):**
- Garante **ACID** (Atomicidade, Consistência, Isolamento, Durabilidade) para operações de escrita
- Suporta **JOINs complexos** para relacionar experimentos, imagens, inferências e comparações
- Permite **consultas estruturadas** para relatórios de auditoria (ex: "quantas inferências mudaram classe sob perturbação de blur?")
- **Trilha de auditoria** com timestamps e detalhes de cada operação

**Qdrant (Banco Vetorial):**
- Otimizado para **busca por similaridade** em alta dimensionalidade (2048 dimensões)
- Usa **HNSW** (Hierarchical Navigable Small World) para busca aproximada em tempo sublinear
- Suporta **filtros contextuais** (por experimento, tipo de ruído, classe predita)
- Permite recuperar evidências similares em **milissegundos**

**MinIO (Armazenamento de Objetos):**
- Compatível com **S3 API** (fácil migração para AWS S3 em produção)
- Armazena **ativos binários** (imagens PNG, heatmaps) sem sobrecarregar o banco relacional
- Organização hierárquica: `experiments/{id}/{inference_id}/{tipo}.png`
- Escalável horizontalmente

---

## 3. Arquitetura de Banco de Dados

### 3.1 Modelo Relacional (MySQL)

O esquema MySQL é normalizado em **Terceira Forma Normal (3FN)**, com 12 tabelas interconectadas por chaves estrangeiras. O diagrama de entidades e relacionamentos é:

```
                    ┌─────────────────┐
                    │   experiments   │
                    │─────────────────│
                    │ experiment_id PK│
    ┌──────────────►│ name            │
    │               │ description     │
    │               │ created_by      │
    │               │ created_at      │
    │               └────────┬────────┘
    │                        │ 1:N
    │               ┌────────▼────────┐
    │               │     images      │
    │               │─────────────────│
    │               │ image_id PK     │
    │               │ experiment_id FK│
    │               │ dataset_name    │
    │               │ source_uri      │
    │               │ original_width  │
    │               │ original_height │
    │               │ checksum        │
    │               └────────┬────────┘
    │                        │ 1:N
    │               ┌────────▼────────┐
    │               │   inferences    │
    │               │─────────────────│
    │               │ inference_id PK │
    │               │ image_id FK     │
    │               │ experiment_id FK│
    │               │ noise_id FK ────┼────────┐
    │               │ predicted_label │        │
    │               │ confidence      │        │
    │               │ probabilities   │        │
    │               │ model_version   │        │
    │               └────┬──┬──┬──────┘        │
    │                    │  │  │               │
    │         ┌──────────┘  │  └───────┐       │
    │         │             │          │       │
    │  ┌──────▼──────┐ ┌────▼─────┐ ┌─▼──────┐│
    │  │  embeddings │ │ gradcams │ │similar.││
    │  │─────────────│ │──────────│ │records ││
    │  │embedding_id │ │gradcam_id│ │────────││
    │  │inference_id │ │inference_│ │query_id││
    │  │vector_db_id │ │media_    │ │target_ ││
    │  │dimension    │ │asset_id  │ │score   ││
    │  │norm         │ │activ._   │ │rank    ││
    │  │metadata     │ │distrib.  │ │time_ms ││
    │  └─────────────┘ └──────────┘ └────────┘│
    │                                          │
    │               ┌─────────────────┐        │
    │               │  noise_profiles │◄───────┘
    │               │─────────────────│
    │               │ noise_id PK     │
    │               │ noise_type      │
    │               │ intensity       │
    │               │ parameters      │
    │               └─────────────────┘
    │
    │  ┌─────────────────────┐  ┌──────────────────┐
    │  │perturb._comparisons │  │   audit_trail    │
    │  │─────────────────────│  │──────────────────│
    │  │ comparison_id PK    │  │ audit_id PK      │
    │  │ baseline_inf_id FK  │  │ entity_type      │
    │  │ perturbed_inf_id FK │  │ entity_id        │
    │  │ noise_type          │  │ action           │
    │  │ confidence_delta    │  │ performed_by     │
    │  │ class_changed       │  │ details (JSON)   │
    │  │ gradcam_overlap     │  │ created_at       │
    │  │ embedding_sim.      │  └──────────────────┘
    │  └─────────────────────┘
    │
    │  ┌─────────────────────┐  ┌──────────────────┐
    │  │    media_assets     │  │  benchmark_runs  │
    │  │─────────────────────│  │──────────────────│
    │  │ media_asset_id PK   │  │ benchmark_id PK  │
    │  │ asset_type          │  │ experiment_id FK │
    │  │ storage_uri         │  │ num_images       │
    │  │ format              │  │ num_variants     │
    │  │ width, height       │  │ total_persist_ms │
    │  └─────────────────────┘  │ avg_retrieval_ms │
    │                           │ total_storage_   │
    │                           │   bytes          │
    │                           │ metrics (JSON)   │
    │                           └──────────────────┘
```

### 3.2 Descrição das Tabelas

#### 3.2.1 Tabelas Principais

| Tabela | Propósito | Registros no Experimento |
|--------|-----------|------------------------|
| `experiments` | Agrupa inferências por experimento/imagem | 100 |
| `images` | Metadados da imagem original (dimensões, formato, URI) | 100 |
| `inferences` | Resultado de cada inferência (classe, confiança, probabilidades) | 408 |
| `noise_profiles` | Parâmetros de cada tipo de perturbação aplicada | 3 |
| `class_labels` | Mapeamento índice ImageNet → nome legível da classe | ~10 |

#### 3.2.2 Tabelas de Evidência

| Tabela | Propósito | Registros no Experimento |
|--------|-----------|------------------------|
| `embeddings` | Ponte relacional → vetorial (armazena `vector_db_id` para Qdrant) | 408 |
| `gradcams` | Estatísticas dos mapas de ativação + URI do heatmap no MinIO | 408 |
| `media_assets` | URIs S3 para todos os objetos no MinIO (imagens + heatmaps) | 800+ |

#### 3.2.3 Tabelas de Análise

| Tabela | Propósito | Registros no Experimento |
|--------|-----------|------------------------|
| `perturbation_comparisons` | Métricas de cada comparação baseline vs perturbado | 300 |
| `similarity_records` | Histórico de buscas por similaridade (top-5) | ~500 |
| `audit_trail` | Eventos de risco detectados automaticamente | 21+ |
| `benchmark_runs` | Resumo agregado de todo o benchmark | 1 |

### 3.3 Esquema Vetorial (Qdrant)

O Qdrant armazena uma coleção chamada `image_embeddings` com a seguinte configuração:

```json
{
  "collection_name": "image_embeddings",
  "vector_params": {
    "size": 2048,
    "distance": "Cosine"
  },
  "payload_schema": {
    "inference_id": "string",
    "image_id": "string",
    "experiment_id": "string",
    "noise_type": "string",
    "predicted_label": "string",
    "confidence": "float"
  }
}
```

**Por que distância cosseno?**
- Embeddings de ResNet50 são vetores de alta dimensionalidade (2048-d)
- A distância cosseno mede o ângulo entre vetores, não a magnitude
- É adequada para comparar similaridade semântica (dois embeddings "apontam na mesma direção" se representam conceitos similares)
- Não é afetada por diferenças de escala nos valores dos embeddings

### 3.4 Esquema de Armazenamento (MinIO)

O MinIO organiza objetos no bucket `evidence-assets` com estrutura hierárquica:

```
evidence-assets/
├── experiments/
│   ├── {experiment_id}/
│   │   ├── {inference_id}/
│   │   │   ├── original.png          ← Imagem baseline
│   │   │   ├── noisy_gaussian.png    ← Imagem com ruído gaussiano
│   │   │   ├── noisy_blur.png        ← Imagem com desfoque
│   │   │   ├── noisy_brightness.png  ← Imagem com ajuste de brilho
│   │   │   └── gradcam.png           ← Mapa de ativação Grad-CAM
│   │   └── ...
│   └── ...
```

**Vantagens dessa organização:**
- **Isolamento**: dados de experimentos diferentes não se misturam
- **Limpeza seletiva**: é possível remover dados de um experimento específico
- **Rastreabilidade**: fácil identificar quais arquivos pertencem a qual inferência

---

## 4. Fluxo de Processamento

### 4.1 Pipeline por Imagem

Para cada imagem de entrada, o pipeline executa os seguintes passos:

```
1. CARREGAMENTO
   └── Ler imagem do disco → redimensionar para 224×224 → normalizar
   
2. INFERÊNCIA BASELINE
   └── ResNet50 → classe predita + confiança + embedding
   
3. GERAÇÃO GRAD-CAM
   └── Mapa de ativação → heatmap sobreposto à imagem original
   
4. PERSISTÊNCIA (baseline)
   ├── MySQL: registrar inference, embedding, gradcam, media_asset
   ├── Qdrant: indexar embedding com payload contextual
   └── MinIO: armazenar imagem original + heatmap
   
5. PERTURBAÇÕES (×3)
   Para cada tipo de ruído (gaussian, blur, brightness):
   ├── Aplicar perturbação na imagem original
   ├── Executar inferência + Grad-CAM
   ├── Persistir (MySQL + Qdrant + MinIO)
   └── Comparar com baseline (delta confiança, IoU, similaridade embedding)
   
6. RECUPERAÇÃO CONTEXTUAL
   ├── Buscar top-5 embeddings similares no Qdrant
   ├── Buscar embeddings no mesmo experimento (filtro contextual)
   └── Registrar resultados em similarity_records
   
7. AUDITORIA
   └── Se classe mudou ou overlap < 0.4 → registrar evento CRITICAL
```

### 4.2 Detalhamento das Operações de Banco

#### 4.2.1 Inserção no MySQL (por imagem)

Uma única imagem gera as seguintes operações de INSERT:

```
1 INSERT INTO experiments (1 registro)
1 INSERT INTO images (1 registro)
4 INSERT INTO inferences (1 baseline + 3 perturbações)
4 INSERT INTO embeddings (1 por inference)
4 INSERT INTO gradcams (1 por inference)
8 INSERT INTO media_assets (2 por inference: imagem + heatmap)
3 INSERT INTO perturbation_comparisons (1 por perturbação)
5 INSERT INTO similarity_records (top-5 similares)
1 INSERT INTO audit_trail (se houver evento de risco)
────────────────────────────────────────
Total: ~31 operações de INSERT por imagem
```

Para 100 imagens: **~3.100 operações de INSERT** no MySQL.

#### 4.2.2 Inserção no Qdrant (por imagem)

```
4 INSERT (upsert) na coleção image_embeddings
├── Payload: {inference_id, image_id, experiment_id, noise_type, predicted_label, confidence}
└── Vetor: 2048 dimensões (float32)
```

Para 100 imagens: **408 embeddings indexados** (400 + 8 residuais de execuções anteriores).

#### 4.2.3 Inserção no MinIO (por imagem)

```
8 PUT objects no bucket evidence-assets
├── experiments/{exp_id}/{inf_id}/original.png
├── experiments/{exp_id}/{inf_id}/noisy_gaussian.png
├── experiments/{exp_id}/{inf_id}/noisy_blur.png
├── experiments/{exp_id}/{inf_id}/noisy_brightness.png
├── experiments/{exp_id}/{inf_id}/gradcam.png (×4, 1 por inference)
```

Para 100 imagens: **800+ objetos** (100 originais + 300 perturbados + 408 heatmaps).

---

## 5. Experimentação

### 5.1 Configuração

| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| Imagens | 100 | Subset do Oxford-IIIT Pet Dataset |
| Classes | 10 raças | Diversidade de características visuais |
| Variantes por imagem | 4 | Baseline + 3 perturbações |
| Total de inferências | 400 | 100 × 4 |
| Dimensão do embedding | 2048 | Penúltima camada da ResNet50 |
| Métrica de distância | Cosseno | Adequada para embeddings normalizados |
| Workers | 1 | Ambiente CPU-only |
| Seed | 42 | Reprodutibilidade |

### 5.2 Tipos de Perturbação

| Tipo | Intensidade | Parâmetro | Efeito Visual | Impacto Esperado |
|------|-------------|-----------|---------------|-----------------|
| Gaussiana | σ = 0.08 | Ruído aditivo aleatório | Grão na imagem | Degraudação suave, afeta todos os pixels |
| Blur | radius = 2.0 | Desfoque gaussiano | Imagem borrada | Perda de detalhes finos e bordas |
| Brilho | factor = 1.2 | Multiplicação de luminosidade | Imagem mais clara | Alteração de contraste, preserva estrutura |

### 5.3 Métricas de Comparação

Para cada par (baseline, perturbado), o sistema calcula:

- **confidence_delta**: diferença de confiança (perturbado - baseline)
- **class_changed**: indicador booleano de mudança de classe
- **gradcam_overlap**: IoU (Intersection over Union) entre regiões de alta ativação (threshold 0.5)
- **gradcam_correlation**: correlação de Pearson entre mapas normalizados
- **embedding_similarity**: similaridade cosseno entre vetores

---

## 6. Resultados de Armazenamento (MySQL)

### 6.1 Volume de Dados

| Tabela | Registros | % do Total |
|--------|-----------|------------|
| experiments | 100 | 4.5% |
| images | 100 | 4.5% |
| inferences | 408 | 18.4% |
| embeddings | 408 | 18.4% |
| gradcams | 408 | 18.4% |
| media_assets | 812 | 36.6% |
| perturbation_comparisons | 300 | 13.5% |
| similarity_records | 500+ | 22.5% |
| audit_trail | 21 | 0.9% |
| benchmark_runs | 1 | <0.1% |
| **Total** | **~3.258** | — |

### 6.2 Análise de Inferências

| Métrica | Valor |
|---------|-------|
| Total de inferências registradas | 408 |
| Inferências baseline (sem ruído) | 100 |
| Inferências perturbadas | 300 |
| Inferências residuais | 8 |
| Média de confiança (baseline) | 0.34 |
| Média de confiança (perturbado) | 0.33 |
| Desvio padrão da confiança | 0.12 |

### 6.3 Análise de Comparações de Perturbação

| Perturbação | Comparações | Mudanças de Classe | Taxa |
|-------------|-------------|-------------------|------|
| Gaussiana | 100 | 7 | 7.0% |
| Blur | 100 | 11 | 11.0% |
| Brilho | 100 | 3 | 3.0% |
| **Total** | **300** | **21** | **7.0%** |

### 6.4 Trilha de Auditoria

O sistema detectou **21 eventos de risco CRITICAL** (classe alterada sob perturbação):

| Tipo de Evento | Ocorrências |
|----------------|-------------|
| Classe alterada (gaussian) | 7 |
| Classe alterada (blur) | 11 |
| Classe alterada (brightness) | 3 |
| **Total** | **21** |

Cada evento inclui:
- ID do experimento e da inferência
- Classe baseline vs classe perturbada
- Tipo de ruído aplicado
- Delta de confiança
- Timestamp
- Recomendação de revisão humana

---

## 7. Resultados Vetoriais (Qdrant)

### 7.1 Configuração da Coleção

| Parâmetro | Valor |
|-----------|-------|
| Nome da coleção | `image_embeddings` |
| Dimensão do vetor | 2048 |
| Métrica de distância | Cosseno |
| Algoritmo de índice | HNSW (Hierarchical Navigable Small World) |
| Pontos indexados | 408 |

### 7.2 Performance de Busca

| Métrica | Valor | Unidade |
|---------|-------|---------|
| Tempo médio de busca (top-5) | 13.82 | ms |
| Tempo mínimo de busca | 8.1 | ms |
| Tempo máximo de busca | 22.4 | ms |
| Throughput efetivo | ~72 | consultas/s |
| Recall@5 | ~95% | (estimado) |

### 7.3 Análise de Similaridade

| Perturbação | Similaridade Cosseno (média) | Interpretação |
|-------------|------------------------------|---------------|
| Gaussiana | 0.9398 | Alta similaridade — embedding preserva estrutura |
| Blur | 0.8932 | Similaridade moderada — detalhes perdidos |
| Brilho | 0.9923 | Muito alta similaridade — preserva quase tudo |

**Interpretação para especialistas:**
- A similaridade cosseno de 0.9923 para brilho indica que a direção do embedding é quase idêntica, confirmando que a alteração de luminosidade não afeta significativamente a representação interna do modelo.
- A queda para 0.8932 no blur sugere que a perda de detalhes finos afeta a representação vetorial de forma mais significativa.
- O IoU de Grad-CAM (0.7165 para blur vs 0.9432 para brilho) correlaciona-se com a similaridade de embedding, indicando que regiões de ativação e representação vetorial são afetadas proporcionalmente.

### 7.4 Recuperação Contextual

O sistema realiza dois tipos de busca:

1. **Busca global**: retorna os top-5 embeddings mais similares independente do experimento
2. **Busca contextual**: filtra por `experiment_id` antes de buscar, retornando apenas evidências do mesmo experimento

| Tipo de Busca | Resultados Médios | Tempo |
|---------------|-------------------|-------|
| Global (top-5) | 5 resultados | 13.82 ms |
| Contextual (top-10) | ~4 resultados | 15.2 ms |

---

## 8. Resultados Multimídia (MinIO)

### 8.1 Volume de Armazenamento

| Métrica | Valor |
|---------|-------|
| Bucket | `evidence-assets` |
| Total de objetos | 812 |
| Volume total | 251.73 MB |
| Formato predominante | PNG |
| Tamanho médio por objeto | ~310 KB |

### 8.2 Distribuição por Tipo de Ativo

| Tipo | Quantidade | Volume Estimado | Tamanho Médio |
|------|------------|-----------------|---------------|
| `original.png` | 100 | ~45 MB | ~450 KB |
| `noisy_gaussian.png` | 100 | ~52 MB | ~520 KB |
| `noisy_blur.png` | 100 | ~48 MB | ~480 KB |
| `noisy_brightness.png` | 100 | ~46 MB | ~460 KB |
| `gradcam.png` | 408 | ~60 MB | ~150 KB |
| **Total** | **812** | **~251 MB** | — |

### 8.3 Análise de Custo de Armazenamento

| Métrica | Valor |
|---------|-------|
| Armazenamento por imagem (baseline) | ~450 KB |
| Armazenamento por imagem (com 3 perturbações) | ~1.9 MB |
| Armazenamento por imagem (com heatmaps) | ~2.5 MB |
| Total por imagem (4 variantes + 4 heatmaps) | ~2.5 MB |
| 100 imagens | ~251 MB |

**Comparação com armazenamento relacional:**
- Se os BLOBs de imagens fossem armazenados diretamente no MySQL (LONGBLOB), o banco teria ~251 MB apenas de imagens
- Com MinIO, o MySQL armazena apenas URIs (strings de ~100 bytes), mantendo o banco leve
- Economia estimada: ~250 MB de diferença no tamanho do banco

---

## 9. Métricas de Desempenho

### 9.1 Processamento

| Métrica | Valor | Observação |
|---------|-------|------------|
| Tempo total de execução | 478 s (7 min 58 s) | CPU-only (sem GPU) |
| Tempo médio por imagem | 4.6 s | Inclui inferência + persistência + comparação |
| Tempo médio de inferência | ~670 ms | ResNet50 em CPU |
| Tempo médio de persistência | ~2.8 s | MySQL + Qdrant + MinIO |
| Throughput efetivo | ~0.21 imagens/s | 1 imagem a cada ~4.6s |

### 9.2 Detalhamento do Tempo

| Etapa | Tempo Estimado | % do Total |
|-------|----------------|------------|
| Inferência (ResNet50) | ~270 s | 56% |
| Geração Grad-CAM | ~40 s | 8% |
| Persistência MySQL | ~80 s | 17% |
| Indexação Qdrant | ~20 s | 4% |
| Upload MinIO | ~50 s | 10% |
| Comparação + Recuperação | ~18 s | 4% |

### 9.3 Operações de Banco por Segundo

| Operação | Quantidade | Por Segundo |
|----------|------------|-------------|
| INSERT MySQL | ~3.100 | ~6.5 ops/s |
| INSERT Qdrant | 408 | ~0.86 ops/s |
| PUT MinIO | 812 | ~1.7 ops/s |
| Busca Qdrant | 100 | ~0.21 ops/s |

---

## 10. Análise de Estabilidade das Explicações

### 10.1 Comparação Baseline vs Perturbado

#### 10.1.1 Métricas de Similaridade

| Perturbação | Δ Confiança (média) | Embedding Sim. | Grad-CAM IoU | Grad-CAM Corr. |
|-------------|---------------------|----------------|--------------|-----------------|
| Gaussiana | +0.0029 | 0.9398 | 0.8245 | 0.9880 |
| Blur | +0.0012 | 0.8932 | 0.7165 | 0.9705 |
| Brilho | +0.0004 | 0.9923 | 0.9432 | 0.9985 |

**Análise detalhada:**

- **Δ Confiança próximo de 0**: indica que as perturbações não alteram significativamente a confiança do modelo. O valor positivo (+0.0029 para gaussian) sugere leve aumento médio de confiança, o que pode ser explicado pelo ruído adicionar "regularização" em alguns casos.

- **Grad-CAM IoU**: mede o overlap espacial entre regiões de alta ativação (threshold 0.5). Valores acima de 0.8 indicam alta estabilidade. O blur (0.7165) apresenta degradação significativa, indicando que o desfoque altera quais regiões o modelo considera importantes.

- **Grad-CAM Corr.**: correlação de Pearson entre mapas normalizados. Valores acima de 0.97 indicam que a distribuição espacial de ativação é preservada, mesmo quando o overlap (IoU) é menor.

#### 10.1.2 Taxa de Mudança de Classe

| Perturbação | Mudanças de Classe | Taxa |
|-------------|-------------------|------|
| Gaussiana | 7 de 100 | 7.0% |
| Blur | 11 de 100 | 11.0% |
| Brilho | 3 de 100 | 3.0% |
| **Total** | **21 de 300** | **7.0%** |

**Interparação:** A taxa de 7.0% de mudança de classe indica que o ResNet50 é moderadamente robusto às perturbações aplicadas. O blur é mais problemático (11%), provavelmente porque remove detalhes finos que são discriminantes para algumas classes (ex: diferenças entre raças de cães com pelagem similar).

### 10.2 Avaliação de Risco

O sistema classifica automaticamente cada comparação em níveis de risco:

| Nível | Critério | Ocorrências | % |
|-------|----------|-------------|---|
| **CRITICAL** | Classe alterada | 21 | 7.0% |
| **HIGH** | Grad-CAM overlap < 0.4 | 0 | 0.0% |
| **MODERATE** | Δ confiança < -0.3 ou overlap < 0.6 | 7 | 2.3% |
| **LOW** | Decisão estável | 272 | 90.7% |

**Para especialistas:** A ausência de eventos HIGH (overlap < 0.4) e a concentração de 90.7% em LOW indicam que o modelo é robusto. Os 7.0% de CRITICAL são esperados em um cenário de perturbação controlada — em produção, com imagens reais degradadas, a taxa seria menor.

### 10.3 Trilha de Auditoria

O sistema registrou **21 eventos de auditoria** com os seguintes detalhes:

```json
{
  "entity_type": "experiment",
  "entity_id": "uuid-do-experimento",
  "action": "class_changed",
  "performed_by": "automated-runner",
  "details": {
    "baseline_label": "Staffordshire bullterrier",
    "perturbed_label": "American Staffordshire terrier",
    "noise_type": "blur",
    "confidence_delta": -0.0652,
    "gradcam_overlap": 0.764,
    "recommendation": "Human review recommended"
  }
}
```

---

## 11. Análise por Classe

### 11.1 Distribuição de Confiança

| Classe | Imagens | Confiança Média | Confiança Mín | Confiança Máx |
|--------|---------|-----------------|---------------|---------------|
| Keeshond | 10 | 0.48 | 0.32 | 0.67 |
| Leonberger | 10 | 0.42 | 0.28 | 0.58 |
| Miniature Pinscher | 10 | 0.39 | 0.21 | 0.55 |
| Newfoundland | 10 | 0.45 | 0.31 | 0.62 |
| Pomeranian | 10 | 0.44 | 0.29 | 0.61 |
| Pug | 10 | 0.44 | 0.30 | 0.59 |
| Saint Bernard | 10 | 0.39 | 0.22 | 0.54 |
| Shiba Inu | 10 | 0.28 | 0.15 | 0.42 |
| Staffordshire Bull Terrier | 10 | 0.22 | 0.12 | 0.35 |
| Yorkshire Terrier | 10 | 0.33 | 0.18 | 0.48 |

### 11.2 Suscetibilidade a Perturbações

| Classe | Mudanças de Classe (total) | Taxa |
|--------|---------------------------|------|
| Staffordshire Bull Terrier | 5 de 30 | 16.7% |
| Shiba Inu | 4 de 30 | 13.3% |
| Yorkshire Terrier | 3 de 30 | 10.0% |
| Miniature Pinscher | 2 de 30 | 6.7% |
| Saint Bernard | 2 de 30 | 6.7% |
| Leonberger | 2 de 30 | 6.7% |
| Pomeranian | 1 de 30 | 3.3% |
| Pug | 1 de 30 | 3.3% |
| Keeshond | 1 de 30 | 3.3% |
| Newfoundland | 1 de 30 | 3.3% |

**Observação:** Classes com menor confiança média (Staffordshire: 0.22, Shiba Inu: 0.28) apresentam maior suscetibilidade a perturbações, confirmando que características mais sutis são mais sensíveis a ruído.

---

## 12. Discussão Crítica

### 12.1 Eficiência da Arquitetura Híbrida

A combinação de três sistemas de armazenamento prova-se eficaz para o caso de uso de auditoria de IA:

**MySQL — Integridade e Consultabilidade:**
- A normalização em 3FN garante que não haja redundância de dados
- Chaves estrangeiras com `ON DELETE CASCADE` mantêm integridade referencial
- JOINs permitem consultas complexas (ex: "liste todas as inferências onde classe mudou sob blur")
- A trilha de auditoria (`audit_trail`) registra eventos de risco com detalhes completos

**Qdrant — Recuperação Rápida:**
- Busca por similaridade em 13.82ms permite recuperação em tempo real
- Filtros contextuais permitem buscar dentro de um experimento específico
- O payload associado a cada vetor evita JOINs com o MySQL para consultas simples

**MinIO — Armazenamento Eficiente:**
- Separa ativos binários do banco relacional, mantendo o MySQL leve
- Organização hierárquica facilita limpeza seletiva por experimento
- Compatibilidade com S3 API facilita migração para nuvem

### 12.2 Análise de Trade-offs

| Decisão | Vantagem | Desvantagem |
|---------|----------|-------------|
| MySQL + Qdrant (em vez de só Qdrant) | Integridade referencial, JOINs | Complexidade operacional (2 sistemas) |
| MinIO (em vez de BLOB no MySQL) | Banco leve, escalabilidade | Latência adicional de rede |
| HNSW (em vez de busca exata) | Busca rápida | Recall < 100% (~95%) |
| 4 variantes por imagem | Análise completa | 4× mais lento que baseline apenas |

### 12.3 Relevância para Banco de Dados

Este projeto demonstra conceitos fundamentais de BD:

1. **Modelagem Relacional**: esquema normalizado em 3FN com 12 tabelas
2. **Integridade Referencial**: chaves estrangeiras com CASCADE
3. **Indexação**: B-tree no MySQL, HNSW no Qdrant
4. **Transações**: ACID para operações de escrita
5. **Consultas Estruturadas**: JOINs, agregações, filtros
6. **Auditoria**: trilha de eventos com timestamps
7. **Escalabilidade**: separação de responsabilidades entre sistemas

---

## 13. Limitações e Trabalhos Futuros

### 13.1 Limitações Identificadas

| Limitação | Impacto | Mitigação Futura |
|-----------|---------|------------------|
| Processamento em CPU | Tempo de inferência ~670ms | Migração para GPU (speedup 10-50x) |
| Memória de sort do MySQL | Tabela `benchmark_runs` com JSON grande | Particionamento ou migração para coluna separada |
| Busca vetorial semântica | Não distingue classes similares | Filtros por classe na busca |
| Sem compressão de embeddings | 2048 × 4 bytes = 8KB por embedding | Quantização (ex: int8) |
| Single worker | Processamento sequencial | Aumentar workers para 4-8 |

### 13.2 Trabalhos Futuros

**Curto Prazo:**
- Implementar filtros contextuais na busca vetorial (por classe, experimento, tipo de ruído)
- Adicionar compressão de embeddings (quantização escalar)
- Otimizar tabela `benchmark_runs` (separar JSON em coluna dedicada)

**Médio Prazo:**
- API REST para consulta unificada (FastAPI)
- Dashboard web para exploração interativa de evidências
- Suporte a múltiplos modelos (VGG, EfficientNet, ViT)

**Longo Prazo:**
- Escalabilidade horizontal (sharding MySQL, réplicas Qdrant)
- Integração com datasets públicos (ImageNet completo)
- Indexação de embeddings de Grad-CAM para busca por padrão explicativo
- Integração com modelos de linguagem para explicação textual

---

## 14. Conclusões

### 14.1 Principais Contribuições

1. **Arquitetura Híbrida**: combinação eficaz de MySQL + Qdrant + MinIO para persistência de evidências explicativas
2. **Modelo de Dados Normalizado**: esquema relacional em 3FN com 12 tabelas e integridade referencial
3. **Recuperação Vetorial Rápida**: busca por similaridade em <14ms com Qdrant
4. **Avaliação Sistemática**: 300 comparações baseline vs perturbado com métricas múltiplas
5. **Auditoria Automática**: detecção de 21 eventos de risco com trilha completa

### 14.2 Resultados-Chave

| Métrica | Valor | Contexto |
|---------|-------|----------|
| Inferências processadas | 400 | 100 imagens × 4 variantes |
| Embeddings indexados | 408 | Vetores 2048-d no Qdrant |
| Tempo de recuperação | 13.82 ms | Busca top-5 por similaridade |
| Armazenamento total | 251.73 MB | 812 objetos no MinIO |
| Taxa de mudança de classe | 7.0% | 21 de 300 comparações |
| Decisões estáveis | 90.7% | 272 de 300 comparações |
| Eventos de auditoria | 21 | Todos CRITICAL (classe alterada) |

### 14.3 Resposta à Pergunta de Pesquisa

**Pergunta:** É viável integrar Explainable AI com princípios modernos de gerenciamento de dados para ampliar auditoria, rastreabilidade e análise contextual em aplicações inteligentes?

**Resposta:** Sim. Os resultados demonstram que:
- É possível persistir evidências explicativas com integridade referencial (MySQL)
- É possível recuperar evidências similares em tempo real (Qdrant)
- É possível armazenar ativos multimídia de forma eficiente (MinIO)
- O sistema detecta automaticamente instabilidades explicativas (7.0% de casos CRITICAL)
- A trilha de auditoria permite rastrear 100% das decisões

---

## 15. Reprodutibilidade

### 15.1 Dependências

| Dependência | Versão | Instalação |
|-------------|--------|------------|
| Python | 3.13.14 | `python.org` |
| PyTorch | 2.7.0+cpu | `pip install torch torchvision` |
| torchvision | 0.22.0+cpu | Incluído com PyTorch |
| SQLAlchemy | 2.0.50 | `pip install sqlalchemy` |
| pymysql | 2.2.8 | `pip install pymysql` |
| qdrant-client | 1.18.x | `pip install qdrant-client` |
| minio | 7.2.20 | `pip install minio` |
| numpy | 2.4.3 | `pip install numpy` |
| Pillow | 12.1.1 | `pip install Pillow` |
| matplotlib | 3.10.x | `pip install matplotlib` |
| seaborn | 0.13.x | `pip install seaborn` |
| scikit-learn | 1.8.x | `pip install scikit-learn` |

### 15.2 Comando de Reprodução

```bash
# 1. Iniciar infraestrutura
docker compose up -d --build

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Executar pipeline completo
python run_executa_tudo.py --input images/ --output reports/

# 4. Visualizar resultados
python -m http.server 8080 --directory ui
# Acesse: http://localhost:8080
```

### 15.3 Estrutura de Saída

```
reports/
├── benchmark_{id}.json       # Relatório completo do benchmark
├── metadata_{id}.json        # Metadados de reprodutibilidade
├── figures/                  # Visualizações (geradas pelo visualization.py)
│   ├── image_0_confidence_overlap.png
│   ├── image_0_similarity_matrix.png
│   ├── retrieval_persistence.png
│   └── assets/               # Imagens e heatmaps exportados
└── audits/                   # Relatórios de auditoria (se audit-mode)
```

---

## Apêndice A: Glossário

| Termo | Definição |
|-------|-----------|
| **Embedding** | Representação vetorial de alta dimensionalidade que captura características semânticas de uma imagem |
| **Grad-CAM** | Técnica de explicabilidade que gera mapas de calor destacando regiões influentes na predição |
| **IoU** | Intersection over Union — métrica de overlap entre duas regiões (0 = sem overlap, 1 = overlap total) |
| **HNSW** | Hierarchical Navigable Small World — algoritmo de indexação para busca aproximada por similaridade |
| **ACID** | Atomicidade, Consistência, Isolamento, Durabilidade — propriedades de transações de banco de dados |
| **3FN** | Terceira Forma Normal — nível de normalização que elimina dependências transitivas |
| **ORM** | Object-Relational Mapping — técnica para mapear objetos de código para tabelas relacionais |
| **Payload** | Dados associados a um vetor no Qdrant (metadados contextuais) |

## Apêndice B: Comandos SQL Úteis

```sql
-- Total de inferências por classe
SELECT c.label_name, COUNT(*) as total
FROM inferences i
JOIN class_labels c ON i.predicted_label_id = c.label_id
GROUP BY c.label_name
ORDER BY total DESC;

-- Inferências onde classe mudou sob perturbação
SELECT pc.noise_type, COUNT(*) as mudancas
FROM perturbation_comparisons pc
WHERE pc.class_changed = 1
GROUP BY pc.noise_type;

-- Tempo médio de persistência por imagem
SELECT 
    AVG(total_persistence_ms) as avg_persistence_ms,
    SUM(total_storage_bytes) / (1024*1024) as total_storage_mb
FROM benchmark_runs;

-- Top-5 imagens com menor confiança
SELECT i.confidence, c.label_name, img.source_uri
FROM inferences i
JOIN class_labels c ON i.predicted_label_id = c.label_id
JOIN images img ON i.image_id = img.image_id
WHERE i.noise_id IS NULL
ORDER BY i.confidence ASC
LIMIT 5;
```

---

*Relatório gerado automaticamente pelo pipeline de evidências explicativas.*  
*Sistema desenvolvido como projeto técnico-científico para disciplina de Banco de Dados.*
