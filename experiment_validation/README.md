# Validacao do Experimento

Esta pasta contem scripts para validar o ambiente antes de rodar o experimento completo.

## Como Usar

### Validacao Completa (recomendado antes do primeiro experimento)

```bash
python experiment_validation/run_validation.py
```

### Validacao Rapida (so infraestrutura)

```bash
python experiment_validation/run_validation.py --infra-only
```

### Validacao sem Pipeline (mais rapido)

```bash
python experiment_validation/run_validation.py --skip-pipeline
```

## O que e Validado

### 1. Infraestrutura (`01_check_infrastructure.py`)
- Docker rodando
- Containers do docker-compose ativos
- Portas acessiveis (3307, 6333, 9000)
- Health endpoints

### 2. Bancos de Dados (`02_check_database.py`)
- Conexao com MySQL
- Schema das tabelas
- Conexao com Qdrant
- Colecao vetorial
- Conexao com MinIO
- Bucket de armazenamento

### 3. Pipeline (`03_check_pipeline.py`)
- Carregamento do modelo ResNet50
- Preprocessamento de imagem
- Inferencia
- Extracao de embedding
- Geracao de Grad-CAM
- Persistencia em todas as camadas
- Recuperacao por similaridade

### 4. Relatorio (`04_generate_report.py`)
- Relatorio em texto
- Relatorio em HTML
- Dados em JSON

### 5. Visualizacoes (`05_generate_plots.py`)
- Diagrama de arquitetura
- Grafico de status
- Grafico de tempos
- Tabela de comparacao

## Estrutura de Saida

```
experiment_validation/
├── reports/
│   ├── validation_report.txt
│   ├── validation_report.html
│   ├── validation_report.json
│   ├── architecture_diagram.png
│   ├── validation_status.png
│   ├── validation_timing.png
│   └── comparison_table.png
└── ...
```

## Interpretacao dos Resultados

### Todas as verificacoes passaram
```
TODAS AS VERIFICACOES PASSARAM!
Voce pode rodar o experimento com seguranca:
python run_executa_tudo.py
```

### Algumas verificacoes falharam
```
ALGUMAS VERIFICACOES FALHARAM!
Corrija os problemas antes de rodar o experimento.
```

## Solucao de Problemas

### Docker nao esta rodando
```bash
docker compose up -d
```

### Porta em uso
Edite `docker-compose.yml` e altere o mapeamento de portas.

### Erro de conexao com MySQL
Verifique se o container MySQL esta saudavel:
```bash
docker compose ps mysql
docker compose logs mysql
```

### Erro de conexao com Qdrant
```bash
docker compose ps qdrant
curl http://127.0.0.1:6333/health
```

### Erro de conexao com MinIO
```bash
docker compose ps minio
curl http://127.0.0.1:9000/minio/health/live
```
