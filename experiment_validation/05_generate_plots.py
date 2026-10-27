"""
Geracao de Plots e Visualizacoes dos Resultados.

Este script gera:
- Grafico de status por camada (barras)
- Grafico de tempos de execucao
- Tabela de comparacao baseline vs perturbacoes
- Exemplo de imagem com Grad-CAM (se disponivel)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))


def generate_status_chart(results: dict, output_path: Path):
    """Grafico de status por camada."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')  # Backend sem GUI
        
        layers = []
        statuses = []
        colors = []
        
        for check_name, result in results.items():
            layers.append(check_name.replace(' - ', '\n'))
            statuses.append(1 if result['passed'] else 0)
            colors.append('#4CAF50' if result['passed'] else '#f44336')
        
        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.barh(layers, statuses, color=colors, edgecolor='white', linewidth=2)
        
        ax.set_xlim(0, 1.2)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(['FALHOU', 'PASSOU'])
        ax.set_title('Status de Validacao por Camada', fontsize=14, fontweight='bold')
        
        for bar, status in zip(bars, statuses):
            label = 'PASSOU' if status else 'FALHOU'
            ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
                    label, va='center', fontweight='bold')
        
        fig.tight_layout()
        fig.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        print(f"[OK] Grafico de status salvo: {output_path}")
        return True
        
    except ImportError:
        print("[WARN] matplotlib nao instalado, pulando geracao de graficos")
        return False


def generate_timing_chart(results: dict, output_path: Path):
    """Grafico de tempos de execucao."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
        
        layers = []
        times = []
        
        for check_name, result in results.items():
            layers.append(check_name.replace(' - ', '\n'))
            times.append(result['elapsed'])
        
        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.barh(layers, times, color='#2196F3', edgecolor='white', linewidth=2)
        
        ax.set_xlabel('Tempo (segundos)')
        ax.set_title('Tempo de Execucao por Validacao', fontsize=14, fontweight='bold')
        
        for bar, time_val in zip(bars, times):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                    f'{time_val:.1f}s', va='center')
        
        fig.tight_layout()
        fig.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        print(f"[OK] Grafico de tempos salvo: {output_path}")
        return True
        
    except ImportError:
        return False


def generate_comparison_table_image(comparisons: list, output_path: Path):
    """Tabela de comparacao como imagem."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
        
        if not comparisons:
            print("[INFO] Sem comparacoes para gerar tabela")
            return False
        
        fig, ax = plt.subplots(figsize=(12, len(comparisons) * 0.8 + 2))
        ax.axis('off')
        
        # Cabecalho
        headers = ['Ruido', 'Delta Confianca', 'Classe Mudou', 'Grad-CAM Overlap', 'Embedding Similarity']
        
        # Dados
        rows = []
        for comp in comparisons:
            rows.append([
                comp['noise_type'],
                f"{comp['confidence_delta']:+.4f}",
                "SIM" if comp.get('class_changed') else "NAO",
                f"{comp['gradcam_overlap']:.3f}",
                f"{comp['embedding_similarity']:.3f}"
            ])
        
        table = ax.table(
            cellText=rows,
            colLabels=headers,
            loc='center',
            cellLoc='center'
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)
        
        # Estilo
        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_facecolor('#4CAF50')
                cell.set_text_props(color='white', fontweight='bold')
            elif row % 2 == 0:
                cell.set_facecolor('#f5f5f5')
        
        ax.set_title('Comparacao Baseline vs Perturbacoes', fontsize=14, fontweight='bold', pad=20)
        
        fig.tight_layout()
        fig.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        print(f"[OK] Tabela de comparacao salva: {output_path}")
        return True
        
    except ImportError:
        return False


