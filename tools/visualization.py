"""
Geracao de visualizacoes para analise de resultados.

Este modulo gera graficos e figuras para:
    - Variacao de confianca por tipo de ruido
    - Overlap de Grad-CAM entre baseline e perturbacoes
    - Mapa de calor de risco por imagem x perturbacao
    - Degradacao explicativa
    - Dashboard de conformidade
    - Matriz de similaridade de embeddings
    - Tempos de persistencia e recuperacao
    - Grade de mapas Grad-CAM

As visualizacoes podem ser geradas a partir de um relatorio
de benchmark (JSON) ou diretamente do banco de dados.
"""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from PIL import Image
from sqlalchemy import select
import re

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from config import DATABASE_DSN, MINIO_ACCESS_KEY, MINIO_BUCKET, MINIO_ENDPOINT, MINIO_SECRET_KEY
from persistence import DatabaseClient, GradCam, Inference, MediaAsset, NoiseProfile, PerturbationComparison
from storage import MinIOClient


def parse_s3_uri(uri: str) -> tuple[str, str]:
    """Extrai bucket e nome do objeto de uma URI S3.
    
    Args:
        uri: URI no formato s3://bucket/object
    
    Returns:
        Tupla (bucket, object_name)
    """
    match = re.match(r'^s3://([^/]+)/(.*)$', uri)
    if not match:
        raise ValueError(f'URI MinIO inválida: {uri}')
    return match.group(1), match.group(2)


def download_asset(storage: MinIOClient, uri: str, output_dir: Path) -> str:
    bucket, object_name = parse_s3_uri(uri)
    filename = object_name.replace('/', '_')
    local_path = output_dir / filename
    storage.download_object(object_name, local_path)
    return str(local_path.relative_to(output_dir))


def load_benchmark_report(report_path: Path) -> dict:
    return json.loads(report_path.read_text(encoding='utf-8'))


