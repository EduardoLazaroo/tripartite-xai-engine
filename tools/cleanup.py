import argparse
import shutil
import sys
from pathlib import Path

from sqlalchemy import text
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from config import DATABASE_DSN, EMBEDDING_DIMENSION, MINIO_ACCESS_KEY, MINIO_BUCKET, MINIO_ENDPOINT, MINIO_SECRET_KEY, QDRANT_API_KEY, QDRANT_COLLECTION, QDRANT_URL
from qdrant_client.http import models as rest
from persistence import DatabaseClient, QdrantClient
from storage import MinIOClient


def _force_remove_readonly(func, path, excinfo):
    """Forca remocao de arquivos somente-leitura no Windows."""
    import os
    import stat
    os.chmod(path, stat.S_IWRITE)
    func(path)


def clear_mysql(db: DatabaseClient, experiment_id: str = None):
    """Limpa MySQL. Se experiment_id fornecido, remove apenas registros do experimento."""
    with db.Session() as session:
        session.execute(text('SET FOREIGN_KEY_CHECKS = 0;'))
        
        if experiment_id:
            # Remove apenas registros do experimento específico
            tables_in_order = [
                'similarity_records',
                'gradcams',
                'embeddings',
                'perturbation_comparisons',
                'inferences',
                'media_assets',
                'noise_profiles',
                'images',
                'experiments',
                'audit_trail',
                'benchmark_runs',
            ]
            for table in tables_in_order:
                if table == 'experiments':
                    session.execute(text(f'DELETE FROM {table} WHERE experiment_id = :eid'), {'eid': experiment_id})
                elif table == 'benchmark_runs':
                    session.execute(text(f'DELETE FROM {table} WHERE experiment_id = :eid'), {'eid': experiment_id})
                elif table == 'audit_trail':
                    session.execute(text(f"DELETE FROM {table} WHERE entity_type = 'experiment' AND entity_id = :eid"), {'eid': experiment_id})
                elif table in ('gradcams', 'embeddings', 'perturbation_comparisons', 'similarity_records'):
                    # Tabelas com foreign key para inferences
                    session.execute(text(f'''
                        DELETE FROM {table} WHERE inference_id IN (
                            SELECT inference_id FROM inferences WHERE experiment_id = :eid
                        )
                    '''), {'eid': experiment_id})
                elif table == 'inferences':
                    session.execute(text(f'DELETE FROM {table} WHERE experiment_id = :eid'), {'eid': experiment_id})
                elif table == 'media_assets':
                    # Media assets referenciados por gradcams
                    session.execute(text(f'''
                        DELETE FROM {table} WHERE media_asset_id IN (
                            SELECT media_asset_id FROM gradcams WHERE inference_id IN (
                                SELECT inference_id FROM inferences WHERE experiment_id = :eid
                            )
                        )
                    '''), {'eid': experiment_id})
                elif table == 'noise_profiles':
                    session.execute(text(f'''
                        DELETE FROM {table} WHERE noise_id IN (
                            SELECT noise_id FROM inferences WHERE experiment_id = :eid AND noise_id IS NOT NULL
                        )
                    '''), {'eid': experiment_id})
                elif table == 'images':
                    session.execute(text(f'''
                        DELETE FROM {table} WHERE image_id IN (
                            SELECT image_id FROM inferences WHERE experiment_id = :eid
                        )
                    '''), {'eid': experiment_id})
            print(f'MySQL limpo para experimento {experiment_id}.')
        else:
            # Limpa tudo
            tables = [
                'similarity_records',
                'gradcams',
                'embeddings',
                'perturbation_comparisons',
                'inferences',
                'media_assets',
                'noise_profiles',
                'class_labels',
                'images',
                'experiments',
                'audit_trail',
                'benchmark_runs',
            ]
            for table in tables:
                session.execute(text(f'TRUNCATE TABLE {table};'))
            print('MySQL limpo completamente.')
        
        session.execute(text('SET FOREIGN_KEY_CHECKS = 1;'))
        session.commit()


