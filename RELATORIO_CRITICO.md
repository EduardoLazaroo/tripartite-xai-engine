# Relatório Crítico de Revisão do Artigo e Projeto

**Disciplina:** CCO - Banco de Dados
**Autor:** Eduardo Lázaro Roesler de Oliveira
**Tema:** Arquitetura Híbrida de Persistência e Recuperação de Evidências Explicativas em Sistemas de Visão Computacional Baseados em Deep Learning
**Data da Revisão:** 27 de junho de 2026
**Revisor:** Avaliador Exigente (simulacao de banca de mestrado/doutorado)

---

## 1. Visao Geral

Este relatorio apresenta uma analise critica abrangente e rigorosa do artigo tecnico-científico e do projeto de software associados, desenvolvidos como trabalho final da disciplina de Banco de Dados. A analisis e conduzida sob a otica de um professor extremamente exigente, especialista em Banco de Dados, com experiencia em pesquisa cientifica e bancas de mestrado/doutorado. O objetivo e identificar TODOS os possiveis problemas antes que um avaliador real os encontre.

---

## 2. Analise do Conteudo Cientifico do Artigo

### 2.1 Titulo

**Problemas identificados:**
- O titulo e excessivamente longo (21 palavras), o que dificulta a indexacao e a leitura rapida.
- O termo "Evidencias Explicativas" e vago — nao fica claro se refere a mapas de ativacao, embeddings, metricas de confianca ou todos eles simultaneamente.
- Falta o ano de publicacao no titulo, o que e convencao em artigos cientificos.

**Sugestao:** "Arquitetura Hibrida de Persistencia de Evidencias de Explicabilidade em Sistemas de Visao Computacional com Deep Learning"

### 2.2 Resumo e Abstract

**Problemas identificados:**
- O resumo e uma unica pagina de texto continuo sem quebras visuais, dificultando a leitura.
- Falta a explicitacao da **metodologia** no resumo (como o experimento foi conduzido).
- Falta a explicitacao das **principais contribuicoes** de forma destacada.
- O resumo menciona "31,35 ms" e "247,64 MB" mas nao contextualiza se esses numeros sao bons ou ruins.
- Nao ha um paragrafo de "metodologia" separado no resumo — o leitor nao sabe como os resultados foram obtidos.

**Sugestao:** Estruturar o resumo em paragrafos: (1) Contexto e problema, (2) Objetivo, (3) Metodologia, (4) Resultados principais, (5) Conclusao.

### 2.3 Introducao

**Pontos positivos:**
- Contextualizacao adequada sobre Deep Learning e XAI.
- Questao de pesquisa claramente formulada.
- Organizacao do texto beruturada.

**Problemas criticos:**
1. **Falta de justificativa tecnica solida para a necessidade de TRES tecnologias diferentes.** O artigo afirma que a arquitetura e "hibrida" mas nao demonstra que uma solucao com duas tecnologias (ou mesmo uma) seria insuficiente. Qual e o problema concreto que o MySQL + Qdrant + MinIO resolve que o PostgreSQL + pgvector nao resolveria?

2. **O exemplo do "cao da raca Leonberg" e artificial e desconexo do problema real.** O artigo usa um dataset de racas de caes (Oxford-IIIT Pet Dataset) que nao tem relevancia pratica para auditoria de IA. Um professor exigente questionaria: "Por que nao usar um dataset medico (como CheXpert ou MIMIC-CXR) onde a explicabilidade e literalmente questao de vida ou morte?"

3. **A mencao a LGPD/GDPR parece "decorative"** — o artigo nao demonstra como a arquitetura atende especificamente aos requisitos legais. Qual artigo da LGPD exige rastreabilidade de decisoes? Como a arquitetura se alinha ao "direito a explicacao" do Art. 22 do GDPR?

4. **Falta de hipotese de pesquisa.** O artigo tem uma pergunta de pesquisa, mas nao formula uma hipotese testavel. Exemplo: "A hipotese e que uma arquitetura hibrida de persistencia reduz o tempo de recuperacao de evidencias em 50% comparado a uma abordagem monolitica."

5. **A introducao nao define os limites do escopo.** O sistema proposto se aplica apenas a classificacao de imagens? E para deteccao de objetos? Segmentacao? Video?

