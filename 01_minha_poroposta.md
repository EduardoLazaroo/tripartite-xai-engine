# Arquitetura Híbrida de Persistência e Recuperação de Evidências Explicativas em Sistemas de Visão Computacional Baseados em Deep Learning

## Descrição da Proposta

O avanço recente dos modelos de Deep Learning tem impulsionado a adoção de sistemas de Inteligência Artificial em diversos domínios, especialmente em aplicações de Visão Computacional. Embora esses modelos apresentem elevado desempenho preditivo, suas decisões frequentemente são caracterizadas por baixa interpretabilidade, tornando difícil compreender quais fatores influenciaram determinada classificação ou predição.

Como resposta a esse desafio, técnicas de Explainable Artificial Intelligence (XAI) têm sido amplamente exploradas para produzir evidências explicativas capazes de auxiliar na interpretação do comportamento dos modelos. Entre essas evidências destacam-se mapas de ativação, embeddings vetoriais, métricas de confiança e outros artefatos analíticos produzidos durante o processo de inferência.

Entretanto, apesar do crescente interesse na geração dessas explicações, observa-se que a maior parte dos estudos concentra-se na produção das evidências explicativas, enquanto pouca atenção é dedicada ao seu armazenamento, gerenciamento e recuperação posterior. Em muitos sistemas, tais informações são utilizadas apenas momentaneamente durante a execução e posteriormente descartadas, limitando atividades de auditoria, rastreabilidade, análise histórica e investigação do comportamento dos modelos.

Diante desse cenário, este trabalho investiga a seguinte questão de pesquisa:

> Como uma arquitetura híbrida de persistência pode contribuir para o armazenamento, recuperação e auditoria de evidências explicativas produzidas por sistemas de Visão Computacional baseados em Deep Learning?
> 

Para responder a essa questão, propõe-se o desenvolvimento e a avaliação de uma arquitetura híbrida de dados capaz de tratar evidências explicativas como entidades persistentes, organizadas e recuperáveis dentro de um ecossistema integrado de Banco de Dados.

---

# Objetivos

## Objetivo Geral

Investigar a utilização de uma arquitetura híbrida de persistência para o armazenamento, recuperação e auditoria de evidências explicativas produzidas por modelos de Deep Learning aplicados à Visão Computacional.

## Objetivos Específicos

- Modelar uma estrutura de dados capaz de representar evidências explicativas produzidas por sistemas de IA.
- Integrar mecanismos de persistência relacional, vetorial e multimídia em uma única arquitetura.
- Armazenar informações explicativas geradas durante o processo de inferência.
- Implementar mecanismos de recuperação por similaridade utilizando embeddings vetoriais.
- Avaliar a influência de perturbações visuais sobre as decisões e explicações produzidas pelo modelo.
- Analisar a capacidade da arquitetura em apoiar auditoria, rastreabilidade e recuperação contextual de inferências.

---

# Fundamentação Conceitual

O trabalho encontra-se na interseção entre diferentes áreas de pesquisa.

Sob a perspectiva de Inteligência Artificial, são explorados conceitos relacionados a Deep Learning, Redes Neurais Convolucionais (CNNs), Visão Computacional e Explainable Artificial Intelligence (XAI).

No contexto de Banco de Dados, o estudo aborda arquiteturas híbridas de persistência, bancos vetoriais, armazenamento multimídia, recuperação semântica de informações, gerenciamento de embeddings e modelagem de dados analíticos.

Além disso, o trabalho incorpora conceitos de recuperação de informação, busca por similaridade vetorial e rastreabilidade de sistemas inteligentes, buscando estabelecer uma ponte entre a produção de explicações e seu gerenciamento persistente.

---

# Arquitetura Proposta

A arquitetura proposta adota uma abordagem híbrida composta por múltiplas camadas de armazenamento especializadas.

A camada relacional é responsável pela persistência estruturada dos metadados associados aos experimentos, inferências, métricas analíticas e eventos de auditoria produzidos durante a execução do sistema.

A camada vetorial é utilizada para armazenamento e indexação dos embeddings gerados pelos modelos de Deep Learning, possibilitando consultas por similaridade e recuperação semântica das evidências produzidas.

Complementarmente, uma camada de armazenamento de objetos é utilizada para persistir os artefatos multimídia gerados ao longo do processo experimental, incluindo imagens originais, imagens modificadas e mapas explicativos produzidos por técnicas de XAI.

Essa organização busca explorar as características específicas de cada mecanismo de armazenamento, integrando persistência estruturada, busca vetorial e gerenciamento multimídia em uma única arquitetura.

---

# Metodologia Experimental

Para validação da proposta será utilizado um modelo de Deep Learning aplicado à classificação de imagens, baseado na arquitetura ResNet50.

A geração das evidências explicativas será realizada por meio da técnica Grad-CAM (Gradient-weighted Class Activation Mapping), amplamente utilizada para identificação das regiões da imagem mais relevantes para as decisões produzidas pela rede neural.

Durante cada inferência serão produzidos e armazenados:

- imagem analisada;
- classe prevista;
- nível de confiança da predição;
- embeddings visuais extraídos da rede neural;
- mapas Grad-CAM;
- parâmetros experimentais;
- métricas analíticas associadas ao processo de inferência.

Para avaliação da robustez do modelo e da arquitetura proposta, diferentes perturbações visuais serão aplicadas às imagens processadas, incluindo ruídos, desfoques e alterações de brilho.

As evidências produzidas sob diferentes condições serão persistidas e posteriormente comparadas utilizando métricas relacionadas à estabilidade da classificação, similaridade dos embeddings e consistência dos mapas explicativos.

---

# Critérios de Avaliação

A arquitetura será analisada sob diferentes perspectivas.

Do ponto de vista de Banco de Dados, serão avaliados:

- organização dos dados explicativos;
- capacidade de persistência das evidências produzidas;
- desempenho de recuperação das informações armazenadas;
- eficiência da indexação vetorial;
- suporte à rastreabilidade e auditoria.

Sob a perspectiva da Inteligência Artificial, serão avaliados:

- estabilidade das inferências;
- impacto das perturbações visuais;
- consistência das explicações geradas;
- comportamento dos embeddings ao longo dos experimentos.

Os resultados obtidos serão discutidos à luz dos trabalhos relacionados identificados na literatura, permitindo analisar em que medida a arquitetura proposta contribui para o gerenciamento de evidências explicativas em sistemas inteligentes.

---

# Contribuições Esperadas

A principal contribuição deste trabalho consiste na investigação do papel dos Bancos de Dados no gerenciamento de evidências explicativas produzidas por sistemas de Inteligência Artificial.

Espera-se demonstrar que artefatos tradicionalmente tratados como temporários — tais como embeddings, mapas de ativação e métricas interpretativas — podem ser modelados como entidades persistentes, possibilitando mecanismos mais robustos de auditoria, recuperação contextual e rastreabilidade.

Além disso, o estudo busca contribuir para a integração entre Explainable Artificial Intelligence e arquiteturas modernas de Banco de Dados, explorando como mecanismos relacionais, vetoriais e multimídia podem atuar de forma complementar no suporte a aplicações inteligentes explicáveis.

---

Essa versão já está muito mais alinhada ao que normalmente se espera de um artigo científico de Banco de Dados, porque evidencia claramente:

- **Problema de pesquisa**;
- **Questão de pesquisa**;
- **Objetivo geral e específicos**;
- **Contribuição científica**;
- **Metodologia experimental**;
- **Critérios de avaliação**.

Ou seja, ela já começa a parecer não apenas uma descrição de projeto, mas o esqueleto do próprio artigo que seu professor está pedindo.