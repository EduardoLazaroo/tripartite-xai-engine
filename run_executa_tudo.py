"""
Script unico para executar o pipeline completo de evidencias explicativas.

Uso:
    python run_executa_tudo.py                    # Executa tudo
    python run_executa_tudo.py --skip-cleanup     # Pula limpeza inicial
    python run_executa_tudo.py --skip-docker      # Se Docker ja esta rodando
    python run_executa_tudo.py --input images/ --output reports/
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


def run_silent(command: str, description: str = "") -> bool:
    """Executa comando e captura output (etapas rapidas)."""
    if description:
        print(f"\n{'='*60}")
        print(f"  {description}")
        print(f"{'='*60}")

    result = subprocess.run(
        command, shell=True,
        capture_output=True, text=True
    )
    
    if result.returncode != 0:
        full_output = (result.stdout or "") + (result.stderr or "")
        lines = full_output.strip().split('\n')
        last_lines = '\n'.join(lines[-15:])
        print(f"[ERRO] Comando falhou (codigo {result.returncode})")
        print(f"Ultimas linhas:\n{last_lines}")
        return False
    
    return True


def run_live(command: str, description: str = "") -> bool:
    """Executa comando e mostra output em tempo real (processos longos)."""
    if description:
        print(f"\n{'='*60}")
        print(f"  {description}")
        print(f"{'='*60}")
        print(f"[EXECUTANDO] {command}\n")
    
    result = subprocess.run(command, shell=True)
    
    if result.returncode != 0:
        print(f"\n[ERRO] Comando falhou (codigo {result.returncode})")
        return False
    
    return True


def check_docker_running() -> bool:
    """Verifica se os containers Docker estao rodando."""
    result = subprocess.run(
        "docker compose ps --format json",
        shell=True, capture_output=True, text=True
    )
    return result.returncode == 0 and len(result.stdout.strip()) > 0


def wait_for_services(timeout: int = 60) -> bool:
    """Aguarda servicos ficarem disponiveis."""
    print("\n  Aguardando servicos...", end="", flush=True)
    
    start = time.time()
    while time.time() - start < timeout:
        try:
            import urllib.request
            import socket
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            mysql_ok = sock.connect_ex(('127.0.0.1', 3307)) == 0
            sock.close()
            
            req = urllib.request.urlopen("http://127.0.0.1:6333/health", timeout=2)
            qdrant_ok = req.status == 200
            
            req = urllib.request.urlopen("http://127.0.0.1:9000/minio/health/live", timeout=2)
            minio_ok = req.status == 200
            
            if mysql_ok and qdrant_ok and minio_ok:
                print(" OK")
                return True
        except Exception:
            pass
        
        time.sleep(2)
        print(".", end="", flush=True)
    
    print(" ERRO (timeout)")
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline completo de evidencias explicativas"
    )
    parser.add_argument("--input", type=str, default="images/", help="Diretorio de imagens")
    parser.add_argument("--output", type=str, default="reports/", help="Diretorio de saida")
    parser.add_argument("--skip-cleanup", action="store_true", help="Pula limpeza inicial")
    parser.add_argument("--skip-docker", action="store_true", help="Pula inicializacao do Docker")
    parser.add_argument("--skip-benchmark", action="store_true", help="Pula execucao do benchmark")
    parser.add_argument("--skip-visualization", action="store_true", help="Pula geracao de visualizacoes")
    parser.add_argument("--skip-export", action="store_true", help="Pula exportacao para interface web")
    parser.add_argument("--local", action="store_true", help="Executa benchmark no Python local em vez do Docker")
    parser.add_argument("--skip-article", action="store_true", help="Pula compilacao do artigo em PDF")
    args = parser.parse_args()
    
    print("""
    +============================================================+
    |     PIPELINE DE EVIDENCIAS EXPLICATIVAS - v2.0           |
    |     Arquitetura Tripartite (XAI Engine + Paper)           |
    +============================================================+
    """)
    
    start_time = time.time()
    errors = []
    
    # ETAPA 0: Limpar dados anteriores
    if not args.skip_cleanup:
        if not run_silent("python tools/cleanup.py --all", "ETAPA 0: Limpando dados de execucoes anteriores"):
            errors.append("cleanup")
    else:
        print("\n  [INFO] --skip-cleanup: pulando limpeza inicial")
    
    # ETAPA 1: Inicializar infraestrutura
    if not args.skip_docker:
        if not check_docker_running():
            if not run_silent("docker compose up -d", "ETAPA 1: Inicializando infraestrutura"):
                sys.exit(1)
            if not wait_for_services():
                sys.exit(1)
        else:
            print("\n  [INFO] Docker ja esta rodando, pulando inicializacao")
    else:
        print("\n  [INFO] --skip-docker: pulando inicializacao do Docker")
    
    # ETAPA 2: Executar benchmark (MOSTRA OUTPUT EM TEMPO REAL)
    if not args.skip_benchmark:
        if args.local:
            bench_cmd = f"python src/benchmark.py --input {args.input} --output {args.output}"
        else:
            bench_cmd = f"docker compose run --rm pipeline python src/benchmark.py --input {args.input} --output {args.output}"
        
        if not run_live(bench_cmd, "ETAPA 2: Executando benchmark de explicabilidade"):
            errors.append("benchmark")
    else:
        print("\n  [INFO] --skip-benchmark: pulando benchmark")
    
    # ETAPA 3: Gerar visualizacoes
    if not args.skip_visualization:
        output_dir = Path(args.output)
        benchmark_files = list(output_dir.glob("benchmark_*.json"))
        
        if benchmark_files:
            latest_benchmark = max(benchmark_files, key=lambda p: p.stat().st_mtime)
            figures_dir = output_dir / "figures"
            
            if not run_silent(
                f"python tools/visualization.py --report {latest_benchmark} --output {figures_dir}",
                "ETAPA 3: Gerando visualizacoes (graficos analiticos)"
            ):
                errors.append("visualizacao")
        else:
            print("\n  [AVISO] Nenhum arquivo de benchmark encontrado, pulando visualizacoes")
    else:
        print("\n  [INFO] --skip-visualization: pulando visualizacoes")
    
    # ETAPA 4: Compilar artigo cientifico em PDF
    if not args.skip_article:
        if not run_silent("python gerar_artigo_pdf.py", "ETAPA 4: Compilando Artigo Academico em PDF (ABNT)"):
            errors.append("artigo_pdf")
    else:
        print("\n  [INFO] --skip-article: pulando compilacao do PDF")
    
    
    # RESUMO FINAL
    elapsed = time.time() - start_time
    
    print(f"""
    +============================================================+
    |                  PIPELINE CONCLUIDO                        |
    +------------------------------------------------------------+
    |  Tempo total: {elapsed:.1f}s
    |
    |  Resultados:
    |    - Relatorios: {args.output}
    |    - Figuras: {args.output}/figures/
    +============================================================+
    """)
    
    if errors:
        print(f"  [AVISO] Etapas com erro: {', '.join(errors)}")
    else:
        print("  [OK] Todas as etapas concluidas com sucesso!")


if __name__ == "__main__":
    main()
