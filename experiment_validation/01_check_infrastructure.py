"""
Validacao da Infraestrutura - Verifica se Docker e portas estao disponiveis.

Este script verifica:
- Se o Docker esta rodando
- Se as portas 3307 (MySQL), 6333 (Qdrant), 9000 (MinIO) estao livres ou em uso
- Se os containers estao saudaveis
"""

import socket
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from config import DATABASE_DSN, QDRANT_URL, MINIO_ENDPOINT


class InfrastructureChecker:
    """Verifica a infraestrutura necessaria para o experimento."""
    
    def __init__(self):
        self.results = []
        self.all_passed = True
    
    def check_port(self, host: str, port: int, service_name: str) -> bool:
        """Verifica se uma porta esta acessivel."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                self._log(f"[OK] {service_name} - {host}:{port} esta acessivel", "success")
                return True
            else:
                self._log(f"[FAIL] {service_name} - {host}:{port} nao esta acessivel", "error")
                self.all_passed = False
                return False
        except Exception as e:
            self._log(f"[FAIL] {service_name} - Erro ao verificar {host}:{port}: {e}", "error")
            self.all_passed = False
            return False
    
    def check_docker_running(self) -> bool:
        """Verifica se o Docker esta rodando."""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self._log("[OK] Docker esta rodando", "success")
                return True
            else:
                self._log("[FAIL] Docker nao esta rodando", "error")
                self.all_passed = False
                return False
        except FileNotFoundError:
            self._log("[FAIL] Docker nao encontrado no PATH", "error")
            self.all_passed = False
            return False
        except subprocess.TimeoutExpired:
            self._log("[FAIL] Timeout ao verificar Docker", "error")
            self.all_passed = False
            return False
    
    def check_docker_compose_services(self) -> dict:
        """Verifica o status dos containers do docker-compose."""
        services_status = {
            'mysql': False,
            'qdrant': False,
            'minio': False
        }
        
        try:
            result = subprocess.run(
                ["docker", "compose", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(Path(__file__).resolve().parent.parent)
            )
            
            if result.returncode == 0 and result.stdout.strip():
                import json
                try:
                    containers = json.loads(result.stdout)
                    if not isinstance(containers, list):
                        containers = [containers]
                    
                    for container in containers:
                        name = container.get('Name', '').lower()
                        state = container.get('State', '')
                        
                        if 'mysql' in name:
                            services_status['mysql'] = state == 'running'
                        elif 'qdrant' in name:
                            services_status['qdrant'] = state == 'running'
                        elif 'minio' in name:
                            services_status['minio'] = state == 'running'
                except json.JSONDecodeError:
                    # Formato alternativo (tabela)
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if 'mysql' in line.lower():
                            services_status['mysql'] = 'running' in line.lower()
                        if 'qdrant' in line.lower():
                            services_status['qdrant'] = 'running' in line.lower()
                        if 'minio' in line.lower():
                            services_status['minio'] = 'running' in line.lower()
                
                for service, running in services_status.items():
                    status = "running" if running else "not running"
                    level = "success" if running else "warning"
                    self._log(f"[{status.upper()}] Container {service}", level)
                    
                    if not running:
                        self.all_passed = False
            else:
                self._log("[WARN] Nenhum container do docker-compose encontrado", "warning")
                self.all_passed = False
                
        except Exception as e:
            self._log(f"[FAIL] Erro ao verificar containers: {e}", "error")
            self.all_passed = False
        
        return services_status
    
    def check_health_endpoints(self) -> dict:
        """Verifica os endpoints de health dos servicos."""
        import urllib.request
        import urllib.error
        
        health_status = {}
        
        # Qdrant health
        try:
            req = urllib.request.urlopen(f"{QDRANT_URL}/", timeout=5)
            health_status['qdrant'] = req.status == 200
            self._log(f"[OK] Qdrant health check: {req.status}", "success")
        except Exception as e:
            health_status['qdrant'] = False
            self._log(f"[FAIL] Qdrant health check falhou: {e}", "error")
            self.all_passed = False
        
        # MinIO health
        try:
            minio_health_url = f"http://{MINIO_ENDPOINT}/minio/health/live"
            req = urllib.request.urlopen(minio_health_url, timeout=5)
            health_status['minio'] = req.status == 200
            self._log(f"[OK] MinIO health check: {req.status}", "success")
        except Exception as e:
            health_status['minio'] = False
            self._log(f"[FAIL] MinIO health check falhou: {e}", "error")
            self.all_passed = False
        
        return health_status
    
    def _log(self, message: str, level: str = "info"):
        """Registra resultado da verificacao."""
        self.results.append({
            'message': message,
            'level': level,
            'timestamp': time.strftime('%H:%M:%S')
        })
        print(message)
    
    def run_all_checks(self) -> dict:
        """Executa todas as verificacoes de infraestrutura."""
        print("=" * 60)
        print("  VALIDACAO DA INFRAESTRUTURA")
        print("=" * 60)
        print()
        
        # 1. Docker
        print("[1/4] Verificando Docker...")
        docker_ok = self.check_docker_running()
        print()
        
        # 2. Containers
        print("[2/4] Verificando containers do docker-compose...")
        containers_status = self.check_docker_compose_services()
        print()
        
        # 3. Portas
        print("[3/4] Verificando portas...")
        self.check_port('127.0.0.1', 3307, 'MySQL')
        self.check_port('127.0.0.1', 6333, 'Qdrant')
        self.check_port('127.0.0.1', 9000, 'MinIO')
        print()
        
        # 4. Health endpoints
        print("[4/4] Verificando health endpoints...")
        health_status = self.check_health_endpoints()
        print()
        
        # Resumo
        print("=" * 60)
        if self.all_passed:
            print("  RESULTADO: TODAS AS VERIFICACOES PASSARAM")
        else:
            print("  RESULTADO: ALGUMAS VERIFICACOES FALHARAM")
        print("=" * 60)
        
        return {
            'docker_running': docker_ok,
            'containers': containers_status,
            'health': health_status,
            'all_passed': self.all_passed,
            'details': self.results
        }


def main():
    checker = InfrastructureChecker()
    results = checker.run_all_checks()
    
    # Exit code baseado no resultado
    sys.exit(0 if results['all_passed'] else 1)


if __name__ == '__main__':
    main()
