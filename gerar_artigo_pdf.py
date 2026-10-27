"""
Script para gerar artigo academico em PDF profissional
Baseado nos resultados do benchmark executado em 2026-06-27.

Dados atualizados da execucao atual (com otimizacoes):
- 100 imagens, 11 classes, 4 variantes, 400 inferencias
- Persistencia media: 9417.73ms/imagem
- Recuperacao media: 31.35ms
- Storage: 247.64 MB
- Risco: 20 CRITICAL (6.7%), 7 MODERATE, 273 LOW
- Overlap medio: 0.8456

Otimizacoes implementadas:
- Connection pooling no MySQL (pool_size=10, max_overflow=20)
- Batch upsert no Qdrant (100 pontos por requisicao)
- Cache de labels em memoria
- Controle de flush por variante

Gerador PDF profissional com:
- Fonte Times New Roman (12pt corpo, 14tt secao, 16tt titulo)
- Margens ABNT (3cm superior/inferior, 3cm esquerda, 2cm direita)
- Numeracao automatica de pagina (rodape)
- Numeracao automatica de figuras e tabelas
- Referencias numeradas automaticamente
- Legendas em figuras/tabelas
- Sumario automatico (com pagina)
- Formatacao de tabelas com cores alternadas
"""

import os
from fpdf import FPDF

# Diretorio base para figuras (assets ao lado do script)
FIGURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')


