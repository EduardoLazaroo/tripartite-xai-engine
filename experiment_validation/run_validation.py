"""
Script Principal de Validacao do Experimento.

Executa todas as verificacoes antes de rodar o experimento completo:
1. Infraestrutura (Docker, portas)
2. Bancos de dados (MySQL, Qdrant, MinIO)
3. Pipeline (processamento de imagem de teste)
4. Geracao de relatorio

Uso:
    python experiment_validation/run_validation.py              # Validacao completa
    python experiment_validation/run_validation.py --skip-pipeline  # Pula teste do pipeline
    python experiment_validation/run_validation.py --infra-only     # So infraestrutura
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))


class ValidationRunner:
    """Orquestra todas as validacoes."""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    def run_check(self, script_name: str, description: str) -> bool:
        """Executa um script de validacao."""
        print("\n" + "=" * 70)
        print(f"  {description}")
        print("=" * 70)
        
        script_path = Path(__file__).parent / script_name
        
        if not script_path.exists():
            print(f"[ERRO] Script nao encontrado: {script_path}")
            return False
        
        start = time.time()
        if script_name == '03_check_pipeline.py':
            try:
                import torch
                import torchvision
                cmd = [sys.executable, str(script_path)]
            except ImportError:
                cmd = ["docker", "compose", "run", "--rm", "pipeline", "python", f"experiment_validation/{script_name}"]
        else:
            cmd = [sys.executable, str(script_path)]

        result = subprocess.run(
            cmd,
            cwd=str(Path(__file__).resolve().parent.parent)
        )
        elapsed = time.time() - start
        
        passed = result.returncode == 0
        self.results[description] = {
            'passed': passed,
            'elapsed': elapsed,
            'script': script_name
        }
        
        status = "PASSOU" if passed else "FALHOU"
        print(f"\n  Resultado: {status} ({elapsed:.1f}s)")
        
        return passed
    
    def run_infrastructure_check(self) -> bool:
        """Executa validacao da infraestrutura."""
        return self.run_check(
            '01_check_infrastructure.py',
            '1/4 - INFRAESTRUTURA'
        )
    
    def run_database_check(self) -> bool:
        """Executa validacao dos bancos de dados."""
        return self.run_check(
            '02_check_database.py',
            '2/4 - BANCOS DE DADOS'
        )
    
    def run_pipeline_check(self) -> bool:
        """Executa validacao do pipeline."""
        return self.run_check(
            '03_check_pipeline.py',
            '3/4 - PIPELINE'
        )
    
    def generate_report(self) -> bool:
        """Gera relatorio final."""
        print("\n" + "=" * 70)
        print("  4/4 - GERANDO RELATORIO")
        print("=" * 70)
        
        try:
            # Import direto para evitar problema com nome de arquivo comecando com numero
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "report_generator",
                str(Path(__file__).parent / "04_generate_report.py")
            )
            report_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(report_module)
            ReportGenerator = report_module.ReportGenerator
            
            generator = ReportGenerator()
            
            # Adicionar resultados
            for check_name, result in self.results.items():
                generator.add_check_result(check_name, {
                    'all_passed': result['passed'],
                    'elapsed': result['elapsed'],
                    'details': []
                })
            
            paths = generator.save_reports()
            
            print(f"\n[OK] Relatorios gerados:")
            for fmt, path in paths.items():
                print(f"  - {fmt}: {path}")
            
            return True
            
        except Exception as e:
            print(f"[ERRO] Falha ao gerar relatorio: {e}")
            return False
    
    def print_summary(self):
        """Exibe resumo final."""
        self.end_time = time.time()
        total_time = self.end_time - self.start_time
        
        print("\n" + "=" * 70)
        print("  RESUMO DA VALIDACAO")
        print("=" * 70)
        print()
        
        all_passed = True
        for check_name, result in self.results.items():
            status = "[PASSOU]" if result['passed'] else "[FALHOU]"
            print(f"  {status} {check_name} ({result['elapsed']:.1f}s)")
            
            if not result['passed']:
                all_passed = False
        
        print()
        print(f"  Tempo total: {total_time:.1f}s")
        print()
        
        if all_passed:
            print("  " + "=" * 66)
            print("  TODAS AS VERIFICACOES PASSARAM!")
            print("  Voce pode rodar o experimento com seguranca:")
            print("  python run_executa_tudo.py")
            print("  " + "=" * 66)
        else:
            print("  " + "=" * 66)
            print("  ALGUMAS VERIFICACOES FALHARAM!")
            print("  Corrija os problemas antes de rodar o experimento.")
            print("  " + "=" * 66)
        
        print()
        
        return all_passed
    
    def run_all(self, skip_pipeline: bool = False, infra_only: bool = False):
        """Executa todas as validacoes."""
        self.start_time = time.time()
        
        print("\n" + "#" * 70)
        print("#" + " " * 68 + "#")
        print("#   VALIDACAO DO EXPERIMENTO DE EVIDENCIAS EXPLICATIVAS" + " " * 14 + "#")
        print("#" + " " * 68 + "#")
        print("#" * 70)
        print()
        print(f"  Inicio: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. Infraestrutura
        infra_ok = self.run_infrastructure_check()
        if not infra_ok:
            print("\n[ABORTADO] Problemas na infraestrutura.")
            self.print_summary()
            return False
        
        if infra_only:
            self.print_summary()
            return True
        
        # 2. Bancos de dados
        db_ok = self.run_database_check()
        if not db_ok:
            print("\n[ABORTADO] Problemas nos bancos de dados.")
            self.print_summary()
            return False
        
        # 3. Pipeline (opcional)
        if not skip_pipeline:
            pipeline_ok = self.run_pipeline_check()
            if not pipeline_ok:
                print("\n[ABORTADO] Problemas no pipeline.")
                self.print_summary()
                return False
        else:
            print("\n[INFO] Pipeline check (--skip-pipeline)")
        
        # 4. Relatorio
        self.generate_report()
        
        # Resumo
        return self.print_summary()


def main():
    parser = argparse.ArgumentParser(
        description='Validacao completa antes do experimento'
    )
    parser.add_argument(
        '--skip-pipeline',
        action='store_true',
        help='Pula a validacao do pipeline (mais rapido)'
    )
    parser.add_argument(
        '--infra-only',
        action='store_true',
        help='Executa apenas validacao da infraestrutura'
    )
    
    args = parser.parse_args()
    
    runner = ValidationRunner()
    success = runner.run_all(
        skip_pipeline=args.skip_pipeline,
        infra_only=args.infra_only
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
