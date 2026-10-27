<<<<<<< HEAD
# Tripartite XAI Engine: Persistência Híbrida para Evidências Explicativas

Projeto integrado técnico-científico que investiga e implementa uma **arquitetura de persistência tripartite** (relacional, vetorial e armazenamento de objetos) para evidências produzidas por modelos de visão computacional explicável (XAI).

O projeto reúne o artigo acadêmico completo em formato ABNT, a infraestrutura conteinerizada em Docker, o pipeline operacional com ResNet-50 e Grad-CAM, e a suíte completa de validação experimental.

---

## 1. Visão Geral e Contexto

Em sistemas tradicionais de IA explicável, mapas de calor como Grad-CAM são comumente descartados após a exibição ou gravados em diretórios isolados sem contexto estruturado. Esta arquitetura trata explicações de IA como dados de pesquisa de primeira classe, garantindo **rastreabilidade**, **auditabilidade** e **recuperação rápida**:

1. **MySQL 8.0**: Metadados relacionais normalizados (3FN), predições, parâmetros de ruído, métricas comparativas e trilha de auditoria com integridade referencial.
2. **Qdrant**: Banco de dados vetorial para indexação de embeddings densos (2048 dimensões da penúltima camada da ResNet-50) e busca por similaridade em sub-segundo.
3. **MinIO (S3-compatible)**: Armazenamento distribuído de objetos para imagens brutas e mapas de calor Grad-CAM em alta resolução, evitando sobrecarga com BLOBs no banco relacional.

---

## 2. Configuração Experimental e Dataset

- **Dataset**: 100 imagens do Oxford-IIIT Pet Dataset (10 raças distintas, 10 imagens por raça).
- **Modelo de Visão**: ResNet-50 pré-treinada no ImageNet (`IMAGENET1K_V2`).
- **Explicações**: Grad-CAM na última camada convolucional (`layer4`).
- **Perturbações Controladas**:
  - Baseline (imagem original sem perturbação)
  - Ruído Gaussiano ($\sigma = 0.08$)
  - Desfoque Gaussiano (Blur, raio $= 2.0$)
  - Ajuste de Brilho (Brightness factor $= 1.2$)
- **Total de Inferências**: 400 inferências (100 imagens $\times$ 4 variantes).
- **Total de Comparações de Risco**: 300 pares baseline-perturbado.

---

## 3. Stack Tecnológico

| Componente | Tecnologia | Porta Host | Finalidade |
|---|---|---|---|
| **Banco Relacional** | MySQL 8.0 | `3307` | Metadados, auditoria e consultas relacionais |
| **Banco Vetorial** | Qdrant | `6333` (HTTP) / `6334` (gRPC) | Embeddings e busca contextual por similaridade |
| **Object Storage** | MinIO (S3) | `9000` (API) / `9001` (Console) | Armazenamento de imagens e mapas Grad-CAM |
| **Backbone & XAI** | PyTorch & Torchvision | Container Debian | ResNet-50 e gradientes Grad-CAM |
| **Gerador de Artigo** | FPDF2 | Host Python | Compilação do artigo acadêmico ABNT em PDF |

---

## 4. Como Executar

### Pré-requisitos
- **Docker Desktop** (com backend WSL2 no Windows ou Docker Engine no Linux)
- **Python 3.10+**

### Instalação das Dependências Locais

```bash
pip install -r requirements.txt
```

### Execução Completa (Pipeline Unificado)

Para rodar todo o ciclo (limpeza, infraestrutura, benchmark completo de 100 imagens, gráficos analíticos e compilação do artigo PDF):

```bash
python run_executa_tudo.py
```

### Validação da Infraestrutura e Pipeline

Para validar a integridade dos 3 bancos de dados e do pipeline antes ou depois de experimentos:

```bash
python experiment_validation/run_validation.py
```

### Compilação do Artigo Acadêmico em PDF

Para compilar o artigo científico formatado segundo as normas ABNT:
=======
# Persistência Híbrida para Evidências de Explicabilidade (XAI)