### 2.4 Fundamentacao Teorica

**Pontos positivos:**
- Cobre os tres pilares do trabalho (DL, XAI, BD).
- Referencias classicas (Codd, Elmasri & Navathe, LeCun, He et al.).

**Problemas criticos:**
1. **Ausencia de discussao sobre bancos de dados de grafos (Neo4j, Amazon Neptune).** Para um sistema de auditoria com rastreabilidade, um banco de grafos seria uma alternativa natural para modelar relacoes entre inferencias, evidencias e eventos de auditoria. Por que nao foi considerado?

2. **Ausencia de discussao sobre tecnicas de compressao de embeddings.** O artigo identifica como limitacao os "8KB por embedding" mas nao discute Product Quantization, Scalar Quantization, ou Binary Quantization — tecnicas padrao em bancos vetoriais modernos.

3. **Nenhuma discussao sobre transacoes distribuidas.** A arquitetura proposta envolve TRES sistemas de armazenamento independentes. O que acontece se o MySQL gravar o embedding mas o Qdrant falhar? O artigo nao discute consistencia eventual, padrao Saga, ou two-phase commit.

4. **A discussao sobre HNSW e superficial.** O artigo menciona o algoritmo mas nao discute: complexidade de construcao (O(n log n)), consumo de memoria (2-3x os dados originais), parametros (M, ef_construction, ef_search), ou alternativas como IVF-PQ ou ScaNN.

5. **Falta de discussao sobre seguranca.** O MinIO armazena imagens medicas (potencialmente) sem mencionar criptografia, controle de acesso, ou politicas de retencao.

### 2.5 Trabalhos Relacionados

**Problemas criticos (esta e a seccao mais fraca do artigo):**

1. **Apenas 5 trabalhos revisados.** Para um artigo cientifico, espera-se pelo menos 15-20 trabalhos relacionados. A revisao atual e insuficiente para posicionar a contribuicao na literatura.

2. **A Tabela 1 e enganosa.** A comparacao e binaria ("Sim/Nao") sem nuances. Por exemplo:
   - "Arrieta et al. (2020)" e classificado como "Parcial" em auditoria — o que isso significa exatamente?
   - "Barreto et al. (2023)" e classificado como "Parcial" em persistencia — por que?
   - Nenhum trabalho e comparado em termos de desempenho, escalabilidade, ou caso de uso.

3. **Ausencia de trabalhos fundamentais:**
   - MLflow (gestao de experimentos de ML)
   - Kubeflow (pipelines de ML)
   - Apache Atlas / OpenLineage (data lineage)
   - WhyLabs (monitoramento de ML)
   - pgvector (busca vetorial em PostgreSQL)
   - Pinecone, Weaviate, Chroma (bancos vetoriais gerenciados)
   - DVC (Versionamento de dados)

4. **A analise e puramente descritiva.** Nenhum trabalho e criticado em termos de limitacoes metodologicas, escalabilidade, ou adequacao a cenarios reais.

5. **Falta de comparacao com solucoes comerciais.** Ferramentas como AWS SageMaker Model Monitor, Google Vertex AI Explainability, ou Azure Resilience AI nao sao mencionadas.

### 2.6 Metodologia e Desenvolvimento

**Pontos positivos:**
- Arquitetura de tres camadas bem justificada.
- Modelo relacional com 12 tabelas normalizado em 3FN.
- Pipeline de processamento claramente descrito.

**Problemas criticos:**

1. **O experimento e extremamente limitado:**
   - 100 imagens e uma amostra insignificante. Para resultados estatisticamente significativos, seriam necessarias pelo menos 1000+ imagens.
   - 11 classes e muito pouco para generalizar o comportamento do modelo.
   - Apenas 3 tipos de perturbacao — faltam rotacoes, crops, compressao JPEG, artefatos de sensor, etc.
   - CPU-only: os resultados nao refletem o desempenho em producao (GPU).

2. **Ausencia de baseline comparativo.** O artigo nao compara a arquitetura hibrida com:
   - Uma solucao monolitica (tudo no MySQL)
   - Uma solucao com PostgreSQL + pgvector
   - Uma solucao com banco de grafos
   Sem essa comparativa, nao e possivel afirmar que a arquitetura hibrida e superior.

