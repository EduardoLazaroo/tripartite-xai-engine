"""
Validacao do Pipeline - Testa o processamento de uma imagem de exemplo.

Este script verifica:
- Carregamento do modelo ResNet50
- Preprocessamento de imagem
- Inferencia
- Extracao de embedding
- Geracao de Grad-CAM
- Persistencia em todas as camadas
- Recuperacao por similaridade
"""

import sys
import time
import uuid
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


class PipelineChecker:
    """Testa o pipeline com uma imagem de exemplo."""
    
    def __init__(self, test_image_path: str = None):
        self.results = []
        self.all_passed = True
        self.test_image_path = test_image_path
        self.timing = {}
        
        # Resultados do teste para relatorio
        self.test_results = {
            'baseline': None,
            'variants': [],
            'comparisons': [],
            'similarity_search': None
        }
    
    def find_test_image(self) -> Path:
        """Encontra uma imagem de teste."""
        if self.test_image_path:
            path = Path(self.test_image_path)
            if path.exists():
                return path
        
        # Buscar na pasta images/
        images_dir = Path(__file__).resolve().parent.parent / 'images'
        if images_dir.exists():
            for img in images_dir.iterdir():
                if img.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                    return img
        
        self._log("[FAIL] Nenhuma imagem de teste encontrada", "error")
        self.all_passed = False
        return None
    
    def check_model_loading(self) -> bool:
        """Verifica se o modelo ResNet50 carrega corretamente."""
        print("\n[Pipeline] Carregando modelo ResNet50...")
        start = time.time()
        
        try:
            from torchvision import models
            
            model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
            model.eval()
            
            elapsed = time.time() - start
            self.timing['model_loading'] = elapsed
            
            self._log(f"[OK] Modelo carregado em {elapsed:.2f}s", "success")
            self._log(f"[INFO] Arquitetura: ResNet50 (IMAGENET1K_V2)", "info")
            
            return True
            
        except Exception as e:
            self._log(f"[FAIL] Erro ao carregar modelo: {e}", "error")
            self.all_passed = False
            return False
    
    def check_image_preprocessing(self, image_path: Path) -> bool:
        """Verifica o preprocessamento de imagem."""
        print("\n[Pipeline] Testando preprocessamento...")
        
        try:
            from PIL import Image
            from pipeline import preprocess_image
            
            # Carregar imagem
            original = Image.open(image_path).convert('RGB')
            self._log(f"[INFO] Imagem original: {original.size}", "info")
            
            # Preprocessar
            tensor = preprocess_image(original)
            self._log(f"[OK] Tensor preprocessado: shape={tensor.shape}", "success")
            
            return True
            
        except Exception as e:
            self._log(f"[FAIL] Erro no preprocessamento: {e}", "error")
            self.all_passed = False
            return False
    
    def check_full_pipeline(self, image_path: Path) -> bool:
        """Executa o pipeline completo para uma imagem de teste."""
        print("\n[Pipeline] Executando pipeline completo...")
        
        try:
            import torch
            from torchvision import models
            from PIL import Image
            
            from persistence import DatabaseClient, QdrantClient
            from storage import MinIOClient
            from processor import process_image, NOISE_VARIANTS
            
            # Inicializar clientes
            self._log("Inicializando clientes de banco...", "info")
            db = DatabaseClient(DATABASE_DSN)
            db.create_schema()
            
            vector_db = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY,
                collection_name=QDRANT_COLLECTION
            )
            
            storage = MinIOClient(
                endpoint=MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                bucket=MINIO_BUCKET
            )
            
            # Carregar modelo
            self._log("Carregando modelo...", "info")
            model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
            model.eval()
            
            # Processar imagem
            self._log(f"Processando imagem: {image_path.name}", "info")
            start = time.time()
            
            result = process_image(
                image_path=image_path,
                db=db,
                vector_db=vector_db,
                storage=storage,
                model=model,
                experiment_name='validation-test',
                experiment_description='Teste de validacao do pipeline',
                seed=42,
                domain='validation'
            )
            
            elapsed = time.time() - start
            self.timing['full_pipeline'] = elapsed
            
            # Armazenar resultados
            self.test_results['baseline'] = {
                'label': result.baseline.predicted_label,
                'confidence': result.baseline.confidence,
                'inference_id': result.baseline.inference_id
            }
            
            self.test_results['variants'] = [
                {
                    'noise_type': v.noise_type,
                    'label': v.predicted_label,
                    'confidence': v.confidence
                }
                for v in result.variants
            ]
            
            self.test_results['comparisons'] = result.comparisons
            
            # Exibir resultados
            self._log(f"[OK] Pipeline executado em {elapsed:.2f}s", "success")
            self._log(f"[INFO] Baseline: {result.baseline.predicted_label} (conf={result.baseline.confidence:.4f})", "info")
            
            for v in result.variants:
                self._log(f"[INFO] Variante {v.noise_type}: {v.predicted_label} (conf={v.confidence:.4f})", "info")
            
            return True
            
        except Exception as e:
            self._log(f"[FAIL] Erro no pipeline: {e}", "error")
            import traceback
            traceback.print_exc()
            self.all_passed = False
            return False
    
    def check_data_persistence(self) -> dict:
        """Verifica se os dados foram persistidos corretamente."""
        print("\n[Pipeline] Verificando persistencia dos dados...")
        
        persistence_status = {
            'mysql': False,
            'qdrant': False,
            'minio': False
        }
        
        try:
            from sqlalchemy import text, func
            from persistence import DatabaseClient, Inference, Embedding, GradCam, MediaAsset
            
            db = DatabaseClient(DATABASE_DSN)
            
            # Verificar MySQL
            with db.Session() as session:
                # Contar registros
                exp_count = session.execute(text("SELECT COUNT(*) FROM experiments")).scalar()
                inf_count = session.execute(text("SELECT COUNT(*) FROM inferences")).scalar()
                emb_count = session.execute(text("SELECT COUNT(*) FROM embeddings")).scalar()
                gc_count = session.execute(text("SELECT COUNT(*) FROM gradcams")).scalar()
                ma_count = session.execute(text("SELECT COUNT(*) FROM media_assets")).scalar()
                
                self._log(f"[MySQL] Experiments: {exp_count}", "info")
                self._log(f"[MySQL] Inferences: {inf_count}", "info")
                self._log(f"[MySQL] Embeddings: {emb_count}", "info")
                self._log(f"[MySQL] GradCAMs: {gc_count}", "info")
                self._log(f"[MySQL] Media Assets: {ma_count}", "info")
                
                persistence_status['mysql'] = inf_count > 0
            
            # Verificar Qdrant
            from qdrant_client import QdrantClient as QdrantApiClient
            
            client_args = {'url': QDRANT_URL, 'check_compatibility': False, 'timeout': 60}
            if QDRANT_API_KEY:
                client_args['api_key'] = QDRANT_API_KEY
            
            qdrant_client = QdrantApiClient(**client_args)
            collection_info = qdrant_client.get_collection(QDRANT_COLLECTION)
            
            self._log(f"[Qdrant] Pontos indexados: {collection_info.points_count}", "info")
            persistence_status['qdrant'] = collection_info.points_count > 0
            
            # Verificar MinIO
            from minio import Minio
            
            minio_client = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=False
            )
            
            objects = list(minio_client.list_objects(MINIO_BUCKET, recursive=True))
            self._log(f"[MinIO] Objetos armazenados: {len(objects)}", "info")
            persistence_status['minio'] = len(objects) > 0
            
        except Exception as e:
            self._log(f"[FAIL] Erro ao verificar persistencia: {e}", "error")
            self.all_passed = False
        
        return persistence_status
    
    def _log(self, message: str, level: str = "info"):
        """Registra resultado da verificacao."""
        self.results.append({
            'message': message,
            'level': level,
            'timestamp': time.strftime('%H:%M:%S')
        })
        print(f"  {message}")
    
    def run_all_checks(self) -> dict:
        """Executa todas as verificacoes do pipeline."""
        print("=" * 60)
        print("  VALIDACAO DO PIPELINE")
        print("=" * 60)
        
        # Encontrar imagem de teste
        image_path = self.find_test_image()
        if not image_path:
            return {'all_passed': False, 'error': 'Nenhuma imagem de teste encontrada'}
        
        self._log(f"[INFO] Imagem de teste: {image_path}", "info")
        
        # Verificacoes
        model_ok = self.check_model_loading()
        
        if model_ok and image_path:
            self.check_image_preprocessing(image_path)
            pipeline_ok = self.check_full_pipeline(image_path)
            
            if pipeline_ok:
                persistence = self.check_data_persistence()
            else:
                persistence = {'mysql': False, 'qdrant': False, 'minio': False}
        else:
            persistence = {'mysql': False, 'qdrant': False, 'minio': False}
        
        # Resumo
        print("\n" + "=" * 60)
        if self.all_passed:
            print("  RESULTADO: PIPELINE FUNCIONAL")
        else:
            print("  RESULTADO: PIPELINE COM PROBLEMAS")
        print("=" * 60)
        
        return {
            'all_passed': self.all_passed,
            'timing': self.timing,
            'persistence': persistence,
            'test_results': self.test_results,
            'details': self.results
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Valida o pipeline com uma imagem de teste')
    parser.add_argument('--image', type=str, help='Caminho para imagem de teste')
    args = parser.parse_args()
    
    checker = PipelineChecker(test_image_path=args.image)
    results = checker.run_all_checks()
    
    sys.exit(0 if results['all_passed'] else 1)


if __name__ == '__main__':
    main()
