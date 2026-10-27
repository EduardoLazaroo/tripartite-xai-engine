"""
Exportacao de relatorios para interface web.

Este modulo exporta o manifesto de relatorio e os ativos
associados (imagens, Grad-CAMs) para o diretorio da
interface web (ui/), permitindo visualizacao dos resultados.
"""

import argparse
import json
import shutil
import stat
from pathlib import Path


def _force_remove_readonly(func, path, excinfo):
    """Forca remocao de arquivos somente-leitura no Windows."""
    import os
    os.chmod(path, stat.S_IWRITE)
    func(path)


def main():
    """Exporta relatorio e ativos para a interface web.
    
    Copia o report_manifest.json e o diretorio de assets
    para o destino especificado (padrao: ui/).
    """
    parser = argparse.ArgumentParser(description='Exporta relatorio e ativos para a interface web em ui/')
    parser.add_argument('--report', type=str, required=True, help='Caminho para report_manifest.json ou diretório de relatório')
    parser.add_argument('--dest', type=str, default='ui', help='Diretório de destino da interface web')
    args = parser.parse_args()

    report_path = Path(args.report)
    if report_path.is_dir():
        report_path = report_path / 'report_manifest.json'

    if not report_path.exists():
        raise SystemExit(f'Arquivo de manifesto não encontrado: {report_path}')

    if report_path.name != 'report_manifest.json':
        raise SystemExit('O arquivo informado deve ser report_manifest.json')

    dest_dir = Path(args.dest).resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_manifest = dest_dir / 'report_manifest.json'
    shutil.copy2(report_path, dest_manifest)

    source_assets = report_path.parent / 'assets'
    dest_assets = dest_dir / 'assets'
    if dest_assets.exists():
        shutil.rmtree(dest_assets, onerror=_force_remove_readonly)
    shutil.copytree(source_assets, dest_assets)

    print(f'Manifest e ativos exportados para {dest_dir}')


if __name__ == '__main__':
    main()