def generate_architecture_diagram(output_path: Path):
    """Diagrama da arquitetura hibrida."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.patches as mpatches
        
        fig, ax = plt.subplots(figsize=(14, 8))
        ax.set_xlim(0, 14)
        ax.set_ylim(0, 8)
        ax.axis('off')
        
        # Cores
        color_mysql = '#4CAF50'
        color_qdrant = '#2196F3'
        color_minio = '#FF9800'
        color_pipeline = '#9C27B0'
        
        # MySQL
        mysql_rect = mpatches.FancyBboxPatch((0.5, 5), 3, 2, boxstyle="round,pad=0.1",
                                              facecolor=color_mysql, edgecolor='white', linewidth=2)
        ax.add_patch(mysql_rect)
        ax.text(2, 6.5, 'MySQL', ha='center', va='center', fontsize=14, fontweight='bold', color='white')
        ax.text(2, 5.8, 'Banco Relacional', ha='center', va='center', fontsize=10, color='white')
        ax.text(2, 5.3, 'Metadados, Inferencias', ha='center', va='center', fontsize=8, color='white')
        
        # Qdrant
        qdrant_rect = mpatches.FancyBboxPatch((5.5, 5), 3, 2, boxstyle="round,pad=0.1",
                                               facecolor=color_qdrant, edgecolor='white', linewidth=2)
        ax.add_patch(qdrant_rect)
        ax.text(7, 6.5, 'Qdrant', ha='center', va='center', fontsize=14, fontweight='bold', color='white')
        ax.text(7, 5.8, 'Banco Vetorial', ha='center', va='center', fontsize=10, color='white')
        ax.text(7, 5.3, 'Embeddings, Similaridade', ha='center', va='center', fontsize=8, color='white')
        
        # MinIO
        minio_rect = mpatches.FancyBboxPatch((10.5, 5), 3, 2, boxstyle="round,pad=0.1",
                                              facecolor=color_minio, edgecolor='white', linewidth=2)
        ax.add_patch(minio_rect)
        ax.text(12, 6.5, 'MinIO', ha='center', va='center', fontsize=14, fontweight='bold', color='white')
        ax.text(12, 5.8, 'Armazenamento', ha='center', va='center', fontsize=10, color='white')
        ax.text(12, 5.3, 'Imagens, Grad-CAMs', ha='center', va='center', fontsize=8, color='white')
        
        # Pipeline
        pipeline_rect = mpatches.FancyBboxPatch((3, 1), 8, 2.5, boxstyle="round,pad=0.1",
                                                 facecolor=color_pipeline, edgecolor='white', linewidth=2)
        ax.add_patch(pipeline_rect)
        ax.text(7, 3, 'Pipeline de Processamento', ha='center', va='center', fontsize=14, fontweight='bold', color='white')
        ax.text(7, 2.2, 'ResNet50 + Grad-CAM + Perturbacoes', ha='center', va='center', fontsize=10, color='white')
        ax.text(7, 1.5, '100 imagens x 4 variantes = 400 inferencias', ha='center', va='center', fontsize=9, color='white')
        
        # Setas
        ax.annotate('', xy=(3, 3.5), xytext=(2, 5),
                    arrowprops=dict(arrowstyle='->', color='gray', lw=2))
        ax.annotate('', xy=(7, 3.5), xytext=(7, 5),
                    arrowprops=dict(arrowstyle='->', color='gray', lw=2))
        ax.annotate('', xy=(11, 3.5), xytext=(12, 5),
                    arrowprops=dict(arrowstyle='->', color='gray', lw=2))
        
        ax.set_title('Arquitetura Hibrida de Persistencia', fontsize=16, fontweight='bold', pad=20)
        
        fig.tight_layout()
        fig.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        print(f"[OK] Diagrama de arquitetura salvo: {output_path}")
        return True
        
    except ImportError:
        return False


def main():
    """Funcao principal."""
    output_dir = Path(__file__).parent / 'reports'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("  GERACAO DE PLOTS E VISUALIZACOES")
    print("=" * 60)
    print()
    
    # Diagrama de arquitetura
    print("[1/4] Gerando diagrama de arquitetura...")
    generate_architecture_diagram(output_dir / 'architecture_diagram.png')
    
    # Tentar carregar resultados do relatorio JSON
    report_json = output_dir / 'validation_report.json'
    if report_json.exists():
        with open(report_json) as f:
            data = json.load(f)
        
        results = {}
        comparisons = []
        
        for check in data.get('checks', []):
            name = check['name']
            results[name] = {
                'passed': check['results'].get('all_passed', False),
                'elapsed': check['results'].get('elapsed', 0)
            }
            
            test_results = check['results'].get('test_results', {})
            if test_results and test_results.get('comparisons'):
                comparisons = test_results['comparisons']
        
        # Gerar graficos
        print("\n[2/4] Gerando grafico de status...")
        generate_status_chart(results, output_dir / 'validation_status.png')
        
        print("\n[3/4] Gerando grafico de tempos...")
        generate_timing_chart(results, output_dir / 'validation_timing.png')
        
        print("\n[4/4] Gerando tabela de comparacao...")
        if comparisons:
            generate_comparison_table_image(comparisons, output_dir / 'comparison_table.png')
    else:
        print("\n[INFO] Relatorio JSON nao encontrado. Execute run_validation.py primeiro.")
        print("Gerando apenas diagrama de arquitetura.")
    
    print(f"\n[OK] Visualizacoes salvas em: {output_dir}")


if __name__ == '__main__':
    main()
