"""
Geracao de Relatorio Visual da Validacao.

Este script gera:
- Tabela de resumo das verificacoes
- Grafico de status por camada
- Exemplo de imagem processada com Grad-CAM
- Tabela de comparacao baseline vs perturbacoes
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))


class ReportGenerator:
    """Gera relatorio visual da validacao."""
    
    def __init__(self, output_dir: str = 'experiment_validation/reports'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.report_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'checks': [],
            'summary': {}
        }
    
    def add_check_result(self, check_name: str, results: dict):
        """Adiciona resultado de uma verificacao ao relatorio."""
        self.report_data['checks'].append({
            'name': check_name,
            'results': results
        })
    
    def generate_text_report(self) -> str:
        """Gera relatorio em texto."""
        lines = []
        lines.append("=" * 70)
        lines.append("  RELATORIO DE VALIDACAO DO EXPERIMENTO")
        lines.append(f"  Gerado em: {self.report_data['timestamp']}")
        lines.append("=" * 70)
        lines.append("")
        
        for check in self.report_data['checks']:
            lines.append(f"\n{'-' * 70}")
            lines.append(f"  {check['name'].upper()}")
            lines.append(f"{'-' * 70}")
            
            results = check['results']
            
            if 'all_passed' in results:
                status = "PASSOU" if results['all_passed'] else "FALHOU"
                lines.append(f"\n  Status: {status}")
            
            if 'details' in results:
                lines.append("\n  Detalhes:")
                for detail in results['details']:
                    lines.append(f"    {detail['message']}")
            
            if 'timing' in results:
                lines.append("\n  Tempos:")
                for key, value in results['timing'].items():
                    lines.append(f"    {key}: {value:.2f}s")
            
            if 'persistence' in results:
                lines.append("\n  Persistencia:")
                for layer, status in results['persistence'].items():
                    icon = "[OK]" if status else "[FAIL]"
                    lines.append(f"    {icon} {layer}")
            
            if 'test_results' in results and results['test_results']:
                test = results['test_results']
                if test.get('baseline'):
                    lines.append("\n  Resultado do Teste:")
                    lines.append(f"    Baseline: {test['baseline']['label']} (conf={test['baseline']['confidence']:.4f})")
                    
                    if test.get('variants'):
                        lines.append("\n    Variantes:")
                        for v in test['variants']:
                            lines.append(f"      - {v['noise_type']}: {v['label']} (conf={v['confidence']:.4f})")
                    
                    if test.get('comparisons'):
                        lines.append("\n    Comparacoes:")
                        for c in test['comparisons']:
                            lines.append(f"      - {c['noise_type']}: delta_conf={c['confidence_delta']:+.4f}, overlap={c['gradcam_overlap']:.3f}")
        
        lines.append("\n" + "=" * 70)
        lines.append("  FIM DO RELATORIO")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def generate_html_report(self) -> str:
        """Gera relatorio em HTML."""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html lang='pt-BR'>")
        html.append("<head>")
        html.append("  <meta charset='UTF-8'>")
        html.append("  <title>Relatorio de Validacao</title>")
        html.append("  <style>")
        html.append("    body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }")
        html.append("    .container { max-width: 900px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }")
        html.append("    h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }")
        html.append("    h2 { color: #555; margin-top: 30px; }")
        html.append("    .check { margin: 15px 0; padding: 15px; border-radius: 5px; }")
        html.append("    .check-passed { background: #e8f5e9; border-left: 4px solid #4CAF50; }")
        html.append("    .check-failed { background: #ffebee; border-left: 4px solid #f44336; }")
        html.append("    .detail { margin: 5px 0; padding: 5px 10px; font-family: monospace; font-size: 13px; }")
        html.append("    .success { color: #2e7d32; }")
        html.append("    .error { color: #c62828; }")
        html.append("    .warning { color: #f57f17; }")
        html.append("    .info { color: #1565c0; }")
        html.append("    table { width: 100%; border-collapse: collapse; margin: 10px 0; }")
        html.append("    th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }")
        html.append("    th { background: #f5f5f5; font-weight: bold; }")
        html.append("    .status-badge { display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; }")
        html.append("    .badge-success { background: #4CAF50; color: white; }")
        html.append("    .badge-error { background: #f44336; color: white; }")
        html.append("  </style>")
        html.append("</head>")
        html.append("<body>")
        html.append("  <div class='container'>")
        html.append(f"    <h1>Relatorio de Validacao</h1>")
        html.append(f"    <p><strong>Gerado em:</strong> {self.report_data['timestamp']}</p>")
        
        for check in self.report_data['checks']:
            results = check['results']
            passed = results.get('all_passed', False)
            css_class = "check-passed" if passed else "check-failed"
            status_text = "PASSOU" if passed else "FALHOU"
            badge_class = "badge-success" if passed else "badge-error"
            
            html.append(f"    <div class='check {css_class}'>")
            html.append(f"      <h2>{check['name']} <span class='status-badge {badge_class}'>{status_text}</span></h2>")
            
            if 'details' in results:
                html.append("      <table>")
                html.append("        <tr><th>Status</th><th>Mensagem</th></tr>")
                for detail in results['details']:
                    level = detail.get('level', 'info')
                    icon = "OK" if level == "success" else "FAIL" if level == "error" else "INFO"
                    html.append(f"        <tr><td class='{level}'>[{icon}]</td><td class='{level}'>{detail['message']}</td></tr>")
                html.append("      </table>")
            
            if 'test_results' in results and results['test_results']:
                test = results['test_results']
                if test.get('baseline'):
                    html.append("      <h3>Resultado do Teste</h3>")
                    html.append("      <table>")
                    html.append("        <tr><th>Tipo</th><th>Classe</th><th>Confianca</th></tr>")
                    html.append(f"        <tr><td><strong>Baseline</strong></td><td>{test['baseline']['label']}</td><td>{test['baseline']['confidence']:.4f}</td></tr>")
                    
                    if test.get('variants'):
                        for v in test['variants']:
                            html.append(f"        <tr><td>{v['noise_type']}</td><td>{v['label']}</td><td>{v['confidence']:.4f}</td></tr>")
                    
                    html.append("      </table>")
            
            html.append("    </div>")
        
        html.append("  </div>")
        html.append("</body>")
        html.append("</html>")
        
        return "\n".join(html)
    
    def generate_comparison_table(self, comparisons: list) -> str:
        """Gera tabela de comparacao em Markdown."""
        lines = []
        lines.append("\n## Comparacao Baseline vs Perturbacoes\n")
        lines.append("| Ruido | Delta Confianca | Classe Mudou | Grad-CAM Overlap | Embedding Similarity |")
        lines.append("|-------|-----------------|--------------|------------------|---------------------|")
        
        for comp in comparisons:
            class_changed = "SIM" if comp.get('class_changed') else "NAO"
            lines.append(f"| {comp['noise_type']} | {comp['confidence_delta']:+.4f} | {class_changed} | {comp['gradcam_overlap']:.3f} | {comp['embedding_similarity']:.3f} |")
        
        return "\n".join(lines)
    
    def save_reports(self):
        """Salva todos os formatos de relatorio."""
        # Texto
        text_report = self.generate_text_report()
        text_path = self.output_dir / 'validation_report.txt'
        text_path.write_text(text_report, encoding='utf-8')
        print(f"\n[OK] Relatorio texto salvo: {text_path}")
        
        # HTML
        html_report = self.generate_html_report()
        html_path = self.output_dir / 'validation_report.html'
        html_path.write_text(html_report, encoding='utf-8')
        print(f"[OK] Relatorio HTML salvo: {html_path}")
        
        # JSON
        json_path = self.output_dir / 'validation_report.json'
        json_path.write_text(json.dumps(self.report_data, indent=2, default=str), encoding='utf-8')
        print(f"[OK] Relatorio JSON salvo: {json_path}")
        
        return {
            'text': str(text_path),
            'html': str(html_path),
            'json': str(json_path)
        }


def main():
    """Funcao para teste standalone."""
    generator = ReportGenerator()
    
    # Dados de exemplo
    generator.add_check_result('Infraestrutura', {
        'all_passed': True,
        'details': [
            {'message': '[OK] Docker esta rodando', 'level': 'success'},
            {'message': '[OK] MySQL acessivel na porta 3307', 'level': 'success'},
            {'message': '[OK] Qdrant acessivel na porta 6333', 'level': 'success'},
            {'message': '[OK] MinIO acessivel na porta 9000', 'level': 'success'},
        ]
    })
    
    generator.add_check_result('Pipeline', {
        'all_passed': True,
        'timing': {'model_loading': 2.5, 'full_pipeline': 15.3},
        'persistence': {'mysql': True, 'qdrant': True, 'minio': True},
        'test_results': {
            'baseline': {'label': 'golden_retriever', 'confidence': 0.9234},
            'variants': [
                {'noise_type': 'gaussian', 'label': 'golden_retriever', 'confidence': 0.8912},
                {'noise_type': 'blur', 'label': 'golden_retriever', 'confidence': 0.8543},
                {'noise_type': 'brightness', 'label': 'golden_retriever', 'confidence': 0.9101}
            ],
            'comparisons': [
                {'noise_type': 'gaussian', 'confidence_delta': -0.0322, 'class_changed': False, 'gradcam_overlap': 0.78, 'embedding_similarity': 0.95},
                {'noise_type': 'blur', 'confidence_delta': -0.0691, 'class_changed': False, 'gradcam_overlap': 0.65, 'embedding_similarity': 0.89},
                {'noise_type': 'brightness', 'confidence_delta': -0.0133, 'class_changed': False, 'gradcam_overlap': 0.85, 'embedding_similarity': 0.97}
            ]
        },
        'details': []
    })
    
    paths = generator.save_reports()
    print(f"\nRelatorios gerados em: {generator.output_dir}")


if __name__ == '__main__':
    main()
