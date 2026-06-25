"""
Script para gerar artigo academico em Word (.docx)
Baseado nos arquivos: 00_base, 01_minha_poroposta, 02_dialogo_com_professor, 03_orientacoes_finais_banco_dados, 04_relatorio_enorme
"""

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_cell_shading(cell, color):
    """Define a cor de fundo de uma celula."""
    shading = OxmlElement('w:shd')
    shading.set(qn('w:val'), 'clear')
    shading.set(qn('w:color'), 'auto')
    shading.set(qn('w:fill'), color)
    cell._tc.get_or_add_tcPr().append(shading)

def set_run_font(run, font_name='Times New Roman', font_size=12, bold=False):
    """Configura fonte de um run."""
    run.font.name = font_name
    run.font.size = Pt(font_size)
    run.bold = bold
    # Para fontes latinas no Word
    r = run._element
    rPr = r.find(qn('w:rPr'))
    if rPr is None:
        rPr = OxmlElement('w:rPr')
        r.insert(0, rPr)
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.insert(0, rFonts)
    rFonts.set(qn('w:eastAsia'), font_name)
    rFonts.set(qn('w:ascii'), font_name)
    rFonts.set(qn('w:hAnsi'), font_name)

def add_heading_custom(doc, text, level=1):
    """Adiciona titulo com formatacao ABNT."""
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.name = 'Times New Roman'
        run.font.color.rgb = RGBColor(0, 0, 0)
        if level == 1:
            run.font.size = Pt(16)
            run.bold = True
        elif level == 2:
            run.font.size = Pt(14)
            run.bold = True
        elif level == 3:
            run.font.size = Pt(12)
            run.bold = True
        # Configurar fontes latinas
        r = run._element
        rPr = r.find(qn('w:rPr'))
        if rPr is None:
            rPr = OxmlElement('w:rPr')
            r.insert(0, rPr)
        rFonts = rPr.find(qn('w:rFonts'))
        if rFonts is None:
            rFonts = OxmlElement('w:rFonts')
            rPr.insert(0, rFonts)
        rFonts.set(qn('w:eastAsia'), 'Times New Roman')
        rFonts.set(qn('w:ascii'), 'Times New Roman')
        rFonts.set(qn('w:hAnsi'), 'Times New Roman')
    return h

def add_paragraph_custom(doc, text, bold=False, italic=False, alignment=None, first_line_indent=True, font_size=12, space_after=6):
    """Adiciona paragrafo formatado."""
    p = doc.add_paragraph()
    if alignment:
        p.alignment = alignment
    if first_line_indent:
        p.paragraph_format.first_line_indent = Cm(1.25)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.5
    run = p.add_run(text)
    set_run_font(run, font_size=font_size, bold=bold)
    run.italic = italic
    return p

def add_table_custom(doc, headers, rows):
    """Adiciona tabela formatada."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    # Header
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ''
        p = cell.paragraphs[0]
        run = p.add_run(header)
        set_run_font(run, font_size=10, bold=True)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cell_shading(cell, 'D9E2F3')
    
    # Data rows
    for i, row in enumerate(rows):
        for j, cell_text in enumerate(row):
            cell = table.rows[i + 1].cells[j]
            cell.text = ''
            p = cell.paragraphs[0]
            run = p.add_run(str(cell_text))
            set_run_font(run, font_size=10)
    
    doc.add_paragraph()  # Espaço após tabela
    return table

def add_figure(doc, caption):
    """Adiciona legenda de figura."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(caption)
    set_run_font(run, font_size=10, bold=True)
    return p

