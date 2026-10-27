import sys
from datetime import datetime


class PipelineLogger:
    """Logger enxuto para acompanhamento da execucao da pipeline.
    
    Mostra apenas:
    - Nome da etapa
    - Progresso resumido (a cada 10%)
    - Resultado final de cada imagem
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self._start_time = None
        self._step_stack: list[tuple[str, datetime]] = []

    def start(self, message: str):
        self._start_time = datetime.now()
        self._step_stack = []
        self._print(f"[INICIO] {message}")

    def step(self, message: str):
        now = datetime.now()
        self._step_stack.append((message, now))
        depth = len(self._step_stack)
        indent = "  " * min(depth - 1, 3)
        self._print(f"{indent}[ETAPA] {message}")

    def substep(self, message: str):
        pass

    def progress(self, current: int, total: int, message: str = ""):
        pct = (current / total) * 100 if total > 0 else 0
        depth = len(self._step_stack)
        indent = "  " * min(depth, 3)
        self._print(f"{indent}[{pct:3.0f}%] {current}/{total} {message}")

    def info(self, message: str):
        pass

    def image_done(self, filename: str, label: str, confidence: float, time_ms: float):
        """Exibe resultado final de uma imagem processada."""
        depth = len(self._step_stack)
        indent = "  " * min(depth, 3)
        self._print(f"{indent}[OK] {filename} -> {label} ({confidence:.2f}, {time_ms:.0f}ms)")

    def variant_done(self, idx: int, total: int, noise_type: str):
        """Exibe progresso de variante (apenas a cada 25%)."""
        pass

    def comparing(self, label: str, confidence: float):
        """Exibe info de comparacao (nao exibido)."""
        pass

    def retrieval(self, similar: int, contextual: int):
        """Exibe info de recuperacao (nao exibido)."""
        pass

    def warn(self, message: str):
        depth = len(self._step_stack)
        indent = "  " * min(depth, 3)
        self._print(f"{indent}[AVISO] {message}")

    def error(self, message: str):
        depth = len(self._step_stack)
        indent = "  " * min(depth, 3)
        self._print(f"{indent}[ERRO] {message}", file=sys.stderr)

    def done(self, message: str):
        elapsed = ""
        if self._start_time:
            delta = datetime.now() - self._start_time
            elapsed = f" ({delta.total_seconds():.0f}s)"
        if self._step_stack:
            self._step_stack.pop()
        self._print(f"[CONCLUIDO] {message}{elapsed}")

    def section(self, title: str):
        pass

    def _print(self, message: str, file=None):
        if self.verbose:
            print(message, file=file or sys.stdout)


log = PipelineLogger()