3. **Falta de metricas de desempenho do MySQL.** O artigo reporta 31.35ms para o Qdrant mas nao menciona:
   - Tempo de INSERT no MySQL
   - Tempo de SELECT com JOINs
   - Tamanho do banco de dados
   - Uso de indices

4. **A metrica de "9417.73ms por imagem" e alarmante.** Isso significa que para processar 100 imagens, o sistema leva 942 segundos (15.7 minutos). Em producao, com milhoes de inferencias/dia, isso seria completamente inviavel. O artigo justifica o overhead mas nao propoe solucoes.

5. **Nao ha analise de escalabilidade.** O que acontece com 1000 imagens? 10000? O tempo de busca no Qdrant cresce linearmente? O MySQL suporta o volume?

6. **Falta de reprodutibilidade.** Nao ha:
   - Repositorio de codigo
   - Docker Compose
   - Requirements.txt
   - Seed documentada (mencionada na Tabela 2 mas nao explicada)
   - Instrucoes de instalacao

7. **O campo `vector_db_id` como ponte entre MySQL e Qdrant e fraco.** Nao ha garantia de consistencia entre os dois bancos. Se um embedding for apagado do Qdrant mas nao do MySQL (ou vice-versa), o sistema fica inconsistente.

### 2.7 Resultados e Discussao

**Pontos positivos:**
- Tabelas com metricas especificas.
- Analise por classe (Tabela 9).
- Discussao honesta do overhead.

**Problemas criticos:**

1. **Ausencia completa de analise estatistica:**
   - Nao ha desvio padrao para nenhuma metrica.
   - Nao ha intervalos de confianca.
   - Nao ha testes de hipotese (t-test, ANOVA).
   - A diferenca entre 0.9251 e 0.8985 e estatisticamente significativa? Impossivel saber.

2. **A metrica de "sobreposicao media: 0.8456" e apresentada sem contexto.** Isso e bom ou ruim? Qual e o threshold aceitavel? O artigo menciona "valores acima de 0.8 indicam alta estabilidade" mas nao cita nenhuma referencia para justificar esse valor.

3. **A classificacao de risco e arbitraria:**
   - CRITICAL: classe alterada
   - HIGH: overlap < 0.4
   - MODERATE: delta confianca < -0.3 ou overlap < 0.6
   - LOW: decisao estavel
   Esses thresholds sao completamente arbitrarios. Nao ha justificativa teorica ou empirica.

4. **A comparacao entre perturbacoes e superficial.** O artigo diz que "blur foi mais problematico" mas nao explica POR QUE. Qual e a relacao entre o kernel gaussiano do blur e a perda de ativacao no Grad-CAM?

5. **Falta de analise de correlacao entre metricas.** Existe correlacao entre embedding_similarity e gradcam_overlap? Se o embedding muda pouco, o Grad-CAM muda? Essas relacoes nao sao exploradas.

6. **A Tabela 9 tem dados inconsistentes.** A coluna "Confianca Media" usa valores decimais com virgula (0,22), mas a coluna "Sensibilidade" usa porcentagem (41,7%). A consistencia de formatacao e importante.

7. **A discussao nao relaciona os resultados com a literatura.** O artigo nao compara seus resultados com os de Barreto et al. (2023) ou outros trabalhos relacionados.

### 2.8 Conclusao

**Problemas criticos:**
1. A conclusao nao discute a **aplicabilidade pratica** do sistema.
2. Nao ha reflexao sobre o **custo de manutencao** de uma arquitetura com tres bancos de dados.
3. A afirmacao "contribuicao cientifica solida" e auto-congratulatoria sem evidencias.
4. Nao discute como o sistema se comporta em **cenarios reais de producao**.

### 2.9 Referencias

**Problemas criticos:**
1. **Apenas 12 referencias.** Para um artigo cientifico, espera-se pelo menos 20-30 referencias.
2. **Faltam referencias sobre:**
   - Data Lineage (OpenLineage, Apache Atlas)
   - ML Experiment Tracking (MLflow, Weights & Biases)
   - Vector Databases (Weaviate, Chroma, Pinecone)
   - Graph Databases (Neo4j)
   - Embedding Compression (Product Quantization)
   - Distributed Transactions (Saga pattern)
   - AI Governance (NIST AI RMF, EU AI Act)
