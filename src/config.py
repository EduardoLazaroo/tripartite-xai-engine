"""
Configuracoes centralizadas do projeto.

Este arquivo concentra todas as variaveis de ambiente e constantes
utilizadas pela aplicacao. Os valores podem ser sobrescritos via
arquivo .env na raiz do projeto.

Variaveis de ambiente suportadas:
    - DATABASE_DSN: string de conexao MySQL
    - QDRANT_URL: URL do servidor Qdrant
    - QDRANT_API_KEY: chave de API do Qdrant (opcional)
    - QDRANT_COLLECTION: nome da colecao vetorial
    - MINIO_ENDPOINT: endpoint do MinIO
    - MINIO_ACCESS_KEY / MINIO_SECRET_KEY: credenciais MinIO
    - MINIO_BUCKET: nome do bucket de armazenamento
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_PATH = Path(__file__).resolve().parent
load_dotenv(BASE_PATH.parent / '.env')

# === Banco de Dados Relacional (MySQL) ===
DATABASE_DSN = os.getenv(
    "DATABASE_DSN",
    "mysql+pymysql://evidence_user:evidence_pass@127.0.0.1:3307/evidence_db"
)

# === Banco Vetorial (Qdrant) ===
QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "image_embeddings")

# === Armazenamento de Objetos (MinIO) ===
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "evidence-assets")

# === Constantes do Pipeline ===
EMBEDDING_DIMENSION = 2048  # Dimensao do embedding ResNet50
MIRROR_IMAGE_FORMAT = "png"  # Formato de imagem para armazenamento
IMAGE_TARGET_SIZE = (224, 224)  # Tamanho de entrada do modelo

# === Modo de Busca Vetorial ===
# Controla o comportamento da busca por similaridade no Qdrant:
#   - "filtered": recupera apenas imagens da MESMA classe prevista (recomendado para auditoria)
#   - "global": recupera imagens semanticamente semelhantes independentemente da classe
#                (util para avaliacao global dos embeddings)
SEARCH_MODE = os.getenv("SEARCH_MODE", "filtered")