[![Artigo](https://img.shields.io/badge/Artigo-Compilado_PDF-red?logo=adobe-acrobat-reader&logoColor=white)](Artigo_Banco_Dados_Eduardo_Lazaro.pdf)
[![Pós-Graduação](https://img.shields.io/badge/UNESP-PPGCC_Computação-0055A5)](https://www.unesp.br/)
[![Bancos](https://img.shields.io/badge/Stack-MySQL_+_Qdrant_+_MinIO-blue)](#)
[![Status](https://img.shields.io/badge/Compilação-100%25_Validada-success)](#)

Repositório científico reunindo a fundamentação teórica, diagramas e rotina de compilação do artigo acadêmico sobre **persistência híbrida e governança de evidências de inteligência artificial explicável (XAI)**, desenvolvido no Programa de Pós-Graduação em Ciência da Computação da **UNESP**.

---

## 📌 1. Proposta Técnica e Arquitetura Tripartite

A proposta unifica três tecnologias complementares para solucionar o descarte de mapas de atenção visual (Grad-CAM):

1. **MySQL 8.0 (Camada Relacional):** Metadados estruturados, parâmetros de inferência, predições, métricas de risco e logs de auditoria ACID.
2. **Qdrant (Camada Vetorial):** Embeddings semânticos de 512 dimensões indexados com grafo HNSW para recuperação top-k por similaridade visual de atenção.
3. **MinIO (Armazenamento de Objetos S3):** Persistência distribuída de imagens brutas em alta resolução e heatmaps Grad-CAM volumosos.

---

## 📊 2. Evidências Visuais e Resultados

| Recurso | Evidência Gráfica |
| :--- | :--- |
| **Arquitetura Tripartite** | ![Arquitetura](evidencias/figure_3.png) |
| **Grad-CAM Baseline** | ![Original](evidencias/02_gradcam_original.png) |
| **Grad-CAM sob Ruído** | ![Ruído](evidencias/04_gradcam_gaussian.png) |
| **Grad-CAM sob Desfoque** | ![Desfoque](evidencias/06_gradcam_blur.png) |

---

## ⚙️ 3. Compilação do Artigo em PDF

O script de geração utiliza `fpdf2` e fontes do sistema para produzir o PDF formatado nas normas ABNT:
>>>>>>> 62dd760b3ebdfabcb237f0436f8e9a4a12c61caa

```bash
# Instalar biblioteca
pip install fpdf2

# Compilar artigo
python gerar_artigo_pdf.py
```
<<<<<<< HEAD
O documento será gerado na raiz: `Artigo_Banco_Dados_Eduardo_Lazaro.pdf`.

### Visualização na Interface Web

Para inspecionar visualmente as evidências explicativas no navegador:

```bash
cd ui && python -m http.server 8080
```
Acesse `http://localhost:8080`.

---

## 5. Resultados Consolidados do Benchmark (100 Imagens / 400 Inferências)

| Métrica | Resultado Validado | Observação |
|---|---|---|
| **Imagens Processadas** | 100 | 10 raças representativas |
| **Total de Inferências** | 400 | 100 baseline + 300 variantes |
| **Tempo Médio de Persistência** | 3.706 ms / imagem | 4 inferências + 4 Grad-CAMs + 3 armazenamentos |
| **Latência de Recuperação Top-5** | 53,1 ms | Busca vetorial no Qdrant + filtros relacionais |
| **Armazenamento Multimídia (MinIO)** | 218,06 MB | 800 objetos PNG (400 imagens + 400 mapas) |
| **Overlap Grad-CAM Médio (IoU)** | 0,8439 (84,4%) | Estabilidade espacial sob perturbação |
| **Classificação de Risco** | 8 CRITICAL (2,7%), 1 HIGH, 8 MODERATE, 283 LOW | Detecção automática de instabilidade |

---

## 6. Estrutura do Repositório

```
artigo-bd/
├── src/                                  # Código-fonte principal do pipeline
│   ├── benchmark.py                      # Orquestrador do benchmark completo
│   ├── processor.py                      # Processamento de imagens e persistência tripartite
│   ├── pipeline.py                       # Inferência e pré-processamento
│   ├── persistence.py                    # Modelos ORM (SQLAlchemy) e cliente Qdrant
│   ├── gradcam.py                        # Implementação PyTorch de Grad-CAM
│   ├── noise.py                          # Funções de perturbação de imagens
│   ├── storage.py                        # Cliente MinIO / S3
│   ├── search.py                         # Busca vetorial híbrida e contextual
│   ├── metrics.py                        # IoU, correlação de Pearson e similaridade cosseno
│   ├── reproducibility.py                # Captura de sementes e metadados de ambiente
│   ├── audit_report.py                   # Geração de relatórios de auditoria
│   └── config.py                         # Variáveis de ambiente e conexões
├── experiment_validation/                # Suíte de testes automatizados
│   ├── 01_check_infrastructure.py        # Verificação de portas e containers
│   ├── 02_check_database.py              # Verificação de schemas e tabelas
│   ├── 03_check_pipeline.py              # Teste end-to-end de 1 imagem no pipeline
│   ├── 04_generate_report.py             # Consolidador de relatórios de validação
│   └── run_validation.py                 # Runner principal da suíte de testes
├── tools/                                # Scripts de manutenção e visualização
│   ├── cleanup.py                        # Reset controlado dos bancos e buckets
│   ├── visualization.py                  # Geração de figuras analíticas e heatmaps
│   └── export_ui.py                      # Exportação de manifesto para UI
├── sql/                                  # Scripts SQL
│   └── schema.sql                        # DDL das 12 tabelas relacionais do MySQL
├── images/                               # Dataset de 100 imagens de teste (Oxford-IIIT Pet)
├── assets/                               # Figuras, diagramas de arquitetura e gráficos analíticos
├── reports/                              # Relatórios JSON, metadados e figuras geradas
├── ui/                                   # Dashboard web para inspeção visual
├── docker-compose.yml                    # Definição dos serviços MySQL, Qdrant, MinIO e Pipeline
├── Dockerfile                            # Imagem Docker do pipeline com PyTorch CPU
├── gerar_artigo_pdf.py                   # Script de compilação do artigo acadêmico (ABNT)
├── run_executa_tudo.py                   # Script mestre de automação completa
├── Artigo_Banco_Dados_Eduardo_Lazaro.pdf # Artigo final compilado
└── requirements.txt                      # Dependências consolidadas do projeto
```

---

## 7. Apresentação do Portfólio

**Texto de Apresentação:**
> Este trabalho investiga como transformar evidências de explicabilidade em visão computacional em dados recuperáveis, auditáveis e estruturados. A proposta integra banco relacional (MySQL), busca vetorial (Qdrant) e armazenamento de objetos (MinIO) para rastrear predições, embeddings densos, mapas Grad-CAM e perturbações em uma mesma trilha de governança. O pipeline demonstrou recuperação híbrida em ~53 ms e persistência completa em ~3,7 s por imagem, permitindo auditar retroativamente instabilidades de modelos de Deep Learning em conformidade com requisitos da LGPD e AI Act.
=======
O documento será compilado e salvo na raiz como `Artigo_Banco_Dados_Eduardo_Lazaro.pdf`.

---

## 📁 4. Estrutura do Repositório

```text
artigo-bd/
├── assets/                                      # Figuras originais do artigo
├── evidencias/                                  # Evidências e diagramas organizados
│   ├── figure_3.png
│   ├── 02_gradcam_original.png
│   ├── 04_gradcam_gaussian.png
│   └── 06_gradcam_blur.png
├── 01_minha_poroposta.md                        # Delimitação do problema e arquitetura
├── 02_base.md                                   # Metodologia e resultados reportados
├── 03_orientacoes_finais_banco_dados.md         # Diretrizes acadêmicas
├── RELATORIO_CRITICO.md                         # Avaliação crítica e limites
├── gerar_artigo_pdf.py                          # Compilador do artigo em PDF
├── Artigo_Banco_Dados_Eduardo_Lazaro.pdf        # Artigo acadêmico final em PDF
├── Artigo_BD_Relatorio_Publicacao.docx          # Relatório executivo completo em Word
├── APRESENTACAO.md                              # Roteiro de pitch e divulgação
└── README.md                                    # Documentação técnica
```

---

## 📄 5. Material de Publicação para Portfólio

O relatório executivo diagramado em Word, contendo a análise metodológica, tabela completa de latência e benchmark e roteiro editorial para redes profissionais, está disponível em [`Artigo_BD_Relatorio_Publicacao.docx`](file:///d:/projetos/artigo-bd/Artigo_BD_Relatorio_Publicacao.docx).
>>>>>>> 62dd760b3ebdfabcb237f0436f8e9a4a12c61caa