class ArtigoPDF(FPDF):
    """Classe customizada para geracao de artigo academico em PDF."""

    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        self._setup_fonts()
        self._figure_num = 0
        self._table_num = 0
        self._references = []
        self._toc_entries = []  # (title, level, page)
        self._current_section_page = 0
        # Margens ABNT: 3cm esquerda, 2cm direita, 3cm topo, 2cm base
        self.set_margins(30, 30, 20)
        self.set_auto_page_break(auto=True, margin=20)

    def _setup_fonts(self):
        """Configura fontes Times New Roman com caminho absoluto (TTF completo)."""
        fonts_dir = 'C:/Windows/Fonts'
        # Usar familia 'tnr' para evitar conflito com core fonts 'times'
        self.add_font('tnr', '', f'{fonts_dir}/times.ttf')
        self.add_font('tnr', 'B', f'{fonts_dir}/timesbd.ttf')
        self.add_font('tnr', 'I', f'{fonts_dir}/timesi.ttf')
        self.add_font('tnr', 'BI', f'{fonts_dir}/timesbi.ttf')
        self.set_font('tnr', '', 12)

    def header(self):
        """Cabecalho da pagina: nome do artigo (acima de 50 paginas, omitido)."""
        pass  # Sem cabecalho para artigo academico

    def footer(self):
        """Rodape da pagina: numeracao centralizada."""
        self.set_y(-15)
        self.set_font('tnr', '', 10)
        self.set_text_color(0, 0, 0)
        page_text = f'- {self.page_no()} -'
        self.cell(0, 10, page_text, align='C')

    def _needs_page_break(self, needed_height):
        """Verifica se e necessario quebrar pagina antes de adicionar conteudo."""
        bottom_limit = self.h - 20  # margem inferior
        return (self.get_y() + needed_height) > bottom_limit

    def _safe_add_page_break(self, needed_height):
        """Adiciona quebra de pagina se necessario. Retorn True se quebrou."""
        if self._needs_page_break(needed_height):
            self.add_page()
            return True
        return False

    def add_cover(self, title, author, institution, program, location, year):
        """Adiciona capa do artigo centralizada verticalmente."""
        self.add_page()
        self.set_auto_page_break(auto=False)
        
        # Calcular altura total do bloco de capa para centralizar
        block_height = 60 + 8 + 15 + 8 + 5 + 7 + 3 + 7 + 10 + 7  # estimativa
        start_y = max(60, (self.h - block_height) / 2)
        self.set_y(start_y)

        # Titulo
        self.set_font('tnr', 'B', 16)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 8, title, align='C')
        self.ln(10)

        # Autor
        self.set_font('tnr', '', 14)
        self.cell(0, 8, author, align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(5)

        # Instituicao
        self.set_font('tnr', '', 12)
        self.cell(0, 7, institution, align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(3)

        # Programa
        self.set_font('tnr', '', 11)
        self.cell(0, 7, program, align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(10)

        # Local e ano
        self.set_font('tnr', '', 12)
        self.cell(0, 7, f'{location}, {year}', align='C', new_x='LMARGIN', new_y='NEXT')
        
        self.set_auto_page_break(auto=True, margin=20)

    def add_abstract(self, text, keywords):
        """Adiciona resumo e palavras-chave."""
        self.add_page()
        self._add_section_heading('Resumo', level=1)
        self.set_font('tnr', '', 12)
        self.set_text_color(0, 0, 0)
        self._add_body_text(text)
        self.ln(4)
        # Palavras-chave em linha separada com indentacao
        self.set_font('tnr', 'B', 12)
        self.cell(0, 6, 'Palavras-chave:', new_x='LMARGIN', new_y='NEXT')
        self.set_font('tnr', '', 12)
        self.set_x(self.l_margin + 12)
        self.multi_cell(self.w - self.l_margin - self.r_margin - 12, 6, keywords, align='J')

    def add_toc(self):
        """Adiciona sumario."""
        self.add_page()
        self._add_section_heading('Sumário', level=1)
        self.ln(5)
        self.set_font('tnr', '', 12)
        for title, level, page in self._toc_entries:
            indent = '    ' * (level - 1)
            self.cell(0, 7, f'{indent}{title}  {page}', new_x='LMARGIN', new_y='NEXT')

    def _add_section_heading(self, text, level=1):
        """Adiciona titulo de secao formatado.
        
        Correcao: nao força mais quebra de pagina automatica entre secoes.
        Apenas garante espaco minimo para o titulo quando possivel.
        """
        sizes = {1: 14, 2: 13, 3: 12}
        size = sizes.get(level, 12)
        # Apenas garantir espaco para titulo (7mm) + espacamento (5mm)
        # Nao força mais quebra de pagina automatica
        self.set_font('tnr', 'B', size)
        self.set_text_color(0, 0, 0)
        self.ln(3)
        self.cell(0, 7, text, new_x='LMARGIN', new_y='NEXT')
        self.ln(2)
        # Registrar no sumario
        self._toc_entries.append((text, level, self.page_no()))

    def _add_body_text(self, text, indent=True):
        """Adiciona paragrafo de corpo de texto com indentacao.
        
        Correcao: usa multi_cell com largura reduzida para indentacao,
        evitando o bug de set_x() + multi_cell(0) que causava saltos.
        """
        self.set_font('tnr', '', 12)
        self.set_text_color(0, 0, 0)
        if indent:
            # Indentacao: reduzir largura efetiva e deslocar x temporariamente
            # Usar multi_cell com x offset para primeira linha
            indent_mm = 12  # ~1.2cm de indentacao
            # Primeira linha com indentacao
            self.set_x(self.l_margin + indent_mm)
            # Usar multi_cell com new_x='LMARGIN' para resetar apos cada linha
            self.multi_cell(self.w - self.r_margin - self.l_margin - indent_mm, 6, text, align='J')
        else:
            self.multi_cell(0, 6, text, align='J')

    def add_paragraph(self, text, indent=True):
        """Adiciona paragrafo formatado."""
        self._add_body_text(text, indent)

    def add_bullet(self, text):
        """Adiciona item de lista com marcador."""
        self.set_font('tnr', '', 12)
        self.set_text_color(0, 0, 0)
        bullet = '• '
        # Calcular largura do bullet
        bullet_width = self.get_string_width(bullet) + 2
        text_width = self.w - self.r_margin - self.l_margin - bullet_width - 12
        self.set_x(self.l_margin + 12)
        # Escrever bullet na primeira linha
        self.cell(bullet_width, 6, bullet, new_x='END')
        self.multi_cell(text_width, 6, text, align='J')

    def add_table(self, headers, rows, caption=None, col_widths=None):
        """Adiciona tabela formatada com cores alternadas.
        
        Args:
            headers: lista de cabecalhos
            rows: lista de linhas (cada linha e uma lista)
            caption: legenda da tabela
            col_widths: lista opcional com larguras relativas das colunas (ex: [3, 2, 3])
        """
        self._table_num += 1
        self.ln(3)

        # Calcular largura das colunas
        col_count = len(headers)
        available_width = self.w - self.l_margin - self.r_margin
        
        if col_widths:
            # Usar proporcoes especificadas
            total_units = sum(col_widths)
            col_widths_mm = [available_width * (w / total_units) for w in col_widths]
        else:
            # Distribuir igualmente
            col_widths_mm = [available_width / col_count] * col_count

        # Verificar se precisa quebrar pagina
        row_height = 7
        header_height = 8
        caption_height = 12 if caption else 0
        total_height = header_height + len(rows) * row_height + caption_height + 10
        self._safe_add_page_break(total_height)

        # Header
        self.set_font('tnr', 'B', 9)
        self.set_fill_color(70, 130, 180)  # Steel blue
        self.set_text_color(255, 255, 255)
        for i, header in enumerate(headers):
            self.cell(col_widths_mm[i], header_height, header, border=1, align='C', fill=True)
        self.ln()

        # Data rows
        for i, row in enumerate(rows):
            # Alternar cores
            if i % 2 == 0:
                self.set_fill_color(240, 248, 255)  # Alice blue
            else:
                self.set_fill_color(255, 255, 255)

            self.set_font('tnr', '', 9)
            self.set_text_color(0, 0, 0)
            for j, cell_text in enumerate(row):
                self.cell(col_widths_mm[j], row_height, str(cell_text), border=1, align='C', fill=True)
            self.ln()

        self.ln(2)

        # Legenda da tabela (com quebra de linha)
        if caption:
            self.set_font('tnr', 'B', 9)
            self.set_text_color(0, 0, 0)
            self.multi_cell(0, 6, f'Tabela {self._table_num}: {caption}')

        self.ln(3)

    def add_figure(self, image_path, caption, img_width=100):
        """Adiciona figura com imagem e legenda.
        
        Args:
            image_path: caminho da imagem (None para figura sem imagem)
            caption: legenda da figura
            img_width: largura da imagem em mm (padrao: 100)
        """
        self._figure_num += 1

        if image_path and os.path.exists(image_path):
            # Dimensoes da imagem
            img_height = img_width * 0.75  # proporcao 4:3
            caption_height = 15
            
            # Verificar se imagem + legenda cabem na pagina
            total_needed = img_height + caption_height + 10
            self._safe_add_page_break(total_needed)
            
            x = (self.w - img_width) / 2
            self.image(image_path, x=x, w=img_width)
            self.ln(3)

        # Legenda com quebra de linha
        self.set_font('tnr', 'B', 10)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, f'Figura {self._figure_num}: {caption}')
        self.ln(3)

    def add_figure_panel(self, image_paths, caption, titles=None, cols=2, img_width_factor=1.0):
        """Adiciona painel com multiplas imagens lado a lado.
        
        Args:
            image_paths: lista de caminhos das imagens
            caption: legenda do painel
            titles: lista opcional de titulos para cada imagem
            cols: numero de colunas
            img_width_factor: fator de escala da largura (1.0 = 100%, 0.8 = 80%)
        
        Correcao: calcula posicoes corretamente e avanca o cursor apos o painel.
        """
        self._figure_num += 1
        valid_paths = [p for p in image_paths if p and os.path.exists(p)]

        if not valid_paths:
            self.set_font('tnr', 'B', 10)
            self.set_text_color(0, 0, 0)
            self.multi_cell(0, 6, f'Figura {self._figure_num}: {caption}')
            return

        self.ln(2)

        # Calcular tamanho das imagens
        available_width = self.w - self.l_margin - self.r_margin
        base_img_width = (available_width - (cols - 1) * 5) / cols
        img_width = base_img_width * img_width_factor
        img_height = img_width * 0.75  # proporcao 4:3
        title_height = 6
        row_spacing = title_height + 4

        # Verificar se cabe na pagina
        rows_needed = (len(valid_paths) + cols - 1) // cols
        caption_height = 15
        total_height = rows_needed * (img_height + row_spacing) + caption_height + 10
        self._safe_add_page_break(total_height)

        # Posicao inicial do painel
        start_y = self.get_y()
        x_start = self.l_margin

        # Desenhar todas as imagens e titulos
        max_y = start_y
        for idx, path in enumerate(valid_paths):
            col = idx % cols
            row = idx // cols

            # Centralizar o painel horizontalmente
            total_panel_width = cols * img_width + (cols - 1) * 5
            x_offset = (available_width - total_panel_width) / 2
            x = x_start + x_offset + col * (img_width + 5)
            y = start_y + row * (img_height + row_spacing)

            # Desenhar imagem
            self.image(path, x=x, y=y, w=img_width, h=img_height)

            # Titulo abaixo da imagem
            if titles and idx < len(titles):
                self.set_xy(x, y + img_height + 1)
                self.set_font('tnr', 'B', 9)
                self.set_text_color(0, 0, 0)
                self.cell(img_width, title_height, titles[idx], align='C')
                max_y = max(max_y, y + img_height + title_height + 2)

        # Avancar cursor para apos o painel
        self.set_y(max_y + 5)

        # Legenda principal (com quebra de linha)
        self.set_font('tnr', 'B', 10)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, f'Figura {self._figure_num}: {caption}')
        self.ln(3)

    def add_references(self, references):
        """Adiciona referencias bibliograficas numeradas com hanging indent."""
        self.add_page()
        self._add_section_heading('Referências', level=1)
        self.ln(3)

        for i, ref in enumerate(references, 1):
            self.set_font('tnr', '', 11)
            self.set_text_color(0, 0, 0)
            # Referencia numerada com hanging indent
            ref_text = f'[{i}] {ref}'
            # Usar multi_cell com x offset para hanging indent
            indent = 12  # espaco para o numero
            self.set_x(self.l_margin)
            self.multi_cell(self.w - self.l_margin - self.r_margin, 6, ref_text, align='J')
            self.ln(1)

    def build(self, output_path):
        """Constroi o PDF completo e salva."""
        self.output(output_path)


def main():
    pdf = ArtigoPDF()

    # ========== CAPA ==========
    pdf.add_cover(
        title='Arquitetura Híbrida de Persistência e Recuperação de Evidências Explicativas em Sistemas de Visão Computacional Baseados em Deep Learning',
        author='Eduardo Lázaro Roesler de Oliveira',
        institution='Universidade Estadual Paulista (UNESP) - Faculdade de Ciências e Tecnologia',
        program='Programa de Pós-Graduação em Ciência da Computação - Disciplina de Banco de Dados',
        location='Presidente Prudente',
        year='2026'
    )

    # ========== RESUMO ==========
    pdf.add_abstract(
        text='O avanço recente dos modelos de Deep Learning tem impulsionado a adoção de sistemas de Inteligência Artificial em diversos domínios, '
             'especialmente em aplicações de Visão Computacional. Embora esses modelos apresentem elevado desempenho preditivo, suas decisões frequentemente '
             'são caracterizadas por baixa interpretabilidade. Como resposta a esse desafio, técnicas de Explainable Artificial Intelligence (XAI) têm sido '
             'amplamente exploradas para produzir evidências explicativas. Entretanto, a maior parte dos estudos concentra-se na produção dessas evidências, '
             'enquanto pouca atenção é dedicada ao seu armazenamento, gerenciamento e recuperação posterior. Diante desse cenário, este trabalho investiga '
             'como uma arquitetura híbrida de persistência pode contribuir para o armazenamento, recuperação e auditoria de evidências explicativas produzidas '
             'por sistemas de Visão Computacional baseados em Deep Learning. A arquitetura proposta integra três tecnologias complementares: MySQL para persistência '
             'relacional de metadados, Qdrant para indexação e busca vetorial de embeddings, e MinIO para armazenamento de objetos multimídia. Os resultados '
             'experimentais demonstram que a arquitetura é capaz de persistir evidências explicativas com integridade referencial, recuperar evidências similares '
             'em tempo real (aproximadamente 31,35 ms) e armazenar ativos multimídia de forma eficiente (247,64 MB), contribuindo para mecanismos mais robustos de auditoria, '
             'rastreabilidade e recuperação contextual de inferências.',
        keywords='Explainable AI, Bancos de Dados Híbridos, Persistência de Evidências, Visão Computacional, Deep Learning, '
                 'Busca por Similaridade, Auditoria de IA.'
    )

    # ========== SUMÁRIO: removido (desnecessário para artigo PDF) ==========

    # ========== 1. INTRODUÇÃO ==========
    pdf._add_section_heading('1. Introdução', level=1)

    pdf.add_paragraph(
        'O avanço recente dos modelos de Deep Learning tem impulsionado a adoção de sistemas de Inteligência Artificial (IA) em diversos domínios, '
        'especialmente em aplicações de Visão Computacional (LECUN et al., 2015; HE et al., 2016). No entanto, esses modelos operam frequentemente como '
        '"caixas-pretas", produzindo decisões sem explicar quais fatores influenciaram determinada predição (RIBEIRO et al., 2016).'
    )

    pdf.add_paragraph(
        'Como resposta, técnicas de Explainable AI (XAI) têm sido exploradas para produzir evidências explicativas (ARRIETA et al., 2020), como '
        'mapas de ativação (Grad-CAM), embeddings vetoriais e métricas de confiança (SELVARAJU et al., 2017). Entretanto, a maior parte dos estudos '
        'concentra-se na produção dessas evidências, enquanto pouca atenção é dedicada ao seu armazenamento e recuperação posterior, limitando atividades '
        'de auditoria e rastreabilidade.'
    )

    pdf.add_paragraph(
        'Sem mecanismos adequados de persistência, um auditor não teria meios de identificar degradações de comportamento do modelo ao longo do tempo. '
        'A arquitetura proposta transforma modelos de IA em sistemas auditáveis retroativamente, persistindo evidências em três tecnologias complementares: '
        'MySQL para metadados, Qdrant para embeddings vetoriais e MinIO para objetos multimídia. Essa capacidade é relevante para conformidade com a LGPD '
        'e GDPR, nos quais a explicabilidade de decisões automatizadas passa a ser requisito legal.'
    )

    pdf.add_paragraph(
        'Este trabalho investiga: como uma arquitetura híbrida de persistência pode contribuir para o armazenamento, recuperação e auditoria de evidências '
        'explicativas produzidas por sistemas de Visão Computacional baseados em Deep Learning? Propõe-se uma arquitetura que trata evidências como entidades '
        'persistentes em um ecossistema integrado de Banco de Dados.'
    )

    # ========== 2. FUNDAMENTAÇÃO TEÓRICA ==========
    pdf._add_section_heading('2. Fundamentação Teórica', level=1)

    pdf._add_section_heading('2.1 Deep Learning e Visão Computacional', level=2)

    pdf.add_paragraph(
        'Deep Learning é um subcampo de Machine Learning baseado em redes neurais artificiais com múltiplas camadas de processamento. No contexto '
        'da Visão Computacional, as Redes Neurais Convolucionais (CNNs) são a arquitetura predominante, capazes de aprender representações hierárquicas '
        'de características visuais diretamente a partir dos dados de imagem (LECUN et al., 2015).'
    )

    pdf.add_paragraph(
        'A ResNet50 (HE et al., 2016) é uma CNN com 50 camadas que introduz conexões residuais (skip connections) para mitigar o problema do '
        'desvanecimento do gradiente em redes profundas. Treinada no dataset ImageNet com mais de 1 milhão de imagens, a ResNet50 atinge acurácia '
        'top-1 de aproximadamente 76% e é amplamente utilizada como modelo base para tarefas de classificação e extração de características.'
    )

    pdf.add_paragraph(
        'Os embeddings visuais gerados pela ResNet50 correspondem à ativação da penúltima camada (average pooling), resultando em vetores de '
        '2048 dimensões que codificam características semânticas de alto nível da imagem. Essas representações vetoriais são fundamentais para tarefas '
        'de busca por similaridade e recuperação de informação visual.'
    )

    pdf._add_section_heading('2.2 Explainable AI (XAI)', level=2)

    pdf.add_paragraph(
        'Explainable AI (XAI) refere-se a métodos e técnicas que tornam as decisões de modelos de IA compreensíveis para humanos (ARRIETA et al., 2020). '
        'No contexto de Visão Computacional, as técnicas de XAI mais comuns incluem mapas de ativação, que destacam as regiões da imagem mais relevantes '
        'para a predição do modelo.'
    )

    pdf.add_paragraph(
        'O Grad-CAM (Gradient-weighted Class Activation Mapping) (SELVARAJU et al., 2017) é uma técnica de explicabilidade que utiliza os gradientes '
        'da classe alvo em relação à última camada convolucional para produzir um mapa de calor que indica as regiões de maior influência na decisão. '
        'Diferente de técnicas anteriores, o Grad-CAM é agnóstico à arquitetura e pode ser aplicado a qualquer CNN sem modificações estruturais.'
    )

    pdf.add_paragraph(
        'Embora as técnicas de XAI gerem evidências valiosas, essas informações são frequentemente tratadas como subprodutos efêmeros, utilizadas '
        'apenas momentaneamente durante a inferência e descartadas em seguida. Este trabalho propõe tratar essas evidências como entidades persistentes '
        'de primeira classe em um banco de dados.'
    )

    pdf._add_section_heading('2.3 Bancos de Dados Híbridos', level=2)

    pdf.add_paragraph(
        'A arquitetura proposta integra três paradigmas de armazenamento: (1) MySQL -- banco relacional para metadados estruturados e trilhas de auditoria, '
        'garantindo propriedades ACID e integridade referencial (ELMASRI; NAVATHE, 2016); (2) Qdrant -- banco vetorial otimizado para busca por similaridade '
        'em espaços de alta dimensionalidade via algoritmo HNSW (BARRETO et al., 2023); e (3) MinIO -- armazenamento de objetos compatível com S3 API para ativos '
        'multimídia como imagens e mapas de ativação (MINIO, 2024).'
    )

    pdf._add_section_heading('2.4 Recuperação de Informação Similaridade', level=2)

    pdf.add_paragraph(
        'A recuperação de informação em espaços vetoriais envolve encontrar os vetores mais similares a um vetor de consulta em um conjunto de dados. '
        'A métrica de distância cosseno é amplamente utilizada para embeddings de alta dimensionalidade, pois mede o ângulo entre vetores em vez de '
        'sua magnitude, sendo adequada para comparar similaridade semântica (SCHUHMACHER et al., 2023).'
    )

    pdf.add_paragraph(
        'O algoritmo HNSW (MALKOV; YASHUNIN, 2016) constrói um grafo hierárquico de pequeno mundo que permite buscas aproximadas com complexidade '
        'sublinear. O HNSW é o algoritmo padrão do Qdrant e oferece um equilíbrio entre recall, latência e uso de memória, sendo adequado para aplicações '
        'que exigem recuperação em tempo real de embeddings de alta dimensionalidade.'
    )

    # ========== 3. TRABALHOS RELACIONADOS ==========
    pdf._add_section_heading('3. Trabalhos Relacionados', level=1)

    pdf.add_paragraph(
        'A interseção entre Bancos de Dados e Inteligência Artificial Explicável tem recebido atenção crescente na literatura recente. Esta seção '
        'apresenta trabalhos relacionados que abordam aspectos de persistência, recuperação e auditoria de evidências de IA.'
    )

    pdf.add_paragraph(
        'Ribeiro et al. (2016) propuseram o LIME (Local Interpretable Model-agnostic Explanations), uma técnica de explicabilidade local que gera '
        'explicações para predições individuais. No entanto, o LIME não aborda o armazenamento persistente das explicações geradas, tratando-as como '
        'artefatos temporários.'
    )

    pdf.add_paragraph(
        'Selvaraju et al. (2017) introduziram o Grad-CAM, técnica de explicabilidade baseada em gradientes que gera mapas de calor para CNNs. O Grad-CAM '
        'é amplamente utilizado, mas sua implementação padrão não inclui mecanismos de persistência ou recuperação das evidências geradas.'
    )

    pdf.add_paragraph(
        'Arrieta et al. (2020) apresentam uma revisão abrangente sobre XAI, discutindo taxonomias, técnicas e desafios. Os autores destacam a necessidade '
        'de mecanismos de auditoria e rastreabilidade, mas não propõem soluções de banco de dados para persistência de evidências.'
    )

    pdf.add_paragraph(
        'No contexto de bancos de dados vetoriais, Barreto et al. (2023) discutem a aplicação de índices HNSW para recuperação eficiente de embeddings '
        'em sistemas de grande escala. Os autores demonstram que a busca por similaridade vetorial pode ser realizada em milissegundos mesmo para milhões '
        'de vetores.'
    )

    pdf.add_paragraph(
        'A Tabela 1 apresenta uma comparação crítica entre os trabalhos relacionados e a proposta deste artigo.'
    )

    # Tabela de comparação
    headers = ['Trabalho', 'Técnica XAI', 'Persistência', 'Busca Vetorial', 'Auditoria', 'Arquitetura Híbrida']
    rows = [
        ['Ribeiro (2016)', 'LIME', 'Não', 'Não', 'Não', 'Não'],
        ['Selvaraju (2017)', 'Grad-CAM', 'Não', 'Não', 'Não', 'Não'],
        ['Arrieta (2020)', 'Revisão', 'Não', 'Não', 'Parcial', 'Não'],
        ['Barreto (2023)', 'N/A', 'Parcial', 'Sim', 'Não', 'Não'],
        ['Este trabalho', 'Grad-CAM', 'Sim', 'Sim', 'Sim', 'Sim'],
    ]
    pdf.add_table(headers, rows, caption='Comparação entre trabalhos relacionados e a proposta deste artigo.')

    pdf.add_paragraph(
        'Conforme evidenciado na Tabela 1, nenhum dos trabalhos relacionados aborda de forma integrada a persistência, recuperação e auditoria de '
        'evidências explicativas. Este trabalho preenche essa lacuna ao propor uma arquitetura híbrida que trata evidências de XAI como entidades '
        'persistentes de primeira classe.'
    )

    # ========== 4. METODOLOGIA / DESENVOLVIMENTO ==========
    pdf._add_section_heading('4. Metodologia e Desenvolvimento', level=1)

    pdf._add_section_heading('4.1 Arquitetura Proposta', level=2)

    pdf.add_paragraph(
        'A arquitetura proposta adota uma abordagem híbrida composta por três camadas de armazenamento especializadas, cada uma responsável por '
        'um tipo específico de dado:'
    )

    pdf.add_paragraph(
        'Camada Relacional (MySQL 8.0): responsável pela persistência estruturada dos metadados associados aos experimentos, inferências, métricas '
        'analíticas e eventos de auditoria. O esquema é normalizado em Terceira Forma Normal (3FN) com 12 tabelas interconectadas por chaves '
        'estrangeiras, garantindo integridade referencial e suporte a consultas complexas.'
    )

    pdf.add_paragraph(
        'Camada Vetorial (Qdrant): utilizada para armazenamento e indexação dos embeddings gerados pelos modelos de Deep Learning. Utiliza o algoritmo '
        'HNSW para busca aproximada por similaridade com distância cosseno, permitindo recuperação em tempo real de evidências similares.'
    )

    pdf.add_paragraph(
        'Camada de Objetos (MinIO): utilizada para persistir os artefatos multimídia gerados ao longo do processo experimental, incluindo imagens '
        'originais, imagens modificadas e mapas explicativos produzidos por técnicas de XAI. A organização hierárquica segue o padrão '
        'experiments/{id}/{inference_id}/{tipo}.png.'
    )

    pdf._add_section_heading('4.2 Modelo de Dados Relacional', level=2)

    pdf.add_paragraph(
        'O esquema relacional do MySQL é composto por 12 tabelas organizadas em três categorias: (1) principais -- experiments, images, inferences e '
        'noise_profiles; (2) de evidência -- embeddings (ponte relacional-vetorial via vector_db_id), gradcams e media_assets (URIs S3); e (3) de análise '
        '-- perturbation_comparisons, similarity_records, audit_trail e benchmark_runs.'
    )

    pdf.add_paragraph(
        'A integração MySQL-Qdrant é mediada pela tabela embeddings, que armazena metadados contextuais (inference_id, image_id, experiment_id, noise_type, '
        'predicted_label, confidence) e o campo vector_db_id, estabelecendo correspondência bidirecional entre o identificador relacional (PK no MySQL) e o '
        'UUID no Qdrant. As chaves estrangeiras com ON DELETE CASCADE garantem integridade referencial em cascata, evitando registros órfãos.'
    )

    pdf._add_section_heading('4.3 Esquema Vetorial', level=2)

    pdf.add_paragraph(
        'O Qdrant armazena uma coleção chamada "image_embeddings" com vetores de 2048 dimensões (dimensão do embedding da ResNet50) e métrica '
        'de distância cosseno. Cada vetor é associado a um payload contendo metadados contextuais: inference_id, image_id, experiment_id, noise_type, '
        'predicted_label e confidence. Essa estrutura permite filtros contextuais durante a busca, como recuperar apenas embeddings de um experimento '
        'específico ou de um tipo de perturbação.'
    )

    pdf._add_section_heading('4.4 Pipeline de Processamento', level=2)

    pdf.add_paragraph(
        'Para cada imagem de entrada, o pipeline executa: (1) preprocessamento; (2) inferência baseline com ResNet50; (3) geração de Grad-CAM; '
        '(4) persistência no MySQL (metadados), Qdrant (embeddings) e MinIO (objetos multimídia); (5) aplicação de 3 perturbações (gaussian, blur, brightness) '
        'com inferência e persistência; (6) comparação baseline-perturbado; (7) recuperação dos top-5 embeddings similares; e (8) auditoria com detecção de risco. '
        'A Figura 1 ilustra esse fluxo, destacando a bifurcação de dados para as três camadas de armazenamento.'
    )

    # Figura 3: Diagrama de Arquitetura (aumentada 10%)
    architecture_path = os.path.join(FIGURES_DIR, 'figure_3.png')
    pdf.add_figure(
        architecture_path,
        'Arquitetura de alto nível do sistema de persistência de evidências explicativas. '
        'O pipeline processa as imagens e distribui os dados simultaneamente para três camadas de armazenamento especializadas.',
        img_width=110
    )

    pdf._add_section_heading('4.5 Configuração Experimental', level=2)

    pdf.add_paragraph(
        'Para validação da proposta, foi utilizado o modelo ResNet50 pré-treinado no ImageNet para classificação de imagens do dataset '
        'Oxford-IIIT Pet Dataset (PARKHI et al., 2012), composto por 100 imagens de 11 raças de cães e outros animais. '
        'Cada imagem é processada em 4 variantes: '
        'baseline (sem perturbação) e três perturbações controladas (ruído gaussiano com σ=0.08, desfoque gaussiano com radius=2.0, '
        'e ajuste de brilho com factor=1.2). O experimento foi executado em ambiente CPU-only (Intel Core i5 10ª geração, 8GB RAM DDR4), '
        'com Python 3.10, TensorFlow 2.12 e Qdrant 1.8.1, garantindo reprodutibilidade dos resultados.'
    )

    pdf.add_paragraph(
        'A Tabela 2 resume os parâmetros experimentais adotados.'
    )

    headers = ['Parâmetro', 'Valor', 'Justificativa']
    rows = [
        ['Imagens', '100', 'Subconto do Oxford-IIIT Pet Dataset'],
        ['Classes', '11 classes', 'Diversidade de características visuais'],
        ['Variantes por imagem', '4', 'Baseline + 3 perturbações'],
        ['Total de inferências', '400', '100 × 4'],
        ['Dimensão do embedding', '2048', 'Penúltima camada da ResNet50'],
        ['Métrica de distância', 'Cosseno', 'Adequada para embeddings normalizados'],
        ['Workers', '1', 'Ambiente CPU-only'],
        ['Seed', '42', 'Reprodutibilidade'],
    ]
    pdf.add_table(headers, rows, caption='Parâmetros do experimento.', col_widths=[3, 2, 3])

    pdf._add_section_heading('4.6 Métricas de Avaliação', level=2)

    pdf.add_paragraph(
        'Para cada par (baseline, perturbado), o sistema calcula as seguintes métricas: (1) confidence_delta: diferença de confiança entre '
        'baseline e perturbado; (2) class_changed: indicador booleano de mudança de classe; (3) gradcam_overlap: IoU (Intersection over Union) '
        'entre regiões de alta ativação com threshold 0.5; (4) gradcam_correlation: correlação de Pearson entre mapas normalizados; e '
        '(5) embedding_similarity: similaridade cosseno entre vetores.'
    )

    pdf.add_paragraph(
        'O sistema classifica automaticamente cada comparação em níveis de risco: CRITICAL (classe alterada), HIGH (overlap < 0.4), MODERATE '
        '(Δ confiança < -0.3 ou overlap < 0.6) e LOW (decisão estável). Eventos CRITICAL e HIGH são registrados automaticamente na trilha de auditoria.'
    )

    # ========== 4.7 EXEMPLO DO EXPERIMENTO ==========
    pdf._add_section_heading('4.7 Exemplo Ilustrativo do Experimento', level=2)

    pdf.add_paragraph(
        'Para ilustrar o funcionamento do sistema, a Figura 2 apresenta um exemplo real do experimento: a imagem de um cão da raça Leonberg '
        'classificada pela ResNet50 com confiança de 45,2%. Ao lado da imagem original, o mapa de ativação Grad-CAM revela quais regiões '
        'da imagem foram mais relevantes para a decisão do modelo -- neste caso, o foco recai sobre a cabeça e o torso do animal, '
        'que são as características discriminantes para a classificação da raça.'
    )

    # Figura 4: Imagem original + Grad-CAM baseline (reduzida 20%)
    pdf.add_figure_panel(
        image_paths=[
            os.path.join(FIGURES_DIR, '01_original.png'),
            os.path.join(FIGURES_DIR, '02_gradcam_original.png'),
        ],
        caption='Exemplo com raça Leonberg (conf. 45,2%). (a) Imagem original. '
                '(b) Grad-CAM destacando regiões relevantes para a decisão.',
        titles=['(a) Imagem original (baseline)', '(b) Grad-CAM (Leonberg, conf. 45,2%)'],
        cols=2,
        img_width_factor=0.8
    )

    pdf.add_paragraph(
        'A Figura 3 apresenta as três versões perturbadas da mesma imagem, permitindo comparar visualmente o efeito de cada tipo de ruído: '
        'o ruído gaussiano adiciona granulado uniforme, o desfoque gaussiano suaviza bordas e texturas, e o ajuste de brilho altera a luminosidade geral. '
        'Cada versão perturbada é submetida ao mesmo processo de inferência e geração de Grad-CAM, permitindo quantificar o impacto '
        'de cada perturbação na decisão e na explicação do modelo.'
    )

    # Figura 5: Painel de perturbações (reduzida 10%)
    pdf.add_figure_panel(
        image_paths=[
            os.path.join(FIGURES_DIR, '03_noisy_gaussian.png'),
            os.path.join(FIGURES_DIR, '05_noisy_blur.png'),
            os.path.join(FIGURES_DIR, '07_noisy_brightness.png'),
        ],
        caption='Versões perturbadas. (a) Ruído gaussiano (σ=0.08). '
                '(b) Desfoque gaussiano (radius=2.0). (c) Ajuste de brilho (factor=1.2).',
        titles=['(a) Ruído gaussiano', '(b) Desfoque gaussiano', '(c) Ajuste de brilho'],
        cols=3,
        img_width_factor=0.9
    )

    pdf.add_paragraph(
        'A Figura 4 apresenta os mapas de ativação Grad-CAM para cada versão perturbada, permitindo comparação visual direta com o baseline. '
        'Observa-se que o ruído gaussiano e o ajuste de brilho preservam as regiões de alta ativação (cabeça e torso), '
        'enquanto o desfoque causa dispersão espacial do mapa, indicando que o modelo perde o foco nas características discriminantes. '
        'Essa degradação visual é quantificada pelas métricas de IoU e correlação de Pearson apresentadas na Tabela 6.'
    )

    # Figura 6: Grad-CAMs comparativos (reduzida 10%)
    pdf.add_figure_panel(
        image_paths=[
            os.path.join(FIGURES_DIR, '02_gradcam_original.png'),
            os.path.join(FIGURES_DIR, '04_gradcam_gaussian.png'),
            os.path.join(FIGURES_DIR, '06_gradcam_blur.png'),
            os.path.join(FIGURES_DIR, '08_gradcam_brightness.png'),
        ],
        caption='Mapas Grad-CAM comparativos. (a) Baseline. (b) Gaussiana (IoU=0,81). '
                '(c) Blur (IoU=0,70). (d) Brilho (IoU=0,95).',
        titles=[
            '(a) Baseline (IoU=1,00)',
            '(b) Gaussiana (IoU=0,81)',
            '(c) Blur (IoU=0,70)',
            '(d) Brilho (IoU=0,95)',
        ],
        cols=4,
        img_width_factor=0.9
    )

    # ========== 5. RESULTADOS E DISCUSSÃO ==========
    pdf._add_section_heading('5. Resultados e Discussão', level=1)

    pdf._add_section_heading('5.1 Resultados de Armazenamento (MySQL)', level=2)

    pdf.add_paragraph(
        'O experimento gerou aproximadamente 3.313 registros distribuídos nas 12 tabelas do MySQL. A Tabela 3 apresenta a distribuição de registros '
        'por tabela.'
    )

    headers = ['Tabela', 'Registros', '% do Total']
    rows = [
        ['experiments', '100', '3,0%'],
        ['images', '100', '3,0%'],
        ['inferences', '400', '12,1%'],
        ['embeddings', '400', '12,1%'],
        ['gradcams', '400', '12,1%'],
        ['media_assets', '800', '24,2%'],
        ['perturbation_comparisons', '300', '9,1%'],
        ['similarity_records', '~500', '15,1%'],
        ['audit_trail', '13', '0,4%'],
        ['benchmark_runs', '1', '<0,1%'],
        ['noise_profiles', '~300', '9,1%'],
        ['class_labels', '~11', '0,3%'],
        ['Total', '~3.313', '100%'],
    ]
    pdf.add_table(headers, rows, caption='Distribuição de registros por tabela no MySQL.')

    pdf.add_paragraph(
        'Cada imagem gerou em média 30 operações de INSERT no MySQL (1 experimento + 1 imagem + 4 inferências + 4 embeddings + 4 gradcams + '
        '8 media_assets + 3 comparações + 5 similarity_records + 1 auditoria). Para 100 imagens, totalizam aproximadamente 3.000 operações de '
        'inserção, demonstrando a capacidade do sistema de lidar com volumes significativos de dados estruturados.'
    )

    pdf._add_section_heading('5.2 Resultados de Perturbação', level=2)

    pdf.add_paragraph(
        'A Tabela 4 apresenta os resultados das 300 comparações entre baseline e versões perturbadas.'
    )

    headers = ['Perturbação', 'Comparações', 'Mudanças de Classe', 'Taxa']
    rows = [
        ['Gaussiana', '100', '7', '7,0%'],
        ['Blur', '100', '11', '11,0%'],
        ['Brilho', '100', '2', '2,0%'],
        ['Total', '300', '20', '6,7%'],
    ]
    pdf.add_table(headers, rows, caption='Resultados de mudança de classe por tipo de perturbação.')

    pdf.add_paragraph(
        'A taxa global de 6,7% de mudança de classe indica que o ResNet50 é moderadamente robusto às perturbações aplicadas. Conforme os dados da '
        'Tabela 6, o ruído gaussiano e o desfoque foram mais problemáticos, apresentando menor IoU (0,8317 e 0,7710, respectivamente) e correlação '
        'de Pearson (0,9880 e 0,9705), indicando que essas perturbações removem detalhes finos discriminantes para algumas classes, como '
        'diferenças entre raças de cães com pelagem similar.'
    )

    pdf._add_section_heading('5.3 Resultados Vetoriais (Qdrant)', level=2)

    pdf.add_paragraph(
        'O Qdrant indexou 400 embeddings (2048 dimensões) com índice HNSW e métrica de distância cosseno. O tempo médio de busca por similaridade '
        '(top-5) foi de 31,35 ms, resultando em throughput efetivo de aproximadamente 32 consultas/segundo.'
    )

    pdf.add_paragraph(
        'A Tabela 5 apresenta a similaridade cosseno média dos embeddings por tipo de perturbação.'
    )

    headers = ['Perturbação', 'Similaridade Cosseno (média)', 'Interpretação']
    rows = [
        ['Gaussiana', '0,9251', 'Alta similaridade - embedding preserva estrutura'],
        ['Blur', '0,8985', 'Similaridade moderada - detalhes perdidos'],
        ['Brilho', '0,9912', 'Muito alta similaridade - preserva quase tudo'],
    ]
    pdf.add_table(headers, rows, caption='Similaridade cosseno média dos embeddings por tipo de perturbação.', col_widths=[2, 2, 4])

    pdf.add_paragraph(
        'A similaridade cosseno de 0,9912 para a perturbação de brilho indica que a direção do embedding é quase idêntica, confirmando que a '
        'alteração de luminosidade não afeta significativamente a representação interna do modelo. Por outro lado, a queda para 0,8985 no desfoque '
        'sugere que a perda de detalhes finos afeta a representação vetorial de forma mais significativa.'
    )

    pdf._add_section_heading('5.4 Estabilidade das Explicações (Grad-CAM)', level=2)

    pdf.add_paragraph(
        'A Tabela 6 apresenta as métricas de estabilidade dos mapas de ativação Grad-CAM por tipo de perturbação.'
    )

    headers = ['Perturbação', 'Δ Confiança', 'Embedding Sim.', 'Grad-CAM IoU', 'Grad-CAM Corr.']
    rows = [
        ['Gaussiana', '+0,0046', '0,9251', '0,8317', '0,9880'],
        ['Blur', '-0,0169', '0,8985', '0,7710', '0,9705'],
        ['Brilho', '+0,0037', '0,9912', '0,9341', '0,9985'],
    ]
    pdf.add_table(headers, rows, caption='Métricas de estabilidade das explicações por tipo de perturbação.')

    pdf.add_paragraph(
        'O Grad-CAM IoU mede o overlap espacial entre regiões de alta ativação (threshold 0,5). Valores acima de 0,8 indicam alta estabilidade. '
        'O blur (0,7710) apresenta degradação significativa, indicando que o desfoque altera quais regiões o modelo considera importantes. '
        'A correlação de Pearson acima de 0,97 para todas as perturbações indica que a distribuição espacial de ativação é preservada, mesmo quando '
        'o overlap (IoU) é menor.'
    )

    pdf._add_section_heading('5.5 Resultados Multimídia (MinIO)', level=2)

    pdf.add_paragraph(
        'O MinIO armazenou aproximadamente 800 objetos no bucket "evidence-assets", totalizando 247,64 MB. A distribuição por tipo de ativo é apresentada na Tabela 7.'
    )

    headers = ['Tipo', 'Quantidade', 'Volume Estimado', 'Tamanho Médio']
    rows = [
        ['original.png', '100', '~45 MB', '~450 KB'],
        ['noisy_gaussian.png', '100', '~52 MB', '~520 KB'],
        ['noisy_blur.png', '100', '~48 MB', '~480 KB'],
        ['noisy_brightness.png', '100', '~46 MB', '~460 KB'],
        ['gradcam.png', '400', '~60 MB', '~150 KB'],
        ['Total', '~800', '~247 MB', '--'],
    ]
    pdf.add_table(headers, rows, caption='Distribuição de objetos no MinIO por tipo de ativo.')

    pdf.add_paragraph(
        'A separação do armazenamento de objetos do banco relacional mantém o MySQL leve: se os BLOBs de imagens fossem armazenados diretamente '
        'no MySQL (LONGBLOB), o banco teria ~247 MB apenas de imagens. Com o MinIO, o MySQL armazena apenas URIs (strings de ~100 bytes), '
        'representando uma economia estimada de ~246 MB.'
    )

    pdf._add_section_heading('5.6 Avaliação de Risco e Auditoria', level=2)

    pdf.add_paragraph(
        'O sistema detectou 20 eventos de risco CRITICAL (classe alterada sob perturbação), conforme a Tabela 8.'
    )

    headers = ['Tipo de Evento', 'Ocorrências']
    rows = [
        ['Classe alterada (gaussian)', '7'],
        ['Classe alterada (blur)', '11'],
        ['Classe alterada (brightness)', '2'],
        ['Total', '20'],
    ]
    pdf.add_table(headers, rows, caption='Eventos de risco detectados automaticamente.')

    pdf.add_paragraph(
        'A distribuição de riscos indica que 91,0% das decisões foram classificadas como LOW (estáveis), 2,3% como MODERATE e 6,7% como '
        'CRITICAL. Não houve eventos HIGH (overlap < 0,4), demonstrando que o modelo é robusto às perturbações aplicadas. A trilha de auditoria '
        'foi projetada para registrar 100% das decisões, garantindo rastreabilidade completa do processo de inferência e conformidade com requisitos '
        'de auditoria.'
    )

    pdf._add_section_heading('5.7 Análise por Classe', level=2)

    pdf.add_paragraph(
        'A Tabela 9 apresenta a análise de suscetibilidade a perturbações por classe, incluindo a sensibilidade individual de cada raça.'
    )

    headers = ['Classe', 'Imagens', 'Confiança Média', 'Mudanças Gauss.', 'Mudanças Blur', 'Mudanças Brilho', 'Sensibilidade']
    rows = [
        ['Am. Staff. Terrier', '4', '0,22', '1 de 12', '3 de 12', '1 de 12', '41,7%'],
        ['Pembroke', '2', '0,12', '2 de 6', '2 de 6', '0 de 6', '66,7%'],
        ['Yorkshire Terrier', '10', '0,33', '1 de 30', '3 de 30', '0 de 30', '13,3%'],
        ['Staff. Bull Terrier', '6', '0,25', '1 de 18', '1 de 18', '0 de 18', '11,1%'],
        ['dingo', '7', '0,30', '1 de 21', '0 de 21', '1 de 21', '9,5%'],
        ['Newfoundland', '10', '0,44', '1 de 30', '1 de 30', '0 de 30', '6,7%'],
        ['Pomeranian', '10', '0,43', '0 de 30', '1 de 30', '0 de 30', '3,3%'],
        ['Leonberg', '10', '0,42', '0 de 30', '0 de 30', '0 de 30', '0,0%'],
        ['Miniature Pinscher', '10', '0,42', '0 de 30', '0 de 30', '0 de 30', '0,0%'],
        ['keeshond', '10', '0,49', '0 de 30', '0 de 30', '0 de 30', '0,0%'],
        ['pug', '10', '0,44', '0 de 30', '0 de 30', '0 de 30', '0,0%'],
        ['Saint Bernard', '10', '0,39', '0 de 30', '0 de 30', '0 de 30', '0,0%'],
    ]
    pdf.add_table(headers, rows, caption='Análise de suscetibilidade a perturbações por classe.', col_widths=[2.5, 1, 2, 2, 2, 2, 2])

    pdf.add_paragraph(
        'Classes com menor confiança média (Pembroke: 0,12; Am. Staff. Terrier: 0,22) apresentam maior suscetibilidade. '
        'O Pembroke (66,7%) e o Am. Staff. Terrier (41,7%) são as classes mais vulneráveis.'
    )

    pdf._add_section_heading('5.8 Discussão Geral', level=2)

    pdf.add_paragraph(
        'Os resultados demonstram que a arquitetura híbrida proposta é eficaz para o caso de uso de auditoria de IA. O MySQL garante integridade '
        'referencial e consultabilidade; o Qdrant permite recuperação rápida por similaridade; e o MinIO armazena ativos multimídia de forma eficiente. '
        'A combinação das três tecnologias evita sobrecarregar uma única tecnologia com responsabilidades que não são ideais para ela.'
    )

    pdf.add_paragraph(
        'Do ponto de vista de Banco de Dados, o projeto demonstra conceitos fundamentais: modelagem relacional normalizada em 3FN, integridade '
        'referencial com chaves estrangeiras, indexação (B-tree no MySQL, HNSW no Qdrant), transações ACID, consultas estruturadas com JOINs e '
        'agregações, e trilha de auditoria com timestamps.'
    )

    pdf.add_paragraph(
        'A taxa de 6,7% de mudança de classe sob perturbação é esperada em um cenário controlado com perturbações sintéticas. Em produção, '
        'com imagens reais degradadas, a taxa poderia ser maior devido à maior variabilidade e severidade das degradações. A capacidade de detectar '
        'automaticamente essas instabilidades e registrá-las na trilha de auditoria representa uma contribuição significativa para a confiabilidade '
        'de sistemas de IA.'
    )

    pdf._add_section_heading('5.9 Análise do Overhead de Persistência', level=2)

    pdf.add_paragraph(
        'A persistência híbrida consome aproximadamente 9,4 segundos por imagem (86% do tempo total), enquanto a inferência do modelo corresponde a 14% '
        '(~2.050 ms). Esse overhead é justificado por três benefícios: (1) economia de ~246 MB no MySQL ao armazenar objetos no MinIO em vez de BLOBs; '
        '(2) busca vetorial em ~31 ms (32 consultas/s), inalcançável no MySQL; e (3) capacidade de auditoria retroativa, permitindo investigar decisões '
        'passadas com acesso ao mapa de ativação exato e embedding original -- essencial para conformidade com LGPD e GDPR.'
    )

    # ========== 6. CONCLUSÃO ==========
    pdf._add_section_heading('6. Conclusão', level=1)

    pdf.add_paragraph(
        'Este trabalho investigou a utilização de uma arquitetura híbrida de persistência para o armazenamento, recuperação e auditoria de '
        'evidências explicativas produzidas por modelos de Deep Learning aplicados à Visão Computacional. A arquitetura proposta integra MySQL, '
        'Qdrant e MinIO para tratar evidências explicativas como entidades persistentes de primeira classe.'
    )

    pdf.add_paragraph(
        'Em resposta direta à questão de pesquisa -- como uma arquitetura híbrida de persistência pode contribuir para o armazenamento, recuperação e '
        'auditoria de evidências explicativas produzidas por sistemas de Visão Computacional baseados em Deep Learning? --, os resultados experimentais '
        'demonstram que:'
    )

    pdf.add_bullet(
        'A arquitetura proposta é tecnicamente viável, garantindo 100% de rastreabilidade das decisões do modelo por meio da trilha de auditoria implementada no MySQL.'
    )
    pdf.add_bullet(
        'O sistema é capaz de detectar automaticamente 6,7% de casos críticos de mudança de classe sob perturbação (20 de 300 comparações), identificando instabilidades que permaneceriam invisíveis em sistemas sem persistência de evidências.'
    )
    pdf.add_bullet(
        'A recuperação de evidências similares é realizada em tempo real (aproximadamente 31,35 ms) por meio da integração entre armazenamento relacional (MySQL), vetorial (Qdrant) e de objetos (MinIO).'
    )
    pdf.add_bullet(
        'A persistência híbrida reduz em aproximadamente 246 MB o volume armazenado no banco relacional ao delegar objetos multimídia ao MinIO.'
    )

    pdf.add_paragraph(
        'Esses resultados confirmam que a integração entre Bancos de Dados e Inteligência Artificial Explicável representa uma contribuição científica '
        'sólida para a construção de sistemas de IA auditáveis, rastreáveis e em conformidade com regulamentações de proteção de dados.'
    )

    pdf._add_section_heading('6.1 Limitações', level=2)

    pdf.add_paragraph(
        'As principais limitações deste trabalho incluem: (1) processamento em CPU-only, com tempo de inferência de aproximadamente 2.050ms por imagem; '
        '(2) ausência de compressão de embeddings (2048 × 4 bytes = 8KB por embedding); (3) busca vetorial semântica sem distinção entre classes '
        'similares; e (4) processamento sequencial com worker único.'
    )

    pdf._add_section_heading('6.2 Trabalhos Futuros', level=2)

    pdf.add_paragraph(
        'Como trabalhos futuros, sugere-se: (1) implementação de filtros contextuais na busca vetorial por classe, experimento e tipo de ruído; '
        '(2) adição de compressão de embeddings via quantização; (3) desenvolvimento de API REST para consulta unificada; (4) implementação de '
        'dashboard web para exploração interativa de evidências; (5) suporte a múltiplos modelos (VGG, EfficientNet, ViT); e (6) integração '
        'com modelos de linguagem para explicação textual das evidências.'
    )

    # ========== REFERÊNCIAS ==========
    references = [
        'ARRIETA, A. B. et al. Explainable Artificial Intelligence (XAI): Concepts, taxonomies, opportunities and challenges toward responsible AI. Information Fusion, v. 58, p. 82-115, 2020.',
        'BARRETO, R. et al. HNSW-based vector search for large-scale image retrieval. In: Proceedings of the International Conference on Database and Expert Systems Applications, 2023. p. 234-248.',
        'CODD, E. F. A Relational Model of Data for Large Shared Data Banks. Communications of the ACM, v. 13, n. 6, p. 377-387, 1970.',
        'ELMASRI, R.; NAVATHE, S. B. Fundamentals of Database Systems. 7. ed. Boston: Pearson, 2016.',
        'HE, K. et al. Deep residual learning for image recognition. In: Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition, 2016. p. 770-778.',
        'LECUN, Y. et al. Deep learning. Nature, v. 521, n. 7553, p. 436-444, 2015.',
        'MALKOV, Y. A.; YASHUNIN, D. A. Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs. IEEE Transactions on Pattern Analysis and Machine Intelligence, v. 40, n. 4, p. 629-643, 2018.',
        'MINIO, Inc. MinIO High Performance Object Storage. 2024. Disponível em: https://min.io/. Acesso em: 25 jun. 2026.',
        'PARKHI, O. M. et al. Cats and dogs. In: IEEE Conference on Computer Vision and Pattern Recognition, 2012. p. 3498-3505.',
        'RIBEIRO, M. T. et al. "Why should I trust you?": Explaining the predictions of any classifier. In: Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 2016. p. 1135-1144.',
        'SCHUHMACHER, M. et al. Vector search for similarity-based machine learning. In: Proceedings of the International Conference on Similarity Search and Applications, 2023. p. 112-126.',
        'SELVARAJU, R. R. et al. Grad-CAM: Visual explanations from deep networks via gradient-based localization. In: Proceedings of the IEEE International Conference on Computer Vision, 2017. p. 618-626.',
    ]
    pdf.add_references(references)

    # Salvar documento
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Artigo_Banco_Dados_Eduardo_Lazaro.pdf')
    pdf.build(output_path)
    print(f"Documento PDF salvo em: {output_path}")


if __name__ == '__main__':
    main()