def plot_confidence_delta(comparisons: list[dict], output_path: Path):
    noise_types = [c['noise_type'] for c in comparisons]
    deltas = [c['confidence_delta'] for c in comparisons]
    overlaps = [c['gradcam_overlap'] for c in comparisons]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    sns.barplot(x=noise_types, y=deltas, hue=noise_types, ax=axes[0], palette='viridis', legend=False)
    axes[0].set_title('Variação de confiança vs. baseline')
    axes[0].set_xlabel('Tipo de ruído')
    axes[0].set_ylabel('Delta de confiança')
    axes[0].tick_params(axis='x', rotation=45)

    sns.barplot(x=noise_types, y=overlaps, hue=noise_types, ax=axes[1], palette='magma', legend=False)
    axes[1].set_title('Overlap Grad-CAM vs. baseline')
    axes[1].set_xlabel('Tipo de ruído')
    axes[1].set_ylabel('IoU')
    axes[1].tick_params(axis='x', rotation=45)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_risk_heatmap(comparisons_by_image: list[list[dict]], image_names: list[str], output_path: Path):
    risk_map = []
    for comps in comparisons_by_image:
        row = []
        for c in comps:
            overlap = c.get('gradcam_overlap', 1.0)
            if c.get('class_changed', False):
                row.append(3)
            elif overlap < 0.4:
                row.append(2)
            elif overlap < 0.6:
                row.append(1)
            else:
                row.append(0)
        risk_map.append(row)

    risk_map = np.array(risk_map)
    labels = [Path(n).stem[:12] for n in image_names]
    noise_labels = [c['noise_type'] for c in comparisons_by_image[0]] if comparisons_by_image else []

    fig, ax = plt.subplots(figsize=(max(8, len(noise_labels) * 1.2), max(4, len(labels) * 0.5)))
    cmap = sns.color_palette(['#2ecc71', '#f1c40f', '#e74c3c', '#8e44ad'])
    sns.heatmap(risk_map, annot=True, fmt='d', xticklabels=noise_labels, yticklabels=labels,
                ax=ax, cmap=cmap, cbar_kws={'label': 'Nível de Risco'})
    ax.set_title('Mapa de Risco por Imagem × Perturbação')
    ax.set_xlabel('Tipo de Ruído')
    ax.set_ylabel('Imagem')

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_explanation_degradation(comparisons: list[dict], output_path: Path):
    noise_types = [c['noise_type'] for c in comparisons]
    overlaps = [c['gradcam_overlap'] for c in comparisons]

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ['#e74c3c' if o < 0.4 else '#f1c40f' if o < 0.6 else '#2ecc71' for o in overlaps]
    bars = ax.bar(noise_types, overlaps, color=colors)
    ax.axhline(y=0.4, color='red', linestyle='--', alpha=0.7, label='Limiar crítico (0.4)')
    ax.axhline(y=0.6, color='orange', linestyle='--', alpha=0.7, label='Limiar moderado (0.6)')
    ax.set_ylim(0, 1)
    ax.set_xlabel('Tipo de Ruído')
    ax.set_ylabel('Overlap Grad-CAM (IoU)')
    ax.set_title('Degradação Explicativa por Tipo de Perturbação')
    ax.legend()
    ax.tick_params(axis='x', rotation=45)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_compliance_dashboard(compliance: dict, output_path: Path):
    items = list(compliance.keys())
    values = [1 if v else 0 for v in compliance.values()]

    fig, ax = plt.subplots(figsize=(8, 3))
    colors = ['#2ecc71' if v else '#e74c3c' for v in values]
    bars = ax.barh(items, values, color=colors)
    ax.set_xlim(0, 1.2)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['NÃO', 'SIM'])
    ax.set_title('Dashboard de Conformidade')

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                'SIM' if val else 'NÃO', va='center', fontweight='bold')

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_summary_table(benchmark: dict, output_path: Path):
    rows = []
    for result in benchmark['results']:
        rows.append({
            'image': Path(result['image']).name,
            'baseline_label': result['baseline_label'],
            'baseline_confidence': round(result['baseline_confidence'], 4),
            'persistence_ms': result['timing_ms']['persistence'],
            'retrieval_ms': result['timing_ms']['retrieval'],
            'storage_delta_mb': benchmark['storage_mb_delta'],
        })

    columns = ['image', 'baseline_label', 'baseline_confidence', 'persistence_ms', 'retrieval_ms', 'storage_delta_mb']
    html = ['<html><head><meta charset="utf-8"><title>Benchmark Summary</title></head><body>']
    html.append('<h1>Benchmark Summary</h1>')
    html.append('<table border="1" cellpadding="6" cellspacing="0">')
    html.append('<thead><tr>')
    for col in columns:
        html.append(f'<th>{col}</th>')
    html.append('</tr></thead>')
    html.append('<tbody>')
    for row in rows:
        html.append('<tr>')
        for col in columns:
            html.append(f'<td>{row[col]}</td>')
        html.append('</tr>')
    html.append('</tbody></table>')
    html.append('</body></html>')
    output_path.write_text('\n'.join(html), encoding='utf-8')


def generate_manifest(benchmark: dict, output_dir: Path) -> dict:
    storage = MinIOClient(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        bucket=MINIO_BUCKET,
    )
    assets_dir = output_dir / 'assets'
    assets_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        'benchmark': {
            'num_images': benchmark['num_images'],
            'num_variants': benchmark['num_variants_per_image'],
            'storage_mb_delta': benchmark['storage_mb_delta'],
            'avg_retrieval_ms': benchmark['avg_retrieval_ms'],
        },
        'results': [],
    }

    for result in benchmark['results']:
        result_entry = {
            'image': Path(result['image']).name,
            'baseline_label': result['baseline_label'],
            'baseline_confidence': result['baseline_confidence'],
            'timing_ms': result['timing_ms'],
            'baseline_image_local': download_asset(storage, result['baseline_image_uri'], assets_dir),
            'baseline_gradcam_local': download_asset(storage, result['baseline_gradcam_uri'], assets_dir),
            'comparisons': result['comparisons'],
            'variants': [],
        }
        for v in result['variants']:
            result_entry['variants'].append({
                'noise_type': v['noise_type'],
                'predicted_label': v['predicted_label'],
                'confidence': v['confidence'],
                'image_local': download_asset(storage, v['image_uri'], assets_dir),
                'gradcam_local': download_asset(storage, v['gradcam_uri'], assets_dir),
            })
        manifest['results'].append(result_entry)

    manifest_path = output_dir / 'report_manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    return manifest


