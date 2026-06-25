Conversei com meu professor sobre o desenvolvimento deste projeto, explicando que ele seria base para meu artigo científico. Durante a conversa, ele demonstrou certa preocupação com a proposta.

Ele é professor de banco de dados na UNESP e atua diretamente nessa área, então sua visão é bastante centrada em fundamentos de bancos de dados tradicionais. Quando apresentei o tema, que foge um pouco desse escopo mais convencional, percebi uma certa estranheza. Ele levantou algumas questões importantes e provocativas, como:

Qual problema real você está tentando resolver?
Quando você fala em salvar dados importantes, quais dados exatamente são esses?
O que você realmente quer medir com esse sistema?
Se algo for mais rápido ou mais lento, o que isso muda na prática para o usuário?
Por que você está utilizando imagens de raças de cachorro? Qual a justificativa disso dentro do problema?
Falta uma definição mais clara do problema, da solução e do impacto. Está faltando amarrar melhor a transformação real na vida do usuário.

Depois dessa conversa, fiquei refletindo e cheguei à conclusão de que, de fato, talvez o problema ainda não estivesse claramente bem definido.

A partir disso, comecei a repensar o foco do projeto. A nova direção que considero mais sólida é a seguinte:

O sistema pode ser pensado para usuários que utilizam XAI (Explainable AI) principalmente como ferramenta para entender como modelos de IA tomam decisões sobre classificação de objetos. Em muitos casos, essas pessoas usam essas ferramentas apenas para montar protótipos ou aplicações rápidas e depois descartam, principalmente por acreditarem que o custo operacional é elevado.

No entanto, a proposta aqui é justamente mostrar que essa abordagem não é apenas útil, mas também essencial em determinados contextos.

A arquitetura de persistência híbrida (tripla) proposta oferece vantagens estratégicas importantes para sistemas de IA explicável (XAI) e para cenários de auditoria em aplicações críticas:

1. Auditoria e conformidade (MySQL 8)

O MySQL é responsável por registrar todo o histórico das inferências, incluindo experimentos e variações realizadas. Isso permite:

Rastreabilidade completa do processo de decisão (audit trail)
Identificação precisa de quais dados e condições levaram a uma determinada saída do modelo
Garantia de integridade relacional entre evidências visuais e metadados (como classes, scores e atributos)
2. Recuperação em tempo real e alta performance (Qdrant)

O Qdrant é responsável pela busca vetorial e recuperação semântica, oferecendo:

Latência extremamente baixa na recuperação de resultados (na ordem de milissegundos)
Busca por similaridade baseada em embeddings, permitindo encontrar padrões visuais complexos
Capacidade de escalar para grandes volumes de dados de visão computacional
3. Escalabilidade e eficiência de armazenamento (MinIO)

O MinIO atua como camada de armazenamento de objetos, permitindo:

Separação eficiente entre dados estruturados e mídias pesadas (imagens, mapas de explicação etc.)
Redução de carga sobre bancos relacionais e vetoriais
Organização eficiente de grandes volumes de dados sem perda de desempenho
4. Persistência de evidências explicativas (XAI)

Um diferencial importante do sistema é tratar explicações como dados permanentes:

Mapas de explicabilidade (como Grad-CAM) deixam de ser descartáveis e passam a ser registrados
Cada inferência pode ser reproduzida e analisada posteriormente
Possibilidade de estudos comparativos entre variações e perturbações da entrada
5. Arquitetura desacoplada e moderna

A proposta segue um modelo de separação clara de responsabilidades:

Banco relacional para lógica e auditoria
Banco vetorial para similaridade e inteligência semântica
Storage para arquivos pesados e escaláveis

Isso evita sobrecarregar uma única tecnologia com responsabilidades que não são ideais para ela.

Conclusão

O principal valor do projeto está em construir um sistema capaz de unir auditoria, desempenho e escalabilidade, mantendo a explicabilidade da IA como um elemento persistente e analisável. Na prática, trata-se de uma arquitetura que permite compreender e rastrear decisões de modelos de forma estruturada, confiável e reutilizável, especialmente em contextos onde transparência e confiabilidade são fundamentais.