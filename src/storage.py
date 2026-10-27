"""
Cliente para armazenamento de objetos no MinIO.

Este modulo fornece uma interface simplificada para upload e
download de imagens e arquivos no MinIO (S3-compatible).
"""

from io import BytesIO
from pathlib import Path

from minio import Minio
from PIL import Image


class MinIOClient:
    """Cliente para operacoes de armazenamento no MinIO.
    
    Fornece metodos para upload/download de imagens e arquivos
    com gerenciamento automatico de buckets.
    """
    
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ):
        """Inicializa cliente MinIO.
        
        Args:
            endpoint: URL do servidor MinIO
            access_key: chave de acesso
            secret_key: chave secreta
            bucket: nome do bucket
            secure: usar HTTPS
        """
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self.bucket = bucket
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

    def upload_image(self, image: Image.Image, object_name: str) -> str:
        """Faz upload de imagem PIL para o MinIO.
        
        Args:
            image: imagem PIL para upload
            object_name: caminho do objeto no bucket
        
        Returns:
            URI S3 do objeto (s3://bucket/object)
        """
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        self.client.put_object(
            self.bucket,
            object_name,
            buffer,
            length=buffer.getbuffer().nbytes,
            content_type='image/png',
        )
        return f"s3://{self.bucket}/{object_name}"

    def upload_file(self, local_path: Path, object_name: str) -> str:
        """Faz upload de arquivo local para o MinIO.
        
        Args:
            local_path: caminho do arquivo local
            object_name: caminho do objeto no bucket
        
        Returns:
            URI S3 do objeto
        """
        self.client.fput_object(
            self.bucket,
            object_name,
            str(local_path),
            content_type='image/png',
        )
        return f"s3://{self.bucket}/{object_name}"

    def download_object(self, object_name: str, output_path: Path) -> Path:
        """Faz download de objeto do MinIO.
        
        Args:
            object_name: caminho do objeto no bucket
            output_path: caminho local para salvar
        
        Returns:
            Caminho do arquivo baixado
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        response = self.client.get_object(self.bucket, object_name)
        try:
            with open(output_path, 'wb') as f:
                for chunk in response.stream(32*1024):
                    f.write(chunk)
        finally:
            response.close()
            response.release_conn()
        return output_path