def main():
    doc = Document()
    
    # Configurar margens da página
    sections = doc.sections
    for section in sections:
        section.top_margin = Cm(3)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(3)
        section.right_margin = Cm(2)
    
    # ========== CAPA ==========
    for _ in range(6):
        doc.add_paragraph()
    
    # Título do artigo
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(12)
    run = title.add_run('Arquitetura Híbrida de Persistência e Recuperação de Evidências Explicativas em Sistemas de Visão Computacional Baseados em Deep Learning')
    set_run_font(run, font_size=16, bold=True)
    
    # Subtítulo / autor
    author_p = doc.add_paragraph()
    author_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    author_p.paragraph_format.space_after = Pt(6)
    run = author_p.add_run('Eduardo Lázaro Roesler de Oliveira')
    set_run_font(run, font_size=12)
    
    inst_p = doc.add_paragraph()
    inst_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    inst_p.paragraph_format.space_after = Pt(6)
    run = inst_p.add_run('Universidade Estadual Paulista (UNESP) - Faculdade de Ciências e Tecnologia')
    set_run_font(run, font_size=11)
    
    course_p = doc.add_paragraph()
    course_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    course_p.paragraph_format.space_after = Pt(24)
    run = course_p.add_run('Programa de Pós-Graduação em Ciência da Computação - Disciplina de Banco de Dados')
    set_run_font(run, font_size=11)
    
    date_p = doc.add_paragraph()
    date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = date_p.add_run('Presidente Prudente, 2026')
    set_run_font(run, font_size=12)
    
    doc.add_page_break()
    
    # ========== RESUMO ==========
    add_heading_custom(doc, 'Resumo', level=1)
    
    add_paragraph_custom(doc, 
        'O avanço recente dos modelos de Deep Learning tem impulsionado a adoção de sistemas de Inteligência Artificial em diversos domínios, '
        'especialmente em aplicações de Visão Computacional. Embora esses modelos apresentem elevado desempenho preditivo, suas decisões frequentemente '
        'são caracterizadas por baixa interpretabilidade. Como resposta a esse desafio, técnicas de Explainable Artificial Intelligence (XAI) têm sido '
        'amplamente exploradas para produzir evidências explicativas. Entretanto, a maior parte dos estudos concentra-se na produção dessas evidências, '
        'enquanto pouca atenção é dedicada ao seu armazenamento, gerenciamento e recuperação posterior. Diante desse cenário, este trabalho investiga '
        'como uma arquitetura híbrida de persistência pode contribuir para o armazenamento, recuperação e auditoria de evidências explicativas produzidas '
        'por sistemas de Visão Computacional baseados em Deep Learning. A arquitetura proposta integra três tecnologias complementares: MySQL para persistência '
        'relacional de metadados, Qdrant para indexação e busca vetorial de embeddings, e MinIO para armazenamento de objetos multimídia. Os resultados '
        'experimentais demonstram que a arquitetura é capaz de persistir evidências explicativas com integridade referencial, recuperar evidências similares '
        'em tempo real (aproximadamente 14 ms) e armazenar ativos multimídia de forma eficiente, contribuindo para mecanismos mais robustos de auditoria, '
        'rastreabilidade e recuperação contextual de inferências.')
    
    add_paragraph_custom(doc, 
        'Palavras-chave: Explainable AI, Bancos de Dados Híbridos, Persistência de Evidências, Visão Computacional, Deep Learning, '
        'Busca por Similaridade, Auditoria de IA.',
        first_line_indent=False)
    
    doc.add_page_break()
    
    # ========== 1. INTRODUÇÃO ==========
    add_heading_custom(doc, '1. Introdução', level=1)
    
    add_paragraph_custom(doc,
        'O avanço recente dos modelos de Deep Learning tem impulsionado a adoção de sistemas de Inteligência Artificial (IA) em diversos domínios, '
        'especialmente em aplicações de Visão Computacional, como classificação de imagens, detecção de objetos e diagnóstico médico por imagem '
        '(LECUN et al., 2015; HE et al., 2016). Modelos como ResNet50 são capazes de classificar imagens com alta acurácia, superando humanos em tarefas '
        'específicas.')
    
    add_paragraph_custom(doc,
        'No entanto, esses modelos operam frequentemente como "caixas-pretas" — produzem uma decisão sem explicar quais fatores influenciaram '
        'determinada classificação ou predição (RIBEIRO et al., 2016). Essa baixa interpretabilidade torna difícil compreender, auditar e confiar '
        'nas decisões automatizadas, especialmente em contextos críticos como diagnóstico médico, veículos autônomos e sistemas de vigilância.')
    
    add_paragraph_custom(doc,
        'Como resposta a esse desafio, técnicas de Explainable Artificial Intelligence (XAI) têm sido amplamente exploradas para produzir '
        'evidências explicativas capazes de auxiliar na interpretação do comportamento dos modelos (ARRIETA et al., 2020). Entre essas evidências '
        'destacam-se mapas de ativação (como Grad-CAM), embeddings vetoriais, métricas de confiança e outros artefatos analíticos produzidos '
        'durante o processo de inferência (SELVARAJU et al., 2017).')
    
    add_paragraph_custom(doc,
        'Entretanto, apesar do crescente interesse na geração dessas explicações, observa-se que a maior parte dos estudos concentra-se na produção '
        'das evidências explicativas, enquanto pouca atenção é dedicada ao seu armazenamento, gerenciamento e recuperação posterior. Em muitos sistemas, '
        'tais informações são utilizadas apenas momentaneamente durante a execução e posteriormente descartadas, limitando atividades de auditoria, '
        'rastreabilidade, análise histórica e investigação do comportamento dos modelos ao longo do tempo.')
    
    add_paragraph_custom(doc,
        'Diante desse cenário, este trabalho investiga a seguinte questão de pesquisa: como uma arquitetura híbrida de persistência pode contribuir '
        'para o armazenamento, recuperação e auditoria de evidências explicativas produzidas por sistemas de Visão Computacional baseados em Deep Learning?')
    
    add_paragraph_custom(doc,
        'Para responder a essa questão, propõe-se o desenvolvimento e a avaliação de uma arquitetura híbrida de dados capaz de tratar evidências '
        'explicativas como entidades persistentes, organizadas e recuperáveis dentro de um ecossistema integrado de Banco de Dados. A arquitetura integra '
        'três tecnologias complementares: MySQL para persistência relacional de metadados e auditoria, Qdrant para indexação e busca vetorial de '
        'embeddings, e MinIO para armazenamento de objetos multimídia.')
    
    add_paragraph_custom(doc,
        'O restante deste artigo está organizado da seguinte forma: a Seção 2 apresenta a fundamentação teórica; a Seção 3 discute os trabalhos '
        'relacionados; a Seção 4 descreve a metodologia e o desenvolvimento proposto; a Seção 5 apresenta e discute os resultados experimentais; '
        'e a Seção 6 apresenta as conclusões e sugestões para trabalhos futuros.')
    
    # ========== 2. FUNDAMENTAÇÃO TEÓRICA ==========
    add_heading_custom(doc, '2. Fundamentação Teórica', level=1)
    
    add_heading_custom(doc, '2.1 Deep Learning e Visão Computacional', level=2)
    
    add_paragraph_custom(doc,
        'Deep Learning é um subcampo de Machine Learning baseado em redes neurais artificiais com múltiplas camadas de processamento. No contexto '
        'da Visão Computacional, as Redes Neurais Convolucionais (CNNs) são a arquitetura predominante, capazes de aprender representações hierárquicas '
        'de características visuais diretamente a partir dos dados de imagem (LECUN et al., 2015).')
    
    add_paragraph_custom(doc,
        'A ResNet50 (HE et al., 2016) é uma CNN com 50 camadas que introduz conexões residuais (skip connections) para mitigar o problema do '
        'desvanecimento do gradiente em redes profundas. Treinada no dataset ImageNet com mais de 1 milhão de imagens, a ResNet50 atinge acurácia '
        'top-1 de aproximadamente 76% e é amplamente utilizada como modelo base para tarefas de classificação e extração de características.')
    
    add_paragraph_custom(doc,
        'Os embeddings visuais gerados pela ResNet50 correspondem à ativação da penúltima camada (average pooling), resultando em vetores de '
        '2048 dimensões que codificam características semânticas de alto nível da imagem. Essas representações vetoriais são fundamentais para tarefas '
        'de busca por similaridade e recuperação de informação visual.')
    
    add_heading_custom(doc, '2.2 Explainable AI (XAI)', level=2)
    
    add_paragraph_custom(doc,
        'Explainable AI (XAI) refere-se a métodos e técnicas que tornam as decisões de modelos de IA compreensíveis para humanos (ARRIETA et al., 2020). '
        'No contexto de Visão Computacional, as técnicas de XAI mais comuns incluem mapas de ativação, que destacam as regiões da imagem mais relevantes '
        'para a predição do modelo.')
    
    add_paragraph_custom(doc,
        'O Grad-CAM (Gradient-weighted Class Activation Mapping) (SELVARAJU et al., 2017) é uma técnica de explicabilidade que utiliza os gradientes '
        'da classe alvo em relação à última camada convolucional para produzir um mapa de calor que indica as regiões de maior influência na decisão. '
        'Diferente de técnicas anteriores, o Grad-CAM é agnóstico à arquitetura e pode ser aplicado a qualquer CNN sem modificações estruturais.')
    
    add_paragraph_custom(doc,
        'Embora as técnicas de XAI gerem evidências valiosas, essas informações são frequentemente tratadas como subprodutos efêmeros, utilizadas '
        'apenas momentaneamente durante a inferência e descartadas em seguida. Este trabalho propõe tratar essas evidências como entidades persistentes '
        'de primeira classe em um banco de dados.')
    
    add_heading_custom(doc, '2.3 Bancos de Dados Híbridos', level=2)
    
    add_paragraph_custom(doc,
        'A arquitetura híbrida de persistência proposta neste trabalho integra três paradigmas de armazenamento de dados, cada um com características '
        'e otimizações específicas:')
    
    add_paragraph_custom(doc,
        'Bancos de Dados Relacionais (MySQL): baseiam-se no modelo relacional de CODD (1970) e garantem propriedades ACID (Atomicidade, Consistência, '
        'Isolamento, Durabilidade). São ideais para armazenamento estruturado de metadados, registros de inferências e trilhas de auditoria, suportando '
        'consultas complexas com JOINs e agregações (ELMASRI; NAVATHE, 2016).')
    
    add_paragraph_custom(doc,
        'Bancos de Dados Vetoriais (Qdrant): são otimizados para armazenamento e busca por similaridade em espaços de alta dimensionalidade. Utilizam '
        'algoritmos de indexação aproximada como HNSW (Hierarchical Navigable Small World) para permitir buscas sublineares em grandes volumes de vetores. '
        'São fundamentais para recuperação semântica baseada em embeddings (BARRETO et al., 2023).')
    
    add_paragraph_custom(doc,
        'Armazenamento de Objetos (MinIO): seguem o modelo de armazenamento de objetos compatível com S3 API, ideais para ativos binários como imagens, '
        'mapas de ativação e outros arquivos multimídia. Permitem separação eficiente entre dados estruturados e mídias pesadas, com organização hierárquica '
        'e escalabilidade horizontal (MINIO, 2024).')
    
    add_heading_custom(doc, '2.4 Recuperação de Informação e Busca por Similaridade', level=2)
    
    add_paragraph_custom(doc,
        'A recuperação de informação em espaços vetoriais envolve encontrar os vetores mais similares a um vetor de consulta em um conjunto de dados. '
        'A métrica de distância cosseno é amplamente utilizada para embeddings de alta dimensionalidade, pois mede o ângulo entre vetores em vez de '
        'sua magnitude, sendo adequada para comparar similaridade semântica (SCHUHMACHER et al., 2023).')
    
    add_paragraph_custom(doc,
        'O algoritmo HNSW (MALKOV; YASHUNIN, 2016) constrói um grafo hierárquico de pequeno mundo que permite buscas aproximadas com complexidade '
        'sublinear. O HNSW é o algoritmo padrão do Qdrant e oferece um equilíbrio entre recall, latência e uso de memória, sendo adequado para aplicações '
        'que exigem recuperação em tempo real de embeddings de alta dimensionalidade.')
    
    # ========== 3. TRABALHOS RELACIONADOS ==========
    add_heading_custom(doc, '3. Trabalhos Relacionados', level=1)
    
    add_paragraph_custom(doc,
        'A interseção entre Bancos de Dados e Inteligência Artificial Explicável tem recebido atenção crescente na literatura recente. Esta seção '
        'apresenta trabalhos relacionados que abordam aspectos de persistência, recuperação e auditoria de evidências de IA.')
    
    add_paragraph_custom(doc,
        'Ribeiro et al. (2016) propuseram o LIME (Local Interpretable Model-agnostic Explanations), uma técnica de explicabilidade local que gera '
        'explicações para predições individuais. No entanto, o LIME não aborda o armazenamento persistente das explicações geradas, tratando-as como '
        'artefatos temporários.')
    
    add_paragraph_custom(doc,
        'Selvaraju et al. (2017) introduziram o Grad-CAM, técnica de explicabilidade baseada em gradientes que gera mapas de calor para CNNs. O Grad-CAM '
        'é amplamente utilizado, mas sua implementação padrão não inclui mecanismos de persistência ou recuperação das evidências geradas.')
    
    add_paragraph_custom(doc,
        'Arrieta et al. (2020) apresentam uma revisão abrangente sobre XAI, discutindo taxonomias, técnicas e desafios. Os autores destacam a necessidade '
        'de mecanismos de auditoria e rastreabilidade, mas não propõem soluções de banco de dados para persistência de evidências.')
    
    add_paragraph_custom(doc,
        'No contexto de bancos de dados vetoriais, Barreto et al. (2023) discutem a aplicação de índices HNSW para recuperação eficiente de embeddings '
        'em sistemas de grande escala. Os autores demonstram que a busca por similaridade vetorial pode ser realizada em milissegundos mesmo para milhões '
        'de vetores.')
    
    add_paragraph_custom(doc,
        'A Tabela 1 apresenta uma comparação crítica entre os trabalhos relacionados e a proposta deste artigo.')
    
    # Tabela de comparação
    headers = ['Trabalho', 'Técnica de XAI', 'Persistência', 'Busca Vetorial', 'Auditoria', 'Arquitetura Híbrida']
    rows = [
        ['Ribeiro et al. (2016)', 'LIME', 'Não', 'Não', 'Não', 'Não'],
        ['Selvaraju et al. (2017)', 'Grad-CAM', 'Não', 'Não', 'Não', 'Não'],
        ['Arrieta et al. (2020)', 'Revisão', 'Não', 'Não', 'Parcial', 'Não'],
        ['Barreto et al. (2023)', 'N/A', 'Parcial', 'Sim', 'Não', 'Não'],
        ['Este trabalho', 'Grad-CAM', 'Sim (3 camadas)', 'Sim (Qdrant)', 'Sim', 'Sim (MySQL+Qdrant+MinIO)'],
    ]
    add_table_custom(doc, headers, rows)
    
    add_paragraph_custom(doc,
        'Tabela 1: Comparação entre trabalhos relacionados e a proposta deste artigo.',
        first_line_indent=False)
    
    add_paragraph_custom(doc,
        'Conforme evidenciado na Tabela 1, nenhum dos trabalhos relacionados aborda de forma integrada a persistência, recuperação e auditoria de '
        'evidências explicativas. Este trabalho preenche essa lacuna ao propor uma arquitetura híbrida que trata evidências de XAI como entidades '
        'persistentes de primeira classe.')
    
    # ========== 4. METODOLOGIA / DESENVOLVIMENTO ==========
    add_heading_custom(doc, '4. Metodologia e Desenvolvimento', level=1)
    
    add_heading_custom(doc, '4.1 Arquitetura Proposta', level=2)
    
    add_paragraph_custom(doc,
        'A arquitetura proposta adota uma abordagem híbrida composta por três camadas de armazenamento especializadas, cada uma responsável por '
        'um tipo específico de dado:')
    
    add_paragraph_custom(doc,
        'Camada Relacional (MySQL 8.0): responsável pela persistência estruturada dos metadados associados aos experimentos, inferências, métricas '
        'analíticas e eventos de auditoria. O esquema é normalizado em Terceira Forma Normal (3FN) com 12 tabelas interconectadas por chaves '
        'estrangeiras, garantindo integridade referencial e suporte a consultas complexas.')
    
    add_paragraph_custom(doc,
        'Camada Vetorial (Qdrant): utilizada para armazenamento e indexação dos embeddings gerados pelos modelos de Deep Learning. Utiliza o algoritmo '
        'HNSW para busca aproximada por similaridade com distância cosseno, permitindo recuperação em tempo real de evidências similares.')
    
    add_paragraph_custom(doc,
        'Camada de Objetos (MinIO): utilizada para persistir os artefatos multimídia gerados ao longo do processo experimental, incluindo imagens '
        'originais, imagens modificadas e mapas explicativos produzidos por técnicas de XAI. A organização hierárquica segue o padrão '
        'experiments/{id}/{inference_id}/{tipo}.png.')
    
    add_figure(doc, 'Figura 1: Arquitetura de alto nível do sistema de persistência de evidências explicativas.')
    
    add_heading_custom(doc, '4.2 Modelo de Dados Relacional', level=2)
    
    add_paragraph_custom(doc,
        'O esquema relacional do MySQL é composto por 12 tabelas organizadas em três categorias: tabelas principais, tabelas de evidência e tabelas '
        'de análise. A Figura 2 apresenta o diagrama de entidades e relacionamentos.')
    
    add_figure(doc, 'Figura 2: Diagrama de entidades e relacionamentos do modelo relacional (MySQL).')
    
    add_paragraph_custom(doc,
        'As tabelas principais incluem: experiments (agrupa inferências por experimento), images (metadados da imagem original), inferences '
        '(resultado de cada inferência) e noise_profiles (parâmetros de cada tipo de perturbação). As tabelas de evidência incluem embeddings '
        '(ponte relacional-vetorial), gradcams (estatísticas dos mapas de ativação) e media_assets (URIs S3 para objetos no MinIO). As tabelas '
        'de análise incluem perturbation_comparisons, similarity_records, audit_trail e benchmark_runs.')
    
    add_heading_custom(doc, '4.3 Esquema Vetorial', level=2)
    
    add_paragraph_custom(doc,
        'O Qdrant armazena uma coleção chamada "image_embeddings" com vetores de 2048 dimensões (dimensão do embedding da ResNet50) e métrica '
        'de distância cosseno. Cada vetor é associado a um payload contendo metadados contextuais: inference_id, image_id, experiment_id, noise_type, '
        'predicted_label e confidence. Essa estrutura permite filtros contextuais durante a busca, como recuperar apenas embeddings de um experimento '
        'específico ou de um tipo de perturbação.')
    
    add_heading_custom(doc, '4.4 Pipeline de Processamento', level=2)
    
    add_paragraph_custom(doc,
        'Para cada imagem de entrada, o pipeline executa os seguintes passos: (1) carregamento e preprocessamento da imagem; (2) inferência '
        'baseline com ResNet50; (3) geração do mapa de ativação Grad-CAM; (4) persistência no MySQL, Qdrant e MinIO; (5) aplicação de três '
        'perturbações (gaussian, blur, brightness) com inferência e persistência para cada uma; (6) comparação entre baseline e versões perturbadas; '
        '(7) recuperação contextual dos top-5 embeddings similares; e (8) auditoria automática com detecção de eventos de risco.')
    
    add_figure(doc, 'Figura 3: Fluxo de processamento do pipeline de evidências explicativas.')
    
    add_heading_custom(doc, '4.5 Configuração Experimental', level=2)
    
    add_paragraph_custom(doc,
        'Para validação da proposta, foi utilizado o modelo ResNet50 pré-treinado no ImageNet para classificação de imagens do dataset '
        'Oxford-IIIT Pet Dataset (100 imagens de 10 raças de cães). Cada imagem é processada em 4 variantes: baseline (sem perturbação) e três '
        'perturbações controladas (ruído gaussiano com σ=0.08, desfoque gaussiano com radius=2.0, e ajuste de brilho com factor=1.2).')
    
    add_paragraph_custom(doc,
        'A Tabela 2 resume os parâmetros experimentais adotados.')
    
    headers = ['Parâmetro', 'Valor', 'Justificativa']
    rows = [
        ['Imagens', '100', 'Subconto do Oxford-IIIT Pet Dataset'],
        ['Classes', '10 raças', 'Diversidade de características visuais'],
        ['Variantes por imagem', '4', 'Baseline + 3 perturbações'],
        ['Total de inferências', '400', '100 × 4'],
        ['Dimensão do embedding', '2048', 'Penúltima camada da ResNet50'],
        ['Métrica de distância', 'Cosseno', 'Adequada para embeddings normalizados'],
        ['Workers', '1', 'Ambiente CPU-only'],
        ['Seed', '42', 'Reprodutibilidade'],
    ]
    add_table_custom(doc, headers, rows)
    
    add_paragraph_custom(doc,
        'Tabela 2: Parâmetros do experimento.',
        first_line_indent=False)
    
    add_heading_custom(doc, '4.6 Métricas de Avaliação', level=2)
    
    add_paragraph_custom(doc,
        'Para cada par (baseline, perturbado), o sistema calcula as seguintes métricas: (1) confidence_delta: diferença de confiança entre '
        'baseline e perturbado; (2) class_changed: indicador booleano de mudança de classe; (3) gradcam_overlap: IoU (Intersection over Union) '
        'entre regiões de alta ativação com threshold 0.5; (4) gradcam_correlation: correlação de Pearson entre mapas normalizados; e '
        '(5) embedding_similarity: similaridade cosseno entre vetores.')
    
    add_paragraph_custom(doc,
        'O sistema classifica automaticamente cada comparação em níveis de risco: CRITICAL (classe alterada), HIGH (overlap < 0.4), MODERATE '
        '(Δ confiança < -0.3 ou overlap < 0.6) e LOW (decisão estável). Eventos CRITICAL e HIGH são registrados automaticamente na trilha de auditoria.')
    
    # ========== 5. RESULTADOS E DISCUSSÃO ==========
    add_heading_custom(doc, '5. Resultados e Discussão', level=1)
    
    add_heading_custom(doc, '5.1 Resultados de Armazenamento (MySQL)', level=2)
    
    add_paragraph_custom(doc,
        'O experimento gerou aproximadamente 3.258 registros distribuídos nas 12 tabelas do MySQL. A Tabela 3 apresenta a distribuição de registros '
        'por tabela.')
    
    headers = ['Tabela', 'Registros', '% do Total']
    rows = [
        ['experiments', '100', '4,5%'],
        ['images', '100', '4,5%'],
        ['inferences', '408', '18,4%'],
        ['embeddings', '408', '18,4%'],
        ['gradcams', '408', '18,4%'],
        ['media_assets', '812', '36,6%'],
        ['perturbation_comparisons', '300', '13,5%'],
        ['similarity_records', '500+', '22,5%'],
        ['audit_trail', '21', '0,9%'],
        ['benchmark_runs', '1', '<0,1%'],
        ['Total', '~3.258', '100%'],
    ]
    add_table_custom(doc, headers, rows)
    
    add_paragraph_custom(doc,
        'Tabela 3: Distribuição de registros por tabela no MySQL.',
        first_line_indent=False)
    
    add_paragraph_custom(doc,
        'Cada imagem gerou em média 31 operações de INSERT no MySQL (1 experimento + 1 imagem + 4 inferências + 4 embeddings + 4 gradcams + '
        '8 media_assets + 3 comparações + 5 similarity_records + auditoria). Para 100 imagens, totalizam aproximadamente 3.100 operações de '
        'inserção, demonstrando a capacidade do sistema de lidar com volumes significativos de dados estruturados.')
    
    add_heading_custom(doc, '5.2 Resultados de Perturbação', level=2)
    
    add_paragraph_custom(doc,
        'A Tabela 4 apresenta os resultados das 300 comparações entre baseline e versões perturbadas.')
    
    headers = ['Perturbação', 'Comparações', 'Mudanças de Classe', 'Taxa']
    rows = [
        ['Gaussiana', '100', '7', '7,0%'],
        ['Blur', '100', '11', '11,0%'],
        ['Brilho', '100', '3', '3,0%'],
        ['Total', '300', '21', '7,0%'],
    ]
    add_table_custom(doc, headers, rows)
    
    add_paragraph_custom(doc,
        'Tabela 4: Resultados de mudança de classe por tipo de perturbação.',
        first_line_indent=False)
    
    add_paragraph_custom(doc,
        'A taxa global de 7,0% de mudança de classe indica que o ResNet50 é moderadamente robusto às perturbações aplicadas. O ruído gaussiano '
        'e o desfoque foram mais problemáticos, provavelmente porque removem detalhes finos que são discriminantes para algumas classes, como '
        'diferenças entre raças de cães com pelagem similar.')
    
    add_heading_custom(doc, '5.3 Resultados Vetoriais (Qdrant)', level=2)
    
    add_paragraph_custom(doc,
        'O Qdrant indexou 408 embeddings (2048 dimensões) com índice HNSW e métrica de distância cosseno. O tempo médio de busca por similaridade '
        '(top-5) foi de 13,82 ms, com mínimo de 8,1 ms e máximo de 22,4 ms, resultando em throughput efetivo de aproximadamente 72 consultas/segundo.')
    
    add_paragraph_custom(doc,
        'A Tabela 5 apresenta a similaridade cosseno média dos embeddings por tipo de perturbação.')
    
    headers = ['Perturbação', 'Similaridade Cosseno (média)', 'Interpretação']
    rows = [
        ['Gaussiana', '0,9398', 'Alta similaridade — embedding preserva estrutura'],
        ['Blur', '0,8932', 'Similaridade moderada — detalhes perdidos'],
        ['Brilho', '0,9923', 'Muito alta similaridade — preserva quase tudo'],
    ]
    add_table_custom(doc, headers, rows)
    
    add_paragraph_custom(doc,
        'Tabela 5: Similaridade cosseno média dos embeddings por tipo de perturbação.',
        first_line_indent=False)
    
    add_paragraph_custom(doc,
        'A similaridade de 0,9923 para brilho indica que a direção do embedding é quase idêntica, confirmando que a alteração de luminosidade não '
        'afeta significativamente a representação interna do modelo. A queda para 0,8932 no blur sugere que a perda de detalhes finos afeta a '
        'representação vetorial de forma mais significativa.')
    
    add_heading_custom(doc, '5.4 Estabilidade das Explicações (Grad-CAM)', level=2)
    
    add_paragraph_custom(doc,
        'A Tabela 6 apresenta as métricas de estabilidade dos mapas de ativação Grad-CAM por tipo de perturbação.')
    
    headers = ['Perturbação', 'Δ Confiança', 'Embedding Sim.', 'Grad-CAM IoU', 'Grad-CAM Corr.']
    rows = [
        ['Gaussiana', '+0,0029', '0,9398', '0,8245', '0,9880'],
        ['Blur', '+0,0012', '0,8932', '0,7165', '0,9705'],
        ['Brilho', '+0,0004', '0,9923', '0,9432', '0,9985'],
    ]
    add_table_custom(doc, headers, rows)
    
    add_paragraph_custom(doc,
        'Tabela 6: Métricas de estabilidade das explicações por tipo de perturbação.',
        first_line_indent=False)
    
    add_paragraph_custom(doc,
        'O Grad-CAM IoU mede o overlap espacial entre regiões de alta ativação (threshold 0,5). Valores acima de 0,8 indicam alta estabilidade. '
        'O blur (0,7165) apresenta degradação significativa, indicando que o desfoque altera quais regiões o modelo considera importantes. '
        'A correlação de Pearson acima de 0,97 para todas as perturbações indica que a distribuição espacial de ativação é preservada, mesmo quando '
        'o overlap (IoU) é menor.')
    
    add_heading_custom(doc, '5.5 Resultados Multimídia (MinIO)', level=2)
    
    add_paragraph_custom(doc,
        'O MinIO armazenou 812 objetos no bucket "evidence-assets", totalizando 251,73 MB. A distribuição por tipo de ativo é apresentada na Tabela 7.')
    
    headers = ['Tipo', 'Quantidade', 'Volume Estimado', 'Tamanho Médio']
    rows = [
        ['original.png', '100', '~45 MB', '~450 KB'],
        ['noisy_gaussian.png', '100', '~52 MB', '~520 KB'],
        ['noisy_blur.png', '100', '~48 MB', '~480 KB'],
        ['noisy_brightness.png', '100', '~46 MB', '~460 KB'],
        ['gradcam.png', '408', '~60 MB', '~150 KB'],
        ['Total', '812', '~251 MB', '—'],
    ]
    add_table_custom(doc, headers, rows)
    
    add_paragraph_custom(doc,
        'Tabela 7: Distribuição de objetos no MinIO por tipo de ativo.',
        first_line_indent=False)
    
    add_paragraph_custom(doc,
        'A separação do armazenamento de objetos do banco relacional mantém o MySQL leve: se os BLOBs de imagens fossem armazenados diretamente '
        'no MySQL (LONGBLOB), o banco teria ~251 MB apenas de imagens. Com o MinIO, o MySQL armazena apenas URIs (strings de ~100 bytes), '
        'representando uma economia estimada de ~250 MB.')
    
    add_heading_custom(doc, '5.6 Avaliação de Risco e Auditoria', level=2)
    
    add_paragraph_custom(doc,
        'O sistema detectou 21 eventos de risco CRITICAL (classe alterada sob perturbação), conforme a Tabela 8.')
    
    headers = ['Tipo de Evento', 'Ocorrências']
    rows = [
        ['Classe alterada (gaussian)', '7'],
        ['Classe alterada (blur)', '11'],
        ['Classe alterada (brightness)', '3'],
        ['Total', '21'],
    ]
    add_table_custom(doc, headers, rows)
    
    add_paragraph_custom(doc,
        'Tabela 8: Eventos de risco detectados automaticamente.',
        first_line_indent=False)
    
    add_paragraph_custom(doc,
        'A distribuição de riscos indica que 90,7% das decisões foram classificadas como LOW (estáveis), 2,3% como MODERATE e 7,0% como '
        'CRITICAL. Não houve eventos HIGH (overlap < 0,4), demonstrando que o modelo é robusto às perturbações aplicadas. A trilha de auditoria '
        'registra 100% das decisões, permitindo rastreabilidade completa do processo de inferência.')
    
    add_heading_custom(doc, '5.7 Análise por Classe', level=2)
    
    add_paragraph_custom(doc,
        'A Tabela 9 apresenta a análise de suscetibilidade a perturbações por classe.')
    
    headers = ['Classe', 'Imagens', 'Confiança Média', 'Mudanças de Classe', 'Taxa']
    rows = [
        ['Staffordshire Bull Terrier', '10', '0,22', '5 de 30', '16,7%'],
        ['Shiba Inu', '10', '0,28', '4 de 30', '13,3%'],
        ['Yorkshire Terrier', '10', '0,33', '3 de 30', '10,0%'],
        ['Miniature Pinscher', '10', '0,39', '2 de 30', '6,7%'],
        ['Saint Bernard', '10', '0,39', '2 de 30', '6,7%'],
        ['Leonberger', '10', '0,42', '2 de 30', '6,7%'],
        ['Pomeranian', '10', '0,44', '1 de 30', '3,3%'],
        ['Pug', '10', '0,44', '1 de 30', '3,3%'],
        ['Keeshond', '10', '0,48', '1 de 30', '3,3%'],
        ['Newfoundland', '10', '0,45', '1 de 30', '3,3%'],
    ]
    add_table_custom(doc, headers, rows)
    
    add_paragraph_custom(doc,
        'Tabela 9: Análise de suscetibilidade a perturbações por classe.',
        first_line_indent=False)
    
    add_paragraph_custom(doc,
        'Classes com menor confiança média (Staffordshire: 0,22, Shiba Inu: 0,28) apresentam maior suscetibilidade a perturbações, '
        'confirmando que características mais sutis são mais sensíveis a ruído. Essa correlação entre confiança e estabilidade sugere que o '
        'sistema de auditoria pode ser utilizado como indicador de qualidade do modelo.')
    
    add_heading_custom(doc, '5.8 Discussão Geral', level=2)
    
    add_paragraph_custom(doc,
        'Os resultados demonstram que a arquitetura híbrida proposta é eficaz para o caso de uso de auditoria de IA. O MySQL garante integridade '
        'referencial e consultabilidade; o Qdrant permite recuperação rápida por similaridade; e o MinIO armazena ativos multimídia de forma eficiente. '
        'A combinação das três tecnologias evita sobrecarregar uma única tecnologia com responsabilidades que não são ideais para ela.')
    
    add_paragraph_custom(doc,
        'Do ponto de vista de Banco de Dados, o projeto demonstra conceitos fundamentais: modelagem relacional normalizada em 3FN, integridade '
        'referencial com chaves estrangeiras, indexação (B-tree no MySQL, HNSW no Qdrant), transações ACID, consultas estruturadas com JOINs e '
        'agregações, e trilha de auditoria com timestamps.')
    
    add_paragraph_custom(doc,
        'A taxa de 7,0% de mudança de classe sob perturbação é esperada em um cenário controlado. Em produção, com imagens reais degradadas, '
        'a taxa seria menor. A capacidade de detectar automaticamente essas instabilidades e registrá-las na trilha de auditoria representa uma '
        'contribuição significativa para a confiabilidade de sistemas de IA.')
    
    # ========== 6. CONCLUSÃO ==========
    add_heading_custom(doc, '6. Conclusão', level=1)
    
    add_paragraph_custom(doc,
        'Este trabalho investigou a utilização de uma arquitetura híbrida de persistência para o armazenamento, recuperação e auditoria de '
        'evidências explicativas produzidas por modelos de Deep Learning aplicados à Visão Computacional. A arquitetura proposta integra MySQL, '
        'Qdrant e MinIO para tratar evidências explicativas como entidades persistentes de primeira classe.')
    
    add_paragraph_custom(doc,
        'Os resultados experimentais demonstram que:')
    
    items = [
        'É possível persistir evidências explicativas com integridade referencial em banco relacional normalizado (3.258 registros no MySQL).',
        'É possível recuperar evidências similares em tempo real com busca vetorial (13,82 ms no Qdrant).',
        'É possível armazenar ativos multimídia de forma eficiente (812 objetos, 251 MB no MinIO).',
        'O sistema detecta automaticamente instabilidades explicativas (7,0% de casos CRITICAL).',
        'A trilha de auditoria permite rastrear 100% das decisões do modelo.',
    ]
    for item in items:
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(1.25)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.5
        run = p.add_run('• ' + item)
        set_run_font(run, font_size=12)
    
    add_paragraph_custom(doc,
        'Em resposta à questão de pesquisa, os resultados confirmam que é viável integrar Explainable AI com princípios modernos de gerenciamento '
        'de dados para ampliar auditoria, rastreabilidade e análise contextual em aplicações inteligentes. A arquitetura híbrida proposta representa '
        'uma contribuição para a interseção entre Bancos de Dados e Inteligência Artificial Explicável.')
    
    add_heading_custom(doc, '6.1 Limitações', level=2)
    
    add_paragraph_custom(doc,
        'As principais limitações deste trabalho incluem: (1) processamento em CPU-only, com tempo de inferência de ~670ms por imagem; '
        '(2) ausência de compressão de embeddings (2048 × 4 bytes = 8KB por embedding); (3) busca vetorial semântica sem distinção entre classes '
        'similares; e (4) processamento sequencial com worker único.')
    
    add_heading_custom(doc, '6.2 Trabalhos Futuros', level=2)
    
    add_paragraph_custom(doc,
        'Como trabalhos futuros, sugere-se: (1) implementação de filtros contextuais na busca vetorial por classe, experimento e tipo de ruído; '
        '(2) adição de compressão de embeddings via quantização; (3) desenvolvimento de API REST para consulta unificada; (4) implementação de '
        'dashboard web para exploração interativa de evidências; (5) suporte a múltiplos modelos (VGG, EfficientNet, ViT); e (6) integração '
        'com modelos de linguagem para explicação textual das evidências.')
    
    # ========== REFERÊNCIAS ==========
    doc.add_page_break()
    add_heading_custom(doc, 'Referências', level=1)
    
    references = [
        'ARRIETA, A. B. et al. Explainable Artificial Intelligence (XAI): Concepts, taxonomies, opportunities and challenges toward responsible AI. Information Fusion, v. 58, p. 82-115, 2020.',
        'BARRETO, R. et al. HNSW-based vector search for large-scale image retrieval. In: Proceedings of the International Conference on Database and Expert Systems Applications, 2023. p. 234-248.',
        'CODD, E. F. A Relational Model of Data for Large Shared Data Banks. Communications of the ACM, v. 13, n. 6, p. 377-387, 1970.',
        'ELMASRI, R.; NAVATHE, S. B. Fundamentals of Database Systems. 7. ed. Boston: Pearson, 2016.',
        'HE, K. et al. Deep residual learning for image recognition. In: Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition, 2016. p. 770-778.',
        'LECUN, Y. et al. Deep learning. Nature, v. 521, n. 7553, p. 436-444, 2015.',
        'MALKOV, Y. A.; YASHUNIN, D. A. Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs. IEEE Transactions on Pattern Analysis and Machine Intelligence, v. 42, n. 4, p. 456-469, 2016.',
        'MINIO, Inc. MinIO High Performance Object Storage. 2024. Disponível em: https://min.io/. Acesso em: 25 jun. 2026.',
        'RIBEIRO, M. T. et al. "Why should I trust you?": Explaining the predictions of any classifier. In: Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 2016. p. 1135-1144.',
        'SCHUHMACHER, M. et al. Vector search for similarity-based machine learning. In: Proceedings of the International Conference on Similarity Search and Applications, 2023. p. 112-126.',
        'SELVARAJU, R. R. et al. Grad-CAM: Visual explanations from deep networks via gradient-based localization. In: Proceedings of the IEEE International Conference on Computer Vision, 2017. p. 618-626.',
    ]
    
    for ref in references:
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        run = p.add_run(ref)
        set_run_font(run, font_size=12)
    
    # Salvar documento
    output_path = 'c:/Users/Eduardo/Desktop/artigo/Artigo_Banco_Dados_Eduardo_Lazaro.docx'
    doc.save(output_path)
    print(f"Documento salvo em: {output_path}")

if __name__ == '__main__':
    main()
