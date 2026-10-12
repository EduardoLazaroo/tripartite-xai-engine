# Persistencia hibrida para evidencias de explicabilidade

## Contexto

Este diretorio reune o material de um artigo academico sobre o armazenamento e a recuperacao de evidencias produzidas por experimentos de visao computacional explicavel. O foco e uma arquitetura hibrida que combina metadados relacionais, vetores e objetos, em vez de tratar mapas de explicabilidade como arquivos isolados.

O material e indicado para pesquisadores de XAI, aprendizado de maquina e bancos de dados interessados em rastreabilidade experimental.

## Proposta tecnica

A proposta organiza cada evidencia em tres camadas:

1. **MySQL** para metadados, predicoes, parametros e auditoria.
2. **Qdrant** para embeddings e recuperacao por similaridade.
3. **MinIO** para imagens, mapas Grad-CAM e artefatos volumosos.

Os documentos descrevem evidencias como predicoes, confianca, mapas Grad-CAM, perturbacoes e metricas de sobreposicao. Os resultados relatados no artigo devem ser interpretados como resultados do estudo documentado, nao como uma garantia de reproducao neste diretorio.

## Conteudo e uso

| Recurso | Finalidade |
|---|---|
| `01_minha_poroposta.md` | delimitacao do problema e da arquitetura |
| `02_base.md` | base tecnica e resultados relatados |
| `03_orientacoes_finais_banco_dados.md` | orientacoes para a versao final |
| `RELATORIO_CRITICO.md` | avaliacao critica e limites metodologicos |
| `gerar_artigo_pdf.py` | geracao do PDF do artigo |
| `assets/` | figuras usadas no material |

Para gerar o PDF, instale as dependencias usadas pelo script e execute:

```bash
python gerar_artigo_pdf.py
```

Nao ha um manifesto de dependencias nem o pipeline experimental completo neste diretorio. A reproducao das metricas exige acesso aos dados, modelos e configuracoes descritos no artigo.

## Limites e verificacao

O diretorio contem o artigo e seus artefatos de apresentacao, nao uma implementacao integral do experimento. A revisao critica registra lacunas de reprodutibilidade e de avaliacao de desempenho; elas devem ser consideradas em qualquer extensao cientifica do trabalho.

## Material para publicacao

**Texto sugerido**

> Este trabalho investiga como tornar evidencias de explicabilidade em visao computacional recuperaveis, auditaveis e reutilizaveis. A proposta combina banco relacional, busca vetorial e armazenamento de objetos para relacionar predicoes, embeddings, mapas Grad-CAM e perturbacoes em uma mesma trilha experimental. O principal desafio foi tratar explicacoes como dados de pesquisa, com contexto suficiente para consulta e verificacao, e nao apenas como imagens geradas ao final de um modelo. O artigo tambem explicita seus limites metodologicos, criando uma base honesta para futuras avaliacoes de reprodutibilidade e desempenho.

**Capturas recomendadas:** pagina de arquitetura do PDF, um exemplo de Grad-CAM, o esquema de persistencia e a tabela de recuperacao/latencia.

**Prompt para imagem complementar**

```text
Diagrama tecnico academico, fundo claro, mostrando uma arquitetura hibrida para evidencias de IA explicavel: modelo de visao computacional gera predicao, embedding e mapa Grad-CAM; MySQL armazena metadados e auditoria, Qdrant armazena vetores para busca por similaridade e MinIO armazena imagens e mapas; setas rotuladas em portugues, estilo de artigo cientifico, sem logotipos e sem texto pequeno ilegivel.
```