3. **A referencia "BARRETO et al., 2023" e generica.** Nao ha titulo do artigo, apenas "Proceedings of the International Conference...".
4. **A referencia "SCHUHMACHER et al., 2023" tem o mesmo problema.**
5. **A referencia "MINIO, 2024" e uma pagina web, nao um artigo cientifico.**

---

## 3. Analise do Projeto de Software

### 3.1 Estrutura do Projeto

**Problemas criticos:**

1. **O projeto contem APENAS o script gerador do artigo.** Nao ha codigo do sistema de banco de dados descrito no artigo. Isso e uma falha gravissima, pois:
   - Nao e possivel verificar se o sistema realmente funciona.
   - Nao e possivel reproduzir os experimentos.
   - O artigo descreve um sistema que nao esta disponivel para validacao.

2. **Ausencia completa de artefatos de engenharia:**
   - Sem `README.md`
   - Sem `requirements.txt` ou `pyproject.toml`
   - Sem `Docker Compose.yml`
   - Sem scripts SQL de criacao do banco
   - Sem `.gitignore`
   - Sem testes
   - Sem documentacao de API

3. **Caminhos hardcoded:**
   - `C:/Windows/Fonts` — falha em Linux/macOS
   - `c:/Users/Eduardo/Desktop/artigo/Artigo_Banco_Dados_Eduardo_Lazaro.pdf` — falha em qualquer outro computador

### 3.2 Qualidade do Codigo (gerar_artigo.py)

**Problemas criticos:**

1. **A classe `ArtigoPDF` tem mais de 1000 linhas.** Deveria ser dividida em modulos menores (ex: `pdf_format.py`, `pdf_layout.py`, `pdf_content.py`).

2. **Dependencia de fontes do Windows.** O script falha completamente em sistemas Linux/macOS.

3. **Sumario nao funcional.** O proprio codigo admite que o sumario nao funciona ("para sumario com paginas, utilize a versao Word ou ferramentas LaTeX"). Isso e inaceitavel para um artigo academico.

4. **Dados do experimento hardcoded.** Todos os numeros (9417.73, 31.35, 247.64, etc.) estao diretamente no codigo, dificultando atualizacoes.

5. **Falta de tratamento de erros robusto.** O codigo usa `try/except` com `pass` silencioso, mascarando erros.

6. **A formatacao de fontes e redundante.** O metodo `_setup_fonts` repete a logica de configuracao em cada chamada de `set_font`.

### 3.3 Arquivos de Assets

**Problemas:**
- Apenas 8 imagens (4 originais + 4 perturbacoes) e 1 diagrama.
- Faltam diagramas do DER do banco de dados.
- Faltam diagramas do pipeline de dados.
- Faltam diagramas de sequencia mostrando o fluxo de dados entre as camadas.

---

## 4. Aderencia as Orientacoes do Professor

Conforme especificado em `03_orientacoes_finais_banco_dados.md`:

| Critério | Status | Observacoes |
|----------|--------|-------------|
| Relevancia e atualidade do tema | ✅ Atendido | Tema atual e relevante |
| Qualidade da escrita | ⚠️ Parcial | Boa estrutura, mas carece de profundidade critica |
| Clareza na exposicao teorica | ⚠️ Parcial | Falta discussao sobre alternativas (grafos, compressao) |
| Profundidade na analise do estado da arte | ❌ Insuficiente | Apenas 5 trabalhos, analise descritiva |
| Pertinencia da aplicacao pratica | ⚠️ Parcial | Experimento limitado, sem baseline comparativo |
| Qualidade dos resultados e discussao | ⚠️ Parcial | Falta analise estatistica e comparacao com baseline |
| Adequacao das referencias | ❌ Insuficiente | 12 referencias e o minimo; faltam trabalhos fundamentais |
| Estrutura sugerida (secoes) | ✅ Atendido | Todas as secoes presentes |
| Extensao (10-15 paginas) | ✅ Atendido | Artigo gerado em PDF |
| Tabela de comparacao | ✅ Atendido | Tabela 1 presente |
| Reprodutibilidade | ❌ Nao atendido | Sem repositorio, Docker, ou instrucoes |

---

## 5. Pontos Fortes Identificados

