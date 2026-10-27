"""
Busca por similaridade e recuperacao contextual no Qdrant.

Este modulo fornece funcoes para buscar embeddings similares
no banco vetorial Qdrant, com suporte a filtros contextuais.
"""

import time
from typing import List, Optional

from qdrant_client.http import models as rest

from config import QDRANT_API_KEY, QDRANT_COLLECTION, QDRANT_URL
from persistence import QdrantClient


def _build_filter(filter_metadata: dict) -> Optional[rest.Filter]:
    """Constroi filtro Qdrant a partir de dicionario de metadados.
    
    Args:
        filter_metadata: dicionario campo-valor para filtrar
    
    Returns:
        Filtro Qdrant ou None se vazio
    """
    if not filter_metadata:
        return None
    conditions = []
    for key, value in filter_metadata.items():
        if value is None:
            continue
        conditions.append(
            rest.FieldCondition(key=key, match=rest.MatchValue(value=value))
        )
    if not conditions:
        return None
    return rest.Filter(must=conditions)


def search_similar_embeddings(
    query_vector: List[float],
    top_k: int = 10,
    collection_name: Optional[str] = None,
    qdrant_url: Optional[str] = None,
    filter_metadata: Optional[dict] = None,
):
    """Busca embeddings similares no Qdrant.
    
    Args:
        query_vector: vetor de consulta
        top_k: numero de resultados
        collection_name: nome da colecao (opcional)
        qdrant_url: URL do Qdrant (opcional)
        filter_metadata: filtros contextuais (opcional)
    
    Returns:
        Lista de dicionarios com id, score, rank, payload e tempo
    """
    client = QdrantClient(
        url=qdrant_url or QDRANT_URL,
        api_key=QDRANT_API_KEY,
        collection_name=collection_name or QDRANT_COLLECTION,
    )
    start = time.time()
    qdrant_filter = _build_filter(filter_metadata or {})
    response = client.client.query_points(
        collection_name=client.collection_name,
        query=query_vector,
        limit=top_k,
        with_payload=True,
        query_filter=qdrant_filter,
    )
    retrieval_time_ms = int((time.time() - start) * 1000)

    hits = []
    for rank, point in enumerate(response.points, start=1):
        hits.append({
            'id': str(point.id),
            'score': float(point.score),
            'rank': rank,
            'payload': point.payload or {},
            'retrieval_time_ms': retrieval_time_ms,
        })
    return hits


def contextual_retrieval(
    query_vector: List[float],
    filter_metadata: dict,
    top_k: int = 10,
    collection_name: Optional[str] = None,
    qdrant_url: Optional[str] = None,
):
    results = search_similar_embeddings(
        query_vector=query_vector,
        top_k=top_k,
        collection_name=collection_name,
        qdrant_url=qdrant_url,
        filter_metadata=filter_metadata,
    )
    return {
        'top_k': top_k,
        'filter': filter_metadata,
        'results': results,
    }


def explain_similarity(hit: dict, baseline: dict) -> str:
    reasons = []
    if hit.get('predicted_label') == baseline.get('predicted_label'):
        reasons.append('mesma classe predita')
    score = hit.get('score', 0)
    if score > 0.95:
        reasons.append('embedding muito similar — mesmo padrão visual')
    elif score > 0.85:
        reasons.append('embedding similar — variação da mesma classe')
    elif score > 0.7:
        reasons.append('embedding moderadamente similar')
    if hit.get('noise_type') == baseline.get('noise_type'):
        reasons.append('mesma condição de captura')
    if not reasons:
        reasons.append(f'similaridade cosseno = {score:.3f}')
    return 'Similaridade porque: ' + '; '.join(reasons)
