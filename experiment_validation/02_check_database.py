"""
Validacao do Banco de Dados - Verifica MySQL, Qdrant e MinIO.

Este script verifica:
- Conexao com MySQL
- Schema das tabelas
- Conexao com Qdrant
- Colecao vetorial
- Conexao com MinIO
- Bucket de armazenamento
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from config import (
    DATABASE_DSN,
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_BUCKET,
)


class DatabaseChecker:
    """Verifica os bancos de dados e armazenamento."""
    
    def __init__(self):
        self.results = []
        self.all_passed = True
    
    def check_mysql_connection(self) -> bool:
        """Verifica conexao com MySQL."""
        print("[MySQL] Testando conexao...")
        try:
            from sqlalchemy import create_engine, text
            
            engine = create_engine(DATABASE_DSN, future=True)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                row = result.fetchone()
                
                if row and row[0] == 1:
                    self._log("[OK] Conexao com MySQL estabelecida", "success")
                    
                    # Verificar database
                    result = conn.execute(text("SELECT DATABASE()"))
                    db_name = result.fetchone()[0]
                    self._log(f"[INFO] Database ativo: {db_name}", "info")
                    
                    return True
                else:
                    self._log("[FAIL] Resposta inesperada do MySQL", "error")
                    self.all_passed = False
                    return False
                    
        except Exception as e:
            self._log(f"[FAIL] Erro ao conectar MySQL: {e}", "error")
            self.all_passed = False
            return False
    
    def check_mysql_tables(self) -> dict:
        """Verifica se as tabelas necessarias existem."""
        print("\n[MySQL] Verificando schema das tabelas...")
        
        required_tables = [
            'experiments',
            'images',
            'noise_profiles',
            'class_labels',
            'media_assets',
            'inferences',
            'embeddings',
            'gradcams',
            'similarity_records',
            'audit_trail',
            'perturbation_comparisons',
            'benchmark_runs'
        ]
        
        table_status = {}
        
        try:
            from sqlalchemy import create_engine, text, inspect
            
            engine = create_engine(DATABASE_DSN, future=True)
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            
            for table in required_tables:
                if table in existing_tables:
                    table_status[table] = True
                    self._log(f"[OK] Tabela '{table}' existe", "success")
                else:
                    table_status[table] = False
                    self._log(f"[FAIL] Tabela '{table}' NAO existe", "error")
                    self.all_passed = False
                    
        except Exception as e:
            self._log(f"[FAIL] Erro ao verificar tabelas: {e}", "error")
            self.all_passed = False
        
        return table_status
    
    def check_qdrant_connection(self) -> bool:
        """Verifica conexao com Qdrant."""
        print("\n[Qdrant] Testando conexao...")
        try:
            from qdrant_client import QdrantClient as QdrantApiClient
            
            client_args = {'url': QDRANT_URL, 'check_compatibility': False}
            if QDRANT_API_KEY:
                client_args['api_key'] = QDRANT_API_KEY
            
            client = QdrantApiClient(**client_args)
            collections = client.get_collections()
            
            self._log(f"[OK] Conexao com Qdrant estabelecida", "success")
            self._log(f"[INFO] Colecoes existentes: {[c.name for c in collections.collections]}", "info")
            
            return True
            
        except Exception as e:
            self._log(f"[FAIL] Erro ao conectar Qdrant: {e}", "error")
            self.all_passed = False
            return False
    
    def check_qdrant_collection(self) -> bool:
        """Verifica se a colecao vetorial existe e esta configurada corretamente."""
        print("\n[Qdrant] Verificando colecao vetorial...")
        try:
            from qdrant_client import QdrantClient as QdrantApiClient
            
            client_args = {'url': QDRANT_URL, 'check_compatibility': False}
            if QDRANT_API_KEY:
                client_args['api_key'] = QDRANT_API_KEY
            
            client = QdrantApiClient(**client_args)
            
            # Verificar se colecao existe
            collections = [c.name for c in client.get_collections().collections]
            
            if QDRANT_COLLECTION in collections:
                # Obter info da colecao
                collection_info = client.get_collection(QDRANT_COLLECTION)
                
                self._log(f"[OK] Colecao '{QDRANT_COLLECTION}' existe", "success")
                self._log(f"[INFO] Dimensao dos vetores: {collection_info.config.params.vectors.size}", "info")
                self._log(f"[INFO] Distancia: {collection_info.config.params.vectors.distance}", "info")
                self._log(f"[INFO] Pontos indexados: {collection_info.points_count}", "info")
                
                return True
            else:
                self._log(f"[WARN] Colecao '{QDRANT_COLLECTION}' NAO existe (sera criada automaticamente)", "warning")
                return True  # Nao e fatal, sera criada
                
        except Exception as e:
            self._log(f"[FAIL] Erro ao verificar colecao: {e}", "error")
            self.all_passed = False
            return False
    
    def check_minio_connection(self) -> bool:
        """Verifica conexao com MinIO."""
        print("\n[MinIO] Testando conexao...")
        try:
            from minio import Minio
            
            client = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=False
            )
            
            # Testar listando buckets
            buckets = client.list_buckets()
            bucket_names = [b.name for b in buckets]
            
            self._log(f"[OK] Conexao com MinIO estabelecida", "success")
            self._log(f"[INFO] Buckets existentes: {bucket_names}", "info")
            
            return True
            
        except Exception as e:
            self._log(f"[FAIL] Erro ao conectar MinIO: {e}", "error")
            self.all_passed = False
            return False
    
    def check_minio_bucket(self) -> bool:
        """Verifica se o bucket necessario existe."""
        print("\n[MinIO] Verificando bucket...")
        try:
            from minio import Minio
            
            client = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=False
            )
            
            if client.bucket_exists(MINIO_BUCKET):
                self._log(f"[OK] Bucket '{MINIO_BUCKET}' existe", "success")
                
                # Contar objetos
                objects = list(client.list_objects(MINIO_BUCKET, recursive=True))
                self._log(f"[INFO] Objetos no bucket: {len(objects)}", "info")
                
                return True
            else:
                self._log(f"[WARN] Bucket '{MINIO_BUCKET}' NAO existe (sera criado automaticamente)", "warning")
                return True  # Nao e fatal, sera criado
                
        except Exception as e:
            self._log(f"[FAIL] Erro ao verificar bucket: {e}", "error")
            self.all_passed = False
            return False
    
    def _log(self, message: str, level: str = "info"):
        """Registra resultado da verificacao."""
        self.results.append({
            'message': message,
            'level': level,
            'timestamp': time.strftime('%H:%M:%S')
        })
        print(f"  {message}")
    
    def run_all_checks(self) -> dict:
        """Executa todas as verificacoes de banco de dados."""
        print("=" * 60)
        print("  VALIDACAO DOS BANCOS DE DADOS")
        print("=" * 60)
        print()
        
        # MySQL
        print("-" * 40)
        print("MYSQL (Banco Relacional)")
        print("-" * 40)
        mysql_conn = self.check_mysql_connection()
        if mysql_conn:
            self.check_mysql_tables()
        print()
        
        # Qdrant
        print("-" * 40)
        print("QDRANT (Banco Vetorial)")
        print("-" * 40)
        qdrant_conn = self.check_qdrant_connection()
        if qdrant_conn:
            self.check_qdrant_collection()
        print()
        
        # MinIO
        print("-" * 40)
        print("MINIO (Armazenamento de Objetos)")
        print("-" * 40)
        minio_conn = self.check_minio_connection()
        if minio_conn:
            self.check_minio_bucket()
        print()
        
        # Resumo
        print("=" * 60)
        if self.all_passed:
            print("  RESULTADO: TODAS AS VERIFICACOES PASSARAM")
        else:
            print("  RESULTADO: ALGUMAS VERIFICACOES FALHARAM")
        print("=" * 60)
        
        return {
            'mysql_connection': mysql_conn,
            'qdrant_connection': qdrant_conn,
            'minio_connection': minio_conn,
            'all_passed': self.all_passed,
            'details': self.results
        }


def main():
    checker = DatabaseChecker()
    results = checker.run_all_checks()
    
    sys.exit(0 if results['all_passed'] else 1)


if __name__ == '__main__':
    main()