1. **Tema inovador e relevante:** A interseccao entre XAI e Bancos de Dados e uma contribuicao genuina.
2. **Arquitetura bem fundamentada:** A separacao em tres camadas (relacional, vetorial, objetos) e tecnicamente solida.
3. **Modelo relacional robusto:** 12 tabelas normalizadas em 3FN com integridade referencial demonstram competencia em modelagem.
4. **Resultados concretos:** Metricas especificas (IoU, similaridade cosseno, confianca) quantificam o desempenho.
5. **Discussao honesta de limitacoes:** O overhead de 9.4s e transparentemente reportado e justificado.
6. **Formatacao profissional do PDF:** O artigo gerado segue normas ABNT com qualidade visual.

---

## 6. Problemas Criticos (Priorizados por Urgencia)

### 6.1 Problemas Criticos (Correcao Obrigatoria)

| # | Problema | Por que e um problema | Como corrigir |
|---|----------|----------------------|---------------|
| 1 | Ausencia do codigo-fonte do sistema | Impossibilita verificacao e reproducao | Criar repositorio com scripts SQL, pipeline Python, Docker Compose |
| 2 | Apenas 5 trabalhos relacionados | Insuficiente para posicionar a contribuicao | Expandir para 15-20 trabalhos, incluindo MLflow, pgvector, Neo4j |
| 3 | Falta de baseline comparativo | Nao demonstra que a arquitetura hibrida e superior | Implementar e comparar com MySQL-only e PostgreSQL+pgvector |
| 4 | Ausencia de analise estatistica | Resultados nao tem significancia estatistica | Adicionar desvio padrao, IC, testes t/ANOVA |
| 5 | Diagramas placeholders | Compromete a clareza da apresentacao | Gerar diagramas reais com draw.io, Mermaid, ou dbdiagram.io |
| 6 | Experimento limitado (100 imagens) | Resultados nao sao generalizaveis | Usar pelo menos 1000 imagens e mais classes |
| 7 | Falta de reprodutibilidade | Ninguem pode replicar o experimento | Disponibilizar codigo, dados, e instrucoes |

### 6.2 Problemas Importantes (Correcao Fortemente Recomendada)

| # | Problema | Por que e um problema | Como corrigir |
|---|----------|----------------------|---------------|
| 8 | Nao ha discussao sobre consistencia distribuida | Sistema pode ficar inconsistente | Discutir Saga, 2PC, ou consistencia eventual |
| 9 | Thresholds de risco arbitrarios | Classificacao nao tem validade | Justificar com literatura ou analise de sensibilidade |
| 10 | Falta de metricas de desempenho do MySQL | Nao se sabe se o MySQL e o gargalo | Reportar tempo de INSERT/SELECT no MySQL |
| 11 | 9.4s por imagem e inviavel em producao | Sistema nao e pratico | Discutir batch processing, async I/O, GPU |
| 12 | Falta de seguranca no MinIO | Dados medicos precisam de protecao | Adicionar discussao sobre criptografia e controle de acesso |
| 13 | Referencias insuficientes | Base teorica fraca | Adicionar pelo menos 8-10 referencias adicionais |
| 14 | Dataset de caes nao e relevante | Falta de aplicabilidade pratica | Considerar dataset medico ou de seguranca |

### 6.3 Problemas Menores (Correcao Recomendada)

| # | Problema | Sugestao |
|---|----------|----------|
| 15 | Titulo muito longo | Reduzir para ~12 palavras |
| 16 | Resumo sem estrutura | Dividir em paragrafos (contexto, metodo, resultado, conclusao) |
| 17 | Caminhos hardcoded no script | Usar variaveis de ambiente ou arquivo de configuracao |
| 18 | Sumario nao funcional no PDF | Usar LaTeX/Word para sumario com paginas |
| 19 | Sem requirements.txt | Criar arquivo de dependencias |
| 20 | Sem README | Criar documentacao basica |
| 21 | Classe ArtigoPDF muito grande | Refatorar em modulos menores |
| 22 | Dados do experimento hardcoded | Externalizar para YAML/JSON |

---

## 7. Avaliacao Global

### Nota por Critério (escala 0-10)