def plot_similarity_matrix(comparisons: list[dict], output_path: Path):
    labels = [c['noise_type'] for c in comparisons]
    n = len(labels) + 1
    matrix = np.eye(n)
    for i, row in enumerate(comparisons, start=1):
        matrix[0, i] = row['embedding_similarity']
        matrix[i, 0] = row['embedding_similarity']

    full_labels = ['baseline'] + labels
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(matrix, annot=True, fmt='.2f', xticklabels=full_labels, yticklabels=full_labels, ax=ax, cmap='Blues')
    ax.set_title('Similaridade de embeddings (baseline vs. perturbações)')
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_retrieval_times(benchmark: dict, output_path: Path):
    retrieval = [r['timing_ms']['retrieval'] for r in benchmark['results']]
    persistence = [r['timing_ms']['persistence'] for r in benchmark['results']]
    images = [Path(r['image']).name for r in benchmark['results']]

    fig, ax = plt.subplots(figsize=(10, 4))
    x = np.arange(len(images))
    width = 0.35
    ax.bar(x - width / 2, persistence, width, label='Persistência (ms)')
    ax.bar(x + width / 2, retrieval, width, label='Recuperação (ms)')
    ax.set_xticks(x)
    ax.set_xticklabels(images, rotation=45, ha='right')
    ax.set_ylabel('Tempo (ms)')
    ax.set_title('Desempenho de persistência e recuperação')
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def _fetch_minio_image(storage: MinIOClient, storage_uri: str) -> Image.Image | None:
    uri = storage_uri.replace(f's3://{MINIO_BUCKET}/', '')
    try:
        response = storage.client.get_object(MINIO_BUCKET, uri)
        return Image.open(response).convert('RGB')
    except Exception:
        return None