def clear_qdrant(client: QdrantClient, experiment_id: str = None):
    """Limpa Qdrant. Se experiment_id fornecido, remove apenas pontos do experimento."""
    if experiment_id:
        # Remove pontos específicos do experimento usando scroll + delete
        points, _offset = client.client.scroll(
            collection_name=client.collection_name,
            scroll_filter=rest.Filter(
                must=[
                    rest.FieldCondition(
                        key='experiment_id',
                        match=rest.MatchValue(value=experiment_id),
                    )
                ]
            ),
            limit=1000,
            with_payload=False,
            with_vectors=False,
        )
        if points:
            ids = [p.id for p in points]
            client.client.delete(
                collection_name=client.collection_name,
                points_selector=rest.PointIdsList(points=ids),
            )
            print(f'Qdrant limpo para experimento {experiment_id}: {len(ids)} pontos removidos.')
        else:
            print(f'Qdrant: nenhum ponto encontrado para experimento {experiment_id}.')
    else:
        # Recria collection (limpa tudo)
        client.client.delete_collection(collection_name=client.collection_name)
        client.client.create_collection(
            collection_name=client.collection_name,
            vectors_config=rest.VectorParams(size=EMBEDDING_DIMENSION, distance=rest.Distance.COSINE),
        )
        print('Qdrant limpo completamente.')


def clear_minio(storage: MinIOClient, experiment_id: str = None):
    """Limpa MinIO. Se experiment_id fornecido, remove apenas objetos do experimento."""
    if experiment_id:
        # Remove apenas objetos com prefixo do experimento
        prefix = f'experiments/{experiment_id}/'
        objects = storage.client.list_objects(MINIO_BUCKET, prefix=prefix, recursive=True)
        count = 0
        for obj in objects:
            storage.client.remove_object(MINIO_BUCKET, obj.object_name)
            count += 1
        print(f'MinIO limpo para experimento {experiment_id}: {count} objetos removidos.')
    else:
        # Remove todos os objetos
        objects = storage.client.list_objects(MINIO_BUCKET, recursive=True)
        count = 0
        for obj in objects:
            storage.client.remove_object(MINIO_BUCKET, obj.object_name)
            count += 1
        print(f'MinIO limpo completamente: {count} objetos removidos.')


def clear_local_files():
    """Limpa arquivos gerados localmente (reports/, ui/assets/, ui/report_manifest.json)."""
    base = Path(__file__).resolve().parent.parent
    removed = []
    
    # reports/
    reports_dir = base / 'reports'
    if reports_dir.exists():
        shutil.rmtree(reports_dir, onerror=_force_remove_readonly)
        reports_dir.mkdir(parents=True, exist_ok=True)
        removed.append('reports/')
    
    # ui/assets/
    ui_assets = base / 'ui' / 'assets'
    if ui_assets.exists():
        shutil.rmtree(ui_assets, onerror=_force_remove_readonly)
        removed.append('ui/assets/')
    
    # ui/report_manifest.json
    ui_manifest = base / 'ui' / 'report_manifest.json'
    if ui_manifest.exists():
        ui_manifest.unlink()
        removed.append('ui/report_manifest.json')
    
    if removed:
        print(f'Arquivos locais removidos: {", ".join(removed)}')
    else:
        print('Nenhum arquivo local para remover.')


def main():
    parser = argparse.ArgumentParser(
        description='Limpa ambientes de banco de dados e armazenamento para experimentos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Exemplos:
  # Limpar tudo (bancos + arquivos locais)
  python tools/cleanup.py --all
  
  # Limpar apenas MySQL
  python tools/cleanup.py --mysql
  
  # Limpar dados de um experimento específico
  python tools/cleanup.py --all --experiment-id <UUID>
  
  # Limpar apenas MinIO de um experimento
  python tools/cleanup.py --minio --experiment-id <UUID>

  # Limpar apenas arquivos locais (reports, ui)
  python tools/cleanup.py --files
        '''
    )
    parser.add_argument('--mysql', action='store_true', help='Limpar banco relacional MySQL')
    parser.add_argument('--qdrant', action='store_true', help='Limpar banco vetorial Qdrant')
    parser.add_argument('--minio', action='store_true', help='Limpar armazenamento MinIO')
    parser.add_argument('--files', action='store_true', help='Limpar arquivos locais (reports/, ui/assets/, ui/report_manifest.json)')
    parser.add_argument('--all', action='store_true', help='Limpar todos: MySQL, Qdrant, MinIO e arquivos locais')
    parser.add_argument('--experiment-id', type=str, help='ID do experimento para limpeza seletiva')
    args = parser.parse_args()

    if not (args.mysql or args.qdrant or args.minio or args.files or args.all):
        parser.print_help()
        sys.exit(1)

    db = DatabaseClient(DATABASE_DSN)
    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, collection_name=QDRANT_COLLECTION)
    storage = MinIOClient(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        bucket=MINIO_BUCKET,
    )

    experiment_id = args.experiment_id

    if args.mysql or args.all:
        clear_mysql(db, experiment_id)
    if args.qdrant or args.all:
        clear_qdrant(qdrant, experiment_id)
    if args.minio or args.all:
        clear_minio(storage, experiment_id)
    if args.files or args.all:
        clear_local_files()


if __name__ == '__main__':
    main()
