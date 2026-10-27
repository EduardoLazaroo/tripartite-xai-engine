"""
Modulo de reprodutibilidade e metadados de experimentos.

Este modulo fornece funcionalidades para capturar e armazenar
informacoes sobre o ambiente de execucao, garantindo a
reprodutibilidade dos experimentos.

Informacoes capturadas:
    - Versao do git (commit e branch)
    - Versoes das dependencias
    - Informacoes do sistema operacional
    - Parametros do experimento
    - Resultados obtidos
"""

import json
import platform
import subprocess
import sys
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def get_git_commit() -> Optional[str]:
    """Obtem o hash do commit atual do git.
    
    Returns:
        Hash curto do commit ou None se nao disponivel
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True,
            cwd=Path(__file__).resolve().parent.parent, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def get_git_branch() -> Optional[str]:
    """Obtem o nome da branch atual do git.
    
    Returns:
        Nome da branch ou None se nao disponivel
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True,
            cwd=Path(__file__).resolve().parent.parent, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def get_dependencies_versions() -> dict:
    """Coleta as versoes de todas as dependencias instaladas.
    
    Returns:
        Dicionario com nome do pacote e versao instalada
    """
    versions = {"python": platform.python_version()}
    packages = [
        "torch", "torchvision", "numpy", "PIL",
        "sqlalchemy", "pymysql", "qdrant_client", "minio",
        "matplotlib", "seaborn",
    ]
    for pkg in packages:
        try:
            if pkg == "PIL":
                import PIL
                versions["pillow"] = PIL.__version__
            else:
                mod = __import__(pkg)
                versions[pkg] = getattr(mod, "__version__", "unknown")
        except ImportError:
            versions[pkg] = "not installed"
    return versions


@dataclass
class ExperimentMetadata:
    """Metadados completos de um experimento.
    
    Armazena todas as informacoes necessarias para reproduzir
    um experimento, incluindo parametros, ambiente e resultados.
    """
    experiment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    experiment_name: str = "unnamed-experiment"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    timezone: str = "UTC"
    seed: int = 42
    git_commit: Optional[str] = field(default_factory=get_git_commit)
    git_branch: Optional[str] = field(default_factory=get_git_branch)
    hostname: str = field(default_factory=platform.node)
    os: str = field(default_factory=platform.system)
    os_version: str = field(default_factory=platform.version)
    architecture: str = field(default_factory=platform.machine)
    dataset_name: str = "custom"
    dataset_path: str = ""
    num_images: int = 0
    num_classes: int = 0
    image_size: tuple = (224, 224)
    model_name: str = "resnet50"
    model_weights: str = "IMAGENET1K_V2"
    noise_types: list = field(default_factory=list)
    noise_intensities: dict = field(default_factory=dict)
    num_variants: int = 7
    dependencies: dict = field(default_factory=get_dependencies_versions)
    command: str = ""
    args: dict = field(default_factory=dict)
    results: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["image_size"] = list(d["image_size"])
        return d

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    @classmethod
    def load(cls, path: str | Path) -> "ExperimentMetadata":
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        if "image_size" in data and isinstance(data["image_size"], list):
            data["image_size"] = tuple(data["image_size"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def get_metadata(
    experiment_name: str = "benchmark-run",
    seed: int = 42,
    dataset_path: str = "",
    num_images: int = 0,
    num_classes: int = 0,
    noise_types: Optional[list] = None,
    noise_intensities: Optional[dict] = None,
    args: Optional[dict] = None,
) -> ExperimentMetadata:
    """Cria e retorna metadados do experimento com valores padrao.
    
    Args:
        experiment_name: nome do experimento
        seed: semente para reprodutibilidade
        dataset_path: caminho do dataset
        num_images: numero de imagens no dataset
        num_classes: numero de classes
        noise_types: lista de tipos de ruido
        noise_intensities: dicionario de intensidades por tipo
        args: argumentos adicionais
    
    Returns:
        Objeto ExperimentMetadata preenchido
    """
    return ExperimentMetadata(
        experiment_name=experiment_name,
        seed=seed,
        dataset_path=dataset_path,
        num_images=num_images,
        num_classes=num_classes,
        noise_types=noise_types or [
            "none", "gaussian", "salt_pepper",
            "speckle", "blur", "brightness", "contrast",
        ],
        noise_intensities=noise_intensities or {
            "gaussian": 0.08, "salt_pepper": 0.04,
            "speckle": 0.08, "blur": 2.0,
            "brightness": 0.2, "contrast": 0.25,
        },
        command=" ".join(sys.argv),
        args=args or {},
    )
