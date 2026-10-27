"""
Persistencia e acesso a dados.

Este modulo define:
    - Modelos ORM (SQLAlchemy) para MySQL
    - Cliente de banco relacional (DatabaseClient)
    - Cliente de banco vetorial (QdrantClient)

Tabelas do banco relacional:
    - experiments: metadados dos experimentos
    - images: informacoes das imagens processadas
    - noise_profiles: configuracoes de ruido aplicadas
    - class_labels: rotulos de classes
    - media_assets: ativos de midia (imagens, Grad-CAMs)
    - inferences: resultados de inferencia do modelo
    - embeddings: vetores de embedding indexados
    - gradcams: mapas de ativacao Grad-CAM
    - similarity_records: registros de busca por similaridade
    - perturbation_comparacoes: comparacoes baseline vs perturbado
    - audit_trail: trilha de auditoria
    - benchmark_runs: resultados de benchmarks
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    TEXT,
    FLOAT,
    INTEGER,
    Boolean,
    Column,
    ForeignKey,
    String,
)
from config import EMBEDDING_DIMENSION
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

from qdrant_client import QdrantClient as QdrantApiClient
from qdrant_client.http import models as rest

Base = declarative_base()


class Experiment(Base):
    """Tabela de experimentos.
    
    Armazena metadados de cada experimento executado,
    incluindo nome, description e data de criacao.
    """
    __tablename__ = 'experiments'
    experiment_id = Column(String(36), primary_key=True)
    name = Column(TEXT, nullable=False)
    description = Column(TEXT)
    created_by = Column(TEXT)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)


class Image(Base):
    __tablename__ = 'images'
    image_id = Column(String(36), primary_key=True)
    dataset_name = Column(TEXT)
    source_uri = Column(TEXT)
    original_width = Column(INTEGER)
    original_height = Column(INTEGER)
    checksum = Column(TEXT)
    format = Column(TEXT)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)


class NoiseProfile(Base):
    __tablename__ = 'noise_profiles'
    noise_id = Column(String(36), primary_key=True)
    noise_type = Column(TEXT, nullable=False)
    intensity = Column(FLOAT)
    kernel_size = Column(TEXT)
    parameters = Column(JSON)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)


class ClassLabel(Base):
    __tablename__ = 'class_labels'
    label_id = Column(String(36), primary_key=True)
    label_name = Column(TEXT, nullable=False)
    hierarchy_path = Column(TEXT)
    description = Column(TEXT)


class MediaAsset(Base):
    __tablename__ = 'media_assets'
    media_asset_id = Column(String(36), primary_key=True)
    asset_type = Column(TEXT, nullable=False)
    storage_uri = Column(TEXT, nullable=False)
    checksum = Column(TEXT)
    format = Column(TEXT)
    width = Column(INTEGER)
    height = Column(INTEGER)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)


class Inference(Base):
    __tablename__ = 'inferences'
    inference_id = Column(String(36), primary_key=True)
    image_id = Column(String(36), ForeignKey('images.image_id'))
    experiment_id = Column(String(36), ForeignKey('experiments.experiment_id'))
    noise_id = Column(String(36), ForeignKey('noise_profiles.noise_id'))
    predicted_label_id = Column(String(36), ForeignKey('class_labels.label_id'))
    confidence = Column(FLOAT)
    probabilities = Column(JSON)
    preprocessing_steps = Column(JSON)
    model_version = Column(TEXT)
    inference_duration_ms = Column(INTEGER)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    image = relationship('Image')
    experiment = relationship('Experiment')
    noise = relationship('NoiseProfile')
    predicted_label = relationship('ClassLabel')


class Embedding(Base):
    __tablename__ = 'embeddings'
    embedding_id = Column(String(36), primary_key=True)
    inference_id = Column(String(36), ForeignKey('inferences.inference_id'))
    vector_db_id = Column(TEXT, nullable=False)
    dimension = Column(INTEGER, nullable=False)
    norm = Column(FLOAT)
    embedding_metadata = Column(JSON)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    inference = relationship('Inference')


class GradCam(Base):
    __tablename__ = 'gradcams'
    gradcam_id = Column(String(36), primary_key=True)
    inference_id = Column(String(36), ForeignKey('inferences.inference_id'))
    media_asset_id = Column(String(36), ForeignKey('media_assets.media_asset_id'))
    activation_distribution = Column(JSON)
    region_stats = Column(JSON)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    inference = relationship('Inference')
    media_asset = relationship('MediaAsset')


class SimilarityRecord(Base):
    __tablename__ = 'similarity_records'
    similarity_id = Column(String(36), primary_key=True)
    query_inference_id = Column(String(36), ForeignKey('inferences.inference_id'))
    target_inference_id = Column(String(36), ForeignKey('inferences.inference_id'))
    embedding_similarity = Column(FLOAT)
    gradcam_overlap = Column(FLOAT)
    distance_metric = Column(TEXT)
    rank = Column(INTEGER)
    retrieval_time_ms = Column(INTEGER)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)


class AuditTrail(Base):
    __tablename__ = 'audit_trail'
    audit_id = Column(String(36), primary_key=True)
    entity_type = Column(TEXT, nullable=False)
    entity_id = Column(String(36))
    action = Column(TEXT, nullable=False)
    performed_by = Column(TEXT)
    user_agent = Column(TEXT)
    details = Column(JSON)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)


class PerturbationComparison(Base):
    __tablename__ = 'perturbation_comparisons'
    comparison_id = Column(String(36), primary_key=True)
    baseline_inference_id = Column(String(36), ForeignKey('inferences.inference_id'))
    perturbed_inference_id = Column(String(36), ForeignKey('inferences.inference_id'))
    noise_type = Column(TEXT, nullable=False)
    confidence_delta = Column(FLOAT)
    class_changed = Column(Boolean)
    gradcam_overlap = Column(FLOAT)
    gradcam_correlation = Column(FLOAT)
    embedding_similarity = Column(FLOAT)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)


class BenchmarkRun(Base):
    __tablename__ = 'benchmark_runs'
    benchmark_id = Column(String(36), primary_key=True)
    experiment_id = Column(String(36), ForeignKey('experiments.experiment_id'))
    num_images = Column(INTEGER)
    num_variants = Column(INTEGER)
    total_persistence_ms = Column(INTEGER)
    avg_retrieval_ms = Column(FLOAT)
    total_storage_bytes = Column(INTEGER)
    metrics = Column(JSON)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)


class DatabaseClient:
    def __init__(self, dsn: str):
        self.engine = create_engine(dsn, future=True, pool_size=10, max_overflow=20)
        self.Session = sessionmaker(bind=self.engine, future=True)
        self._session = self.Session()

    def create_schema(self):
        Base.metadata.create_all(self.engine)

    def insert_record(self, record: Base, flush: bool = False):
        """Insere registro. Se flush=False, apenas adiciona ao batch."""
        self._session.add(record)
        if flush:
            self._session.commit()
            self._session.refresh(record)
        return record

    def flush(self):
        """Commita todos os registros pendentes de uma vez."""
        self._session.commit()

    def query(self, query):
        with self.Session() as session:
            return session.execute(query).all()

    def scalar(self, statement):
        with self.Session() as session:
            return session.scalars(statement).first()


class QdrantClient:
    def __init__(self, url: str, api_key: Optional[str] = None, collection_name: str = 'image_embeddings', batch_size: int = 100):
        client_args: dict[str, Any] = {'url': url, 'check_compatibility': False, 'timeout': 60}
        if api_key:
            client_args['api_key'] = api_key
        self.client = QdrantApiClient(**client_args)
        self.collection_name = collection_name
        self.batch_size = batch_size
        self._batch: list[rest.PointStruct] = []

        existing_collections = [c.name for c in self.client.get_collections().collections]
        if collection_name not in existing_collections:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=rest.VectorParams(size=EMBEDDING_DIMENSION, distance=rest.Distance.COSINE),
            )

    def insert_embedding(self, entry_id: str, vector: list[float], payload: Optional[dict] = None):
        point = rest.PointStruct(
            id=entry_id,
            vector=vector,
            payload=payload or {'inference_id': entry_id},
        )
        self._batch.append(point)
        if len(self._batch) >= self.batch_size:
            self.flush()

    def flush(self):
        """Envia todos os pontos acumulados de uma vez."""
        if self._batch:
            self.client.upsert(collection_name=self.collection_name, points=self._batch)
            self._batch = []

    def search(self, vector: list[float], top_k: int = 10):
        self.flush()  # Garante que todos os pontos foram enviados antes de buscar
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=top_k,
            with_payload=True,
        )
        return response.points