| Critério | Nota | Justificativa |
|----------|------|---------------|
| Relevancia do tema | 9 | Tema atual, inovador e com aplicacao pratica |
| Fundamentacao teorica | 6 | Boa base, mas falta discussao sobre alternativas |
| Trabalhos relacionados | 4 | Insuficiente em quantidade e profundidade |
| Metodologia | 6 | Arquitetura solida, mas experimento limitado |
| Resultados | 5 | Metricas presentes, mas analise estatistica ausente |
| Discussao | 6 | Boa discussao, mas sem comparacao com baseline |
| Qualidade da escrita | 8 | Texto claro e bem estruturado |
| Reprodutibilidade | 2 | Sem codigo do sistema, sem instrucoes |
| Aderencia as orientacoes | 6 | Maioria atendente, reprodutibilidade faltando |
| **Media Geral** | **5.8** | **Regular, com espaco para melhorias significativas** |

---

## 8. Conclusao do Relatorio

O artigo e o projeto apresentados demonstram um trabalho de qualidade **abaixo do esperado** para uma disciplina de pos-graduacao em Banco de Dados. Embora o tema seja relevante e a arquitetura proposta seja tecnicamente solida, o trabalho apresenta lacunas significativas que limitam seu impacto cientifico e sua utilidade pratica.

### Principais Problemas:

1. **A ausencia do codigo-fonte do sistema de banco de dados** e a limitacao mais critica, pois impede a verificacao independente dos resultados e a reprodutibilidade do experimento.

2. **A revisao de trabalhos relacionados** precisa ser expandida e aprofundada para posicionar adequadamente a contribuicao na literatura.

3. **A analise de resultados** carece de rigor estatistico e de comparacao com abordagens alternativas (baseline monolitico).

4. **Os diagramas do artigo sao placeholders**, comprometendo a clareza da apresentacao.

5. **O experimento e limitado demais** (100 imagens, CPU-only, 11 classes) para generalizar os resultados.

### Potencial:

Com as melhorias sugeridas, o trabalho tem potencial para se tornar uma contribuicao cientifica solida e publicavel em um workshop ou conferencia nacional na area de Bancos de Dados e Inteligencia Artificial. O tema e promissor e a base tecnica existe — falta execucao mais rigorosa.

---

## 9. Recomendacoes Finais (Priorizadas)

### Prioridade Alta (Corrigir antes da entrega final):

1. **Disponibilizar o codigo-fonte do sistema** (scripts SQL, pipeline Python, Docker Compose) em repositorio publico.
2. **Gerar diagramas reais** do DER e da arquitetura (usar draw.io, dbdiagram.io, ou Mermaid).
3. **Expandir a revisao de literatura** para pelo menos 15 trabalhos.
4. **Adicionar analise estatistica** (desvio padrao, intervalos de confianca, testes de hipotese).
5. **Adicionar baseline comparativo** (MySQL-only, PostgreSQL+pgvector).

### Prioridade Media:

6. **Expandir o experimento** para pelo menos 1000 imagens.
7. **Adicionar metricas de desempenho do MySQL**.
8. **Discutir consistencia distribuida** entre as camadas.
9. **Justificar os thresholds de risco** com base na literatura.
10. **Adicionar pelo menos 8 referencias** adicionais.

### Prioridade Baixa:

11. **Externalizar configuracoes** para arquivo de configuracao.
12. **Adicionar testes unitarios** ao gerador de PDF.
13. **Criar README** com instrucoes de instalacao.
14. **Refatorar a classe ArtigoPDF** em modulos menores.

---

## 10. Consideracoes Finais

Este relatorio foi elaborado com o objetivo de identificar TODOS os possiveis problemas do trabalho antes que um professor exigente os encontre. A intencao nao e desmotivar, mas sim fornecer um roteiro claro de melhorias que, se implementadas, tornarao o trabalho significativamente mais robusto e defensavel em uma banca de mestrado.

O tema proposto e genuinamente inovador e merece ser desenvolvido com o rigor que a pesquisa cientifica exige. A interseccao entre Bancos de Dados e Inteligencia Artificial Explicavel e uma fronteira de pesquisa pouco explorada que tem muito a contribuir para a construcao de sistemas de IA auditaveis, rastreaveis e em conformidade com regulamentacoes.

---

*Relatorio elaborado em 27 de junho de 2026 como parte da avaliacao da disciplina de Banco de Dados.*