def plot_gradcam_grid(experiment_id: str, db: DatabaseClient, storage: MinIOClient, output_path: Path):
    rows = db.query(
        select(Inference, GradCam, MediaAsset, NoiseProfile)
        .join(GradCam, GradCam.inference_id == Inference.inference_id)
        .join(MediaAsset, MediaAsset.media_asset_id == GradCam.media_asset_id)
        .outerjoin(NoiseProfile, Inference.noise_id == NoiseProfile.noise_id)
        .where(Inference.experiment_id == experiment_id)
    )
    if not rows:
        return

    cols = min(4, len(rows))
    row_count = int(np.ceil(len(rows) / cols))
    fig, axes = plt.subplots(row_count, cols, figsize=(4 * cols, 3 * row_count))
    axes = np.atleast_1d(axes).flatten()

    for idx, row in enumerate(rows):
        inference, _gradcam, asset, noise = row
        ax = axes[idx]
        img = _fetch_minio_image(storage, asset.storage_uri)
        if img:
            ax.imshow(img)
        else:
            ax.text(0.5, 0.5, 'N/A', ha='center', va='center')
        noise_label = noise.noise_type if noise else 'none'
        ax.set_title(f'{noise_label}\nconf={inference.confidence:.2f}')
        ax.axis('off')

    for j in range(len(rows), len(axes)):
        axes[j].axis('off')

    fig.suptitle('Mapas Grad-CAM por perturbação')
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def generate_from_report(report_path: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    benchmark = load_benchmark_report(report_path)

    for idx, result in enumerate(benchmark['results']):
        prefix = f'image_{idx}'
        plot_confidence_delta(result['comparisons'], output_dir / f'{prefix}_confidence_overlap.png')
        plot_similarity_matrix(result['comparisons'], output_dir / f'{prefix}_similarity_matrix.png')

    plot_retrieval_times(benchmark, output_dir / 'retrieval_persistence.png')

    if 'risk_summary' in benchmark and benchmark['risk_summary']:
        risk_data = benchmark.get('risk_summary', {})
        if 'by_level' in risk_data:
            fig, ax = plt.subplots(figsize=(6, 4))
            levels = list(risk_data['by_level'].keys())
            counts = list(risk_data['by_level'].values())
            colors = ['#8e44ad' if l == 'CRITICAL' else '#e74c3c' if l == 'HIGH'
                      else '#f1c40f' if l == 'MODERATE' else '#2ecc71' for l in levels]
            ax.bar(levels, counts, color=colors)
            ax.set_title('Distribuição de Risco')
            ax.set_ylabel('Quantidade')
            fig.tight_layout()
            fig.savefig(output_dir / 'risk_distribution.png', dpi=150)
            plt.close(fig)

    comparisons_by_image = [r['comparisons'] for r in benchmark['results']]
    image_names = [r['image'] for r in benchmark['results']]
    plot_risk_heatmap(comparisons_by_image, image_names, output_dir / 'risk_heatmap.png')

    all_comps = []
    for r in benchmark['results']:
        all_comps.extend(r['comparisons'])
    if all_comps:
        plot_explanation_degradation(all_comps, output_dir / 'explanation_degradation.png')

    generate_manifest(benchmark, output_dir)
    print(f'Visualizações salvas em {output_dir}')


def generate_from_experiment(experiment_id: str, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    db = DatabaseClient(DATABASE_DSN)
    storage = MinIOClient(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        bucket=MINIO_BUCKET,
    )

    baseline_row = db.query(
        select(Inference.inference_id)
        .where(Inference.experiment_id == experiment_id, Inference.noise_id.is_(None))
    )
    baseline_ids = [row[0] for row in baseline_row]
    if not baseline_ids:
        raise SystemExit(f'Nenhuma inferência baseline para experiment_id={experiment_id}')

    comparisons = db.query(
        select(PerturbationComparison).where(
            PerturbationComparison.baseline_inference_id.in_(baseline_ids)
        )
    )
    comp_data = [{
        'noise_type': c.noise_type,
        'confidence_delta': c.confidence_delta,
        'gradcam_overlap': c.gradcam_overlap,
        'embedding_similarity': c.embedding_similarity,
        'class_changed': bool(c.class_changed),
    } for row in comparisons for c in [row[0]]]

    if comp_data:
        plot_confidence_delta(comp_data, output_dir / 'confidence_overlap.png')
        plot_similarity_matrix(comp_data, output_dir / 'similarity_matrix.png')
        plot_explanation_degradation(comp_data, output_dir / 'explanation_degradation.png')

    plot_gradcam_grid(experiment_id, db, storage, output_dir / 'gradcam_grid.png')
    print(f'Visualizações salvas em {output_dir}')


def main():
    parser = argparse.ArgumentParser(description='Gera visualizações para artigo e seminário')
    parser.add_argument('--report', type=str, help='Caminho do JSON de benchmark')
    parser.add_argument('--experiment-id', type=str, help='ID do experimento no MySQL')
    parser.add_argument('--output', type=str, default='reports/figures', help='Diretório de saída')
    args = parser.parse_args()

    output_dir = Path(args.output)
    if args.report:
        generate_from_report(Path(args.report), output_dir)
    elif args.experiment_id:
        generate_from_experiment(args.experiment_id, output_dir)
    else:
        raise SystemExit('Informe --report ou --experiment-id')


if __name__ == '__main__':
    main()
