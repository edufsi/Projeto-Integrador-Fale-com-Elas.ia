# Guia de Fontes de Dados e Metodologia de Construção de Datasets

Este guia complementa os três documentos de classificação
(`classificacao_violencia_genero_IA.md`, `classificacao_intencao_relato_IA.md`
e `classificacao_gravidade_risco_IA.md`) e a arquitetura do chatbot. Ele
concentra o que é comum às três tarefas: **onde procurar dados** e **como
construir bons datasets**.

### Como ler os níveis de verificação

  Marca             Significado
  ----------------- ---------------------------------------------------------
  **Aberto**        A página, o repositório ou o artigo foi aberto na pesquisa
  **Via busca**     Apareceu em resultado de busca, mas a fonte primária não
                    foi aberta
  **NÃO VERIFICADO** Não foi possível confirmar; conferir antes de citar

Os links e números devem ser reconferidos antes de entrarem no
trabalho final. Datasets mudam de endereço e de condições de acesso. Os
itens com tamanhos e licenças foram extraídos de páginas e artigos, e
podem ter mudado desde então.

------------------------------------------------------------------------

## 1. Resumo: o que existe e o que falta

  Tarefa                        Existe publicamente em PT-BR?   O que serve como apoio
  ----------------------------- ------------------------------- --------------------------------------------
  A --- Tipo de violência       **Não encontrado**              Corpora de misoginia/toxicidade (negativos e
                                                                transferência); WomenHelp e EXIST (es/en)
  B --- Intenção                **Não encontrado**              FAQs institucionais (dúvida); trabalhos em
                                                                inglês sobre relato × conselho
  C --- Gravidade               **Não encontrado**              Rubrica do FONAR; WomenHelp (es, escala
                                                                ordinal); datasets de risco de suicídio

Conclusão: **os rótulos das três tarefas terão de ser construídos pela
equipe.** Os dados existentes servem como negativos, material de
transferência, base de conhecimento (RAG) e referência metodológica. A
seção 3 diz como construir esses rótulos de forma defensável.

------------------------------------------------------------------------

## 2. Catálogo de fontes

### 2.1 Violência contra a mulher em português

  Fonte                            Conteúdo                              Acesso / licença                        Verif.         Utilidade
  -------------------------------- ------------------------------------- --------------------------------------- -------------- ---------------------------
  Boletins de ocorrência do DF     162 BOs de 142 casos (2017--2021),    **Não público** (dados anonimizados     Aberto         Referência metodológica
  (Lima & Oliveira)                rótulo de risco por proximidade do    cedidos pela perícia). arXiv:2401.12980                para C
                                   feminicídio; LSTM com 66% de                                                  
                                   acurácia                                                                      

  CEIA-COREJUR/processos (Hugging  ~1,79 milhão de documentos jurídicos  Licença não verificada                  Aberto         RAG e frases jurídicas;
  Face)                            (TJDFT, TJRS, TJSC)                                                                          linguagem formal

  Relatos de violências contra a   Análise de 66 posts de uma conta de   CC BY 4.0, mas só a análise, não o      Aberto         Aponta fonte de relatos
  mulher (UFMG, Zenodo 16499020)   Instagram                             corpus                                                 em 1ª pessoa

### 2.2 Tarefas vizinhas em português (apoio e transferência)

  Fonte                         Tamanho / rótulos                         Licença                     Verif.   Utilidade
  ----------------------------- ----------------------------------------- --------------------------- -------- ---------------------------
  ToLD-Br                       ~21 mil tweets; 6 categorias, incl.       CC BY-SA 4.0                Aberto   Negativos e exemplos de
  (`JAugusto97/told-br`, HF)    misoginia; 3 anotadores por tweet                                                misoginia
  HateBR                        7.000 comentários do Instagram (3.500     CC BY-NC 4.0 (só pesquisa)  Aberto   Negativos, transferência
  (`franciellevargas/HateBR`)   ofensivos / 3.500 não); inclui sexismo
  Portuguese Hate Speech        5.668 tweets; rótulos hierárquicos,       Só pesquisa, sem licença    Aberto   Negativos, transferência
  (Fortuna et al., 2019)        incl. sexismo                             explícita
  OLID-BR                       ~7,9 mil comentários, anotação em 3       CC BY 4.0                   Via      Negativos
  (`dougtrajano/olid-br`)       camadas                                                                   busca
  TuPyE                         ~43,7 mil documentos, 13 categorias       Não especificada;           Aberto   Maior corpus unificado com
  (`Silly-Machine/TuPyE-…`)     (misoginia: 1.675); reúne ToLD-Br,        mistura licenças                         misoginia
                                HateBR, Fortuna e TuPy
  LexMis-BR (UFG)               Léxico de misoginia e violência contra a  Código MIT; corpus fora do  Aberto   Funções de rotulagem e
                                mulher, 7 classes lexicais                repositório                              filtros
  `hugo-guigo/bertimbau-        Modelo binário de misoginia (BERTimbau),  Licença "other"             Aberto   Baseline
  misoginia-ptbr` (HF)          11.120 textos

### 2.3 Saúde mental e risco em português

  Fonte                         Conteúdo                                   Licença          Verif.   Utilidade
  ----------------------------- ------------------------------------------ ---------------- -------- ----------------------------------
  Ideação suicida PT-BR         3.777 frases de tweets (1.090 positivas),  CC BY 4.0        Aberto   Média para B e C: é risco de
  (Boamente; Zenodo 18343886)   3 psicólogas anotadoras                                                suicídio, **não** violência de
                                                                                                       gênero
  SetembroBR                    ~3.900 usuários, 47 milhões de tweets      Textos **não     Aberto   Inacessível; dado sensível
                                                                           publicados**

### 2.4 Violência doméstica e de gênero em outros idiomas

  Fonte                          Idioma / tamanho                          Rótulos                         Acesso               Verif.
  ------------------------------ ----------------------------------------- ------------------------------- -------------------- ----------
  **WomenHelp** (IberLEF 2026)   Espanhol (norte do México). Gravidade:    Gravidade 0--3 (a classe grave  **Acesso não         Aberto
  CEUR-WS vol. 4273, paper 9     13.630 treino / 3.405 dev / 4.219 teste.  é ~4,5% do treino); tipos      confirmado**         (paper
                                 Tipos: 4.845 / 1.212 / 3.620              multilabel (7 rótulos, 3                              de
                                                                           anotadores)                                           partic.)
  **EXIST** (2021--2025)         Inglês e espanhol; ~7 mil (2021) a ~10    Sexismo, intenção (direct /     Formulário de        Aberto
  nlp.uned.es/exist2021, /2025   mil (2025) tweets                         reported / judgemental),        acesso (pesquisa)    (2021)
                                                                           categorias incl. violência
                                                                           sexual
  **EDOS** (SemEval-2023 T10)    Inglês; 20 mil textos (Gab e Reddit)      3 níveis, incl. ameaças         CC0-1.0              Aberto
  github.com/rewire-online/edos
  MeTooMA                        Inglês; 9.973 tweets                      Relevância, postura, atos de    MIT; só IDs de       Aberto
                                                                           fala (*allegation*)             tweets
  Subramani et al. (2018)        Inglês; 1.135 posts do Facebook anotados  *abuse* (relato) × *advice*     **Dataset não        Aberto
  arXiv:1804.03497                                                         (conselho); κ = 0,85            divulgado**
  Al-Garadi et al. (2022)        Inglês; 6.348 tweets                      Relato de violência por         Não verificado       Via
  *Array*                                                                  parceiro × outros                                    busca
  Guan et al. (2025) *JMIR*      Inglês; 294 posts (ampliados a 2.216 com  8 necessidades de informação    Não verificado       Via
  doi:10.2196/65397              GPT-3.5)                                  (jurídico, abrigo, polícia…)                         busca
  Wang et al. (2026)             Inglês; 9.013 posts de 12 subreddits      Auto-relato de violência        Dataset não          Aberto
  arXiv:2509.12288                                                         doméstica                       verificado
  Ha et al. (2022) DetectIPV     Inglês; treino com 1.062 frases de        Geral, física, emocional,       Material suplementar Via
  *J. Comput. Soc. Sci.*         **questionários**, teste com 618 frases   sexual, negativo                                     busca
                                 do Reddit

### 2.5 Crise e risco de suicídio (análogos para "emergência" e "gravidade")

  Fonte                        Conteúdo                                   Acesso                                  Verif.
  ---------------------------- ------------------------------------------ --------------------------------------- ---------
  UMD Reddit Suicidality v2    11.129 usuários + controles; risco         **Exige aprovação de comitê de ética    Aberto
  (Shing 2018; Zirikly 2019)   None / Low / Moderate / Severe             (IRB) e acordo assinado**
  RSD-15K                      14.613 posts de 1.265 usuários             Formulário com e-mail institucional;    Aberto
  (`aascode/RSD_15K`)                                                     uso comercial proibido
  CAMS                         5.051 posts com causas                     Licença não declarada                   Aberto
  Crisis Text Line             ---                                        **Sem dados abertos**                   Via
                                                                                                                  busca

Nenhum dataset aberto de mensagens de *helpline* com rótulo de intenção
(dúvida / relato / emergência) foi encontrado.

### 2.6 Dados oficiais (estatísticas; quase nenhum texto livre)

  Fonte                                        Uso
  -------------------------------------------- --------------------------------------------------
  Painel do Ligue 180 / ONDH (gov.br, 2020--)  Distribuição de tipos de violência, perfil de vítima e
                                               agressor; **calibrar proporções do dataset**
  SSP-RS, indicadores de violência contra a    Contexto regional (Excel, 2012--2026)
  mulher
  Atlas da Violência (IPEA/FBSP); Anuário      Séries históricas e contexto
  Brasileiro de Segurança Pública
  DataSenado, Pesquisa Nacional de Violência   Survey (11 edições)
  contra a Mulher
  SINAN/VIVA (Ministério da Saúde)             Ficha de notificação: útil para entender o escopo de
                                               categorias; dado sensível e acesso restrito
  Agência Patrícia Galvão (dossiês)            Pesquisas e estatísticas

O acesso aos dados do ONDH em CSV no dados.gov.br **não foi confirmado**
(a página não abriu); verificar se há campo de relato em texto antes de
contar com ele. Pela descrição, parecem categóricos e anonimizados.

### 2.7 Textos oficiais para a classe "dúvida" e para o RAG

  Fonte                                              Observação
  -------------------------------------------------- ------------------------------------------------
  FAQ Lei Maria da Penha (Agência Gov, 25 perguntas) Pergunta-resposta; cita 190 e 180
  FAQ do CEVID / TJRS                                10 perguntas e respostas
  FAQs/cartilhas: TJPR, TJSC, Defensoria do RS,      Via busca; abrir e conferir
  Senado, MPDFT/PFDC
  TJDFT --- formas de violência                      Definições e exemplos dos 5 tipos (útil ao guia
                                                     de anotação)

**Licenças:** o uso para consulta é livre, mas a redistribuição de
textos de portais do governo deve respeitar a licença de cada site
(alguns usam CC BY-ND, que proíbe obras derivadas).

### 2.8 Instrumentos validados de avaliação de risco

  Instrumento          O que é                                            Fonte
  -------------------- -------------------------------------------------- ----------------------------------
  **FONAR** (Brasil)   Formulário Nacional de Avaliação de Risco (Lei     Guia CNJ (nov/2025); formulário
                       14.149/2021; Res. Conjunta CNJ/CNMP 5/2020).       TJDFT
                       A adaptação do TJDFT tem 27 itens. O Guia CNJ de
                       2025 classifica o risco em **extremo, grave e
                       moderado**; uma página do TJPR fala em baixo,
                       médio e extremo (versão anterior?). **A
                       discrepância deve ser conferida.** O guia diz que
                       a classificação não é só soma de pontos.
  Danger Assessment    20 itens sim/não + calendário de severidade;       Campbell, Webster & Glass (2009),
  (Campbell)           revisão de 2009 com pesos (AUC 0,90). Uso livre    *J Interpers Violence* 24(4)
                       só para pesquisa/ensino
  LAP (Maryland)       11 perguntas, derivadas do Danger Assessment;      MNADV
                       restrições de modificação
  DASH (SafeLives)     Checklist de risco alto; encaminhamento ao MARAC   safelives.org.uk
  ODARA / SARA /       13 / 20 / 10 itens (reincidência e risco)          Justice Canada
  B-SAFER
  CTS2 (Straus)        Escala de táticas de conflito, 78 perguntas;       Straus (1996)
                       há adaptação para o português do Brasil (via
                       busca). Mede táticas, não letalidade

------------------------------------------------------------------------

## 3. Metodologia de construção de datasets

### 3.1 Princípio geral: construir em ciclos (MATTER / MAMA)

O processo de referência é **MATTER** (*Model, Annotate, Train, Test,
Evaluate, Revise*), descrito por Pustejovsky & Stubbs (*Natural Language
Annotation for Machine Learning*, O'Reilly, 2012). O laço interno é o
**MAMA** (*Model-Annotate*). A ideia é tratar a mudança do esquema de
anotação como parte do método, e não como falha.

``` text
   Modelar (taxonomia + guia v_n)
        │
        ▼
   Anotar (lote pequeno)
        │
        ▼
   Treinar (baseline simples)
        │
        ▼
   Testar / Avaliar (concordância + erros)
        │
        ▼
   Revisar guia → v_(n+1)
```

**Aplicação:** fazer ao menos **3 iterações**, com lotes pequenos
(dezenas a poucas centenas de itens) e guia versionado (v1, v2, v3).

### 3.2 Guia de anotação

Conteúdo mínimo:

-   definições operacionais de cada classe;
-   exemplos positivos **e negativos**;
-   **casos de fronteira com a decisão tomada**;
-   regras de precedência (por exemplo, "emergência prevalece");
-   instruções sobre o que **não** inferir além do texto.

Piloto: 50--100 itens, 2--3 anotadores, discussão aberta. **Cada
desacordo vira uma regra ou um exemplo do guia.**

### 3.3 Concordância entre anotadores

  Tarefa                  Métrica                                       Observação
  ----------------------- --------------------------------------------- -----------------------------------
  A (multilabel)          α de Krippendorff e κ por rótulo (binário);   Reportar também a concordância
                          concordância exata do conjunto                exata do conjunto
  B (intenção, classe     κ por classe; F1 de concordância na classe    O κ global esconde a classe rara
  rara)                   *emergência*
  C (ordinal 0--4)        κ ponderado (quadrático) e α ordinal          Penaliza mais 0↔4 que 2↔3

Referências de interpretação: Landis & Koch (1977) (0,61--0,80 =
substancial); Krippendorff costuma recomendar α ≥ 0,80, com α ≥ 0,67
como limite tentativo. **Esses limiares são convenções discutidas na
literatura** (por exemplo, Wong et al., ACL 2021, criticam limiares
fixos); reportar o valor **com intervalo de confiança** e interpretar
com cautela.

Tamanho da amostra de dupla anotação (**heurística, não regra**):
300--500 itens com 2--3 anotadores, garantindo ao menos 30--50
positivos nas classes raras, com IC por reamostragem (*bootstrap*).

### 3.4 Desacordo humano não é só ruído

Em tarefas subjetivas, o desacordo carrega informação (Pavlick &
Kwiatkowski, 2019). Röttger et al. (NAACL 2022) distinguem dois
paradigmas:

  Paradigma         Ideia                                        Uso neste projeto
  ----------------- -------------------------------------------- --------------------------------
  **Prescritivo**   Regras claras; o desacordo é erro            A (tipo) e B (intenção):
                                                                 definem o que é emergência
  **Descritivo**    O desacordo é informação                     C (gravidade): **guardar todos
                                                                 os rótulos individuais**

Para C: treinar com **rótulo suave** (distribuição entre anotadores) ou
com a média, e avaliar considerando o desacordo (Fornaciari et al.,
NAACL 2021; Davani et al., TACL 2022; Uma et al., JAIR 2021). Para obter
rótulo único, usar adjudicação por especialista **sem apagar os rótulos
originais**.

### 3.5 Amostragem e cobertura

-   **Busca por palavras-chave gera viés** (o ToLD-Br usou coleta dupla:
    por termos e por perfis).
-   **Estratificar** por classe e por fonte.
-   **Sobreamostrar a classe rara** (*emergência*) com anotação
    dedicada.
-   **Negativos difíceis:** menções de violência em notícias, ficção,
    política, piadas, letras de música. Sem eles, o modelo aprende
    "palavra de violência = violência".
-   **Active learning** (Settles, 2009): priorizar para anotação os
    exemplos em que o baseline tem mais incerteza.
-   **Contrast sets** (Gardner et al., 2020): pares com mudança mínima
    que altera o rótulo ("ele me ameaçou" × "ele ameaçou o time
    adversário").
-   **CheckList** (Ribeiro et al., ACL 2020): testes comportamentais
    (negação, mudança de tempo verbal, terceira pessoa).

### 3.6 Anotação assistida por LLM e supervisão fraca

A literatura mostra que LLMs podem anotar bem algumas tarefas (Gilardi
et al., PNAS 2023; Törnberg, 2023), mas também que **a anotação
automática exige validação humana** (Pangakis et al., 2023) e que as
conclusões podem mudar conforme prompt e modelo (Baumann et al., 2025,
preprint). Esses estudos usam tarefas de menor risco (política, tópico).
**Não há evidência verificada de que se generalizem para gravidade e
emergência em violência de gênero em português.**

Protocolo recomendado:

1.  Usar o LLM para **pré-anotar e priorizar**, nunca como verdade.
2.  Congelar o prompt **antes** de medir.
3.  Medir o LLM contra o ouro humano (κ e F1 **por classe**), em
    amostra estratificada.
4.  Relatar o desempenho na classe crítica separadamente.
5.  Usar **funções de rotulagem** (léxicos como o LexMis-BR, regex) para
    **recuperar candidatos**, não para rotular o teste. Referência:
    *data programming*/Snorkel (Ratner et al., NeurIPS 2016; VLDB 2017).

### 3.7 Dados sintéticos gerados por LLM

Referências: Meng et al. (NeurIPS 2022); Self-Instruct (Wang et al.,
ACL 2023); Li et al. (EMNLP 2023), que discute limitações em tarefas
mais subjetivas; AttrPrompt (Yu et al., NeurIPS 2023), em que prompts
com **atributos diversos** superam prompts só com a classe; Shumailov
et al. (*Nature*, 2024) sobre colapso ao treinar recursivamente com
dados gerados.

Regras:

-   Gerar com **atributos cruzados:** tipo de violência, registro
    (formal/informal), região, relação com o agressor, nível de detalhe,
    tamanho, erros de digitação.
-   Usar **só no treino**, nunca na validação nem no teste.
-   Marcar cada exemplo com `origem = sintético`.
-   Revisar manualmente uma amostra.
-   Fazer **ablação:** comparar o desempenho com e sem sintético em
    teste 100% humano.
-   O sintético **não substitui** a classe rara real: textos de LLM
    costumam ser limpos, completos e didáticos.

### 3.8 Divisão sem vazamento e conjunto ouro

-   **Desduplicar**, inclusive quase-duplicatas, **antes** de dividir
    (Lee et al., ACL 2022; Elangovan et al., EACL 2021).
-   Dividir por **autor, *thread* e fonte** (Geva et al., EMNLP 2019:
    modelos aprendem o anotador).
-   Se possível, o teste deve ser anotado por pessoas **diferentes** das
    do treino.
-   **Teste ouro:** 100% humano, dupla anotação adjudicada, **congelado
    antes de qualquer experimento**.
-   Conjuntos separados para a classe rara e para desafio.
-   **Quanto anotar?** Não há número mínimo universal. Construir uma
    **curva de aprendizado** (25%, 50%, 75%, 100% do treino) e parar
    quando o F1 da classe crítica estabilizar (resultados de *few-shot*,
    como SetFit, mostram que poucos exemplos podem bastar em algumas
    tarefas, mas isso não foi verificado para este domínio).

### 3.9 Escala ordinal subjetiva: *best-worst scaling*

Para a gravidade, escalas de Likert tendem a ser pouco confiáveis.
Kiritchenko & Mohammad (ACL 2017) mostram que a comparação **melhor-pior**
(*best-worst scaling*, BWS) é mais confiável com o mesmo número de
anotações.

**Aplicação:** apresentar tuplas de 4 textos e pedir o **mais grave** e o
**menos grave**; converter em escores contínuos e depois em faixas 0--4
por limiares. Esses estudos usam palavras e frases curtas; para relatos
longos e pesados, o custo de leitura é maior. Usar BWS num **subconjunto**
(300--500 textos) para **calibrar os limiares e ancorar os exemplos do
guia**, e usar a escala direta no restante.

### 3.10 Documentação do dataset

Preencher um **datasheet** por dataset:

-   *Datasheets for Datasets* (Gebru et al., arXiv:1803.09010);
-   *Data Statements for NLP* (Bender & Friedman, TACL 2018): inclui o
    perfil dos anotadores e a variedade linguística;
-   *Data Cards* (Pushkarna et al., FAccT 2022);
-   *Dataset Nutrition Label* (Holland et al., 2018).

Incluir seções específicas: **proporção de texto sintético**, **uso
indevido** (por exemplo, "não usar para triagem automática de vítimas
sem supervisão humana"), perfil dos anotadores e concordância.

### 3.11 Quem anota e com quais ferramentas

-   **A e B:** anotadores treinados com o guia costumam bastar.
-   **C:** incluir ao menos **uma pessoa com formação na área**
    (psicologia, serviço social, direito, rede de atendimento) para
    calibrar e adjudicar.
-   **Evitar crowd aberto** em conteúdo traumático (Steiger et al.,
    CHI 2021, sobre o bem-estar de moderadores de conteúdo).
-   **Onde recrutar:** não há fonte verificada. Sugestão: pós-graduandos
    e colegas de psicologia, direito e serviço social da UFRGS e
    núcleos de estudos de gênero, com termo de consentimento e
    treinamento.

  Ferramenta        Licença         Observação
  ----------------- --------------- -------------------------------------------
  Label Studio      Código aberto   Multilabel e ordinal, com revisão
  doccano           Código aberto   Mais simples, só texto
  INCEpTION         Código aberto   Mais potente; curva de aprendizado maior
  Argilla           Código aberto   Bom para revisar pré-anotação de LLM
  Prodigy           Comercial       Opção paga

------------------------------------------------------------------------

## 4. Ética, privacidade e aspectos legais da coleta

> Isto não é parecer jurídico. Confirmar com a orientação e o CEP.

-   **Resolução CNS 510/2016, art. 1º, parágrafo único:** pesquisas com
    informações de acesso público, de domínio público ou com bancos de
    dados agregados sem possibilidade de identificação individual não
    são registradas nem avaliadas pelo sistema CEP/CONEP. O Ofício
    Circular CONEP 17/2022 esclarece o enquadramento (o resumo obtido
    indica que depende de não haver identificação, nem indireta, e de
    não haver acesso restrito; **conferir o texto**).
-   **Implicação:** posts públicos em que pessoas relatam violência
    sofrida são de pessoas potencialmente identificáveis, o que
    enfraquece a dispensa. **Consultar o CEP/UFRGS ou a orientação antes
    de coletar** relatos reais, mesmo que a resolução pareça permitir a
    dispensa.
-   **LGPD:** dados de violência são dados pessoais sensíveis. O
    art. 11, II, "c" permite tratamento para estudos por órgão de
    pesquisa, "garantida, sempre que possível, a anonimização".
-   **Termos de uso do Reddit e do X:** não foram verificados; ler antes
    de coletar ou redistribuir. Distribuir apenas IDs ou rótulos quando
    não puder redistribuir o texto.
-   **Boas práticas de pesquisa com redes sociais:** Benton, Coppersmith
    & Dredze (EthNLP 2017); Chancellor et al. (FAT* 2019), sobre tensões
    éticas ao inferir saúde mental a partir de redes sociais; Fiesler &
    Proferes (2018), sobre expectativas de usuários de que tweets
    públicos sejam usados em pesquisa.
-   **Anonimização:** remover nomes, @, telefones, endereços e
    identificadores; considerar parafrasear.
-   **Bem-estar dos anotadores:** exposição limitada por sessão, aviso de
    conteúdo, opção de pular, contato de apoio psicológico e rodízio.
-   **Acesso ao dataset final:** sob pedido e com termo de uso, e não
    aberto, dado o risco de reidentificação.
-   **Licenças:** HateBR é CC BY-NC (sem uso comercial); ToLD-Br é
    CC BY-SA (a licença se propaga); os datasets unificados misturam
    licenças.

------------------------------------------------------------------------

## 5. Receita resumida por dataset

### Comum às três tarefas

1.  Consultar o CEP/UFRGS e a orientação sobre dados e participantes.
2.  Definir a política de anonimização.
3.  Escrever o guia v1 e abrir o datasheet.
4.  Rodar pilotos no ciclo MATTER (3 iterações).
5.  **Reservar o teste ouro desde o início** e congelá-lo.

### A --- Tipo de violência

Taxonomia da Lei Maria da Penha com regras de coocorrência → coleta
variada + negativos difíceis → piloto com 2--3 anotadores → dupla
anotação em 20--30% dos itens (heurística) → α por rótulo → LLM apenas
para pré-anotar → sintético diverso para rótulos raros → divisão por
autor → contrast sets.

### B --- Intenção

*Emergência* definida de forma **prescritiva** → sobreamostrar candidatos
(palavras-chave e *active learning*) → toda a classe *emergência* com
dupla revisão → κ e F1 por classe → teste humano estratificado →
sintético só no treino → limiar escolhido priorizando o recall da
emergência → uso documentado como apoio à triagem.

### C --- Gravidade

Anotação **descritiva**, guardando os rótulos individuais → rubrica
baseada no FONAR → BWS num subconjunto para calibrar níveis → κ ponderado
e α ordinal → treino com rótulo suave ou regressão ordinal → avaliação
com erro absoluto e κ ponderado → especialista só para adjudicar quando
for preciso rótulo único → **relatar o desacordo como resultado**.

------------------------------------------------------------------------

## 6. Referências principais

**Metodologia**

-   Pustejovsky & Stubbs (2012). *Natural Language Annotation for
    Machine Learning*. O'Reilly.
-   Artstein & Poesio (2008). Inter-Coder Agreement for Computational
    Linguistics. *Computational Linguistics* 34(4).
    https://aclanthology.org/J08-4004/
-   Antoine, Villaneau & Lefeuvre (2014). Weighted Krippendorff's alpha
    for ordinal data. EACL. https://aclanthology.org/E14-1058/
-   Wong et al. (2021). Cross-replication Reliability. ACL.
    https://aclanthology.org/2021.acl-long.548/
-   Gebru et al. Datasheets for Datasets. https://arxiv.org/abs/1803.09010
-   Bender & Friedman (2018). Data Statements for NLP. *TACL* 6.
    https://aclanthology.org/Q18-1041/
-   Pushkarna et al. (2022). Data Cards. FAccT.
    https://dl.acm.org/doi/10.1145/3531146.3533231
-   Röttger et al. (2022). Two Contrasting Data Annotation Paradigms for
    Subjective NLP Tasks. NAACL. https://aclanthology.org/2022.naacl-main.13/
-   Davani, Díaz & Prabhakaran (2022). Dealing with Disagreements.
    *TACL* 10. https://aclanthology.org/2022.tacl-1.6/
-   Fornaciari et al. (2021). Beyond Black & White. NAACL.
    https://aclanthology.org/2021.naacl-main.204/
-   Uma et al. (2021). Learning from Disagreement: A Survey. *JAIR* 72.
    https://doi.org/10.1613/jair.1.12752
-   Pavlick & Kwiatkowski (2019). *TACL* 7. https://aclanthology.org/Q19-1043/
-   Ribeiro et al. (2020). CheckList. ACL.
    https://aclanthology.org/2020.acl-main.442/
-   Gardner et al. (2020). Contrast sets. Findings of EMNLP.
    https://aclanthology.org/2020.findings-emnlp.117/
-   Settles (2009). Active Learning Literature Survey.
    https://burrsettles.com/pub/settles.activelearning.pdf
-   Kiritchenko & Mohammad (2017). Best-Worst Scaling More Reliable than
    Rating Scales. ACL. https://aclanthology.org/P17-2074/
-   Lee et al. (2022). Deduplicating Training Data. ACL.
    https://aclanthology.org/2022.acl-long.577/
-   Geva et al. (2019). Are We Modeling the Task or the Annotator?
    EMNLP. https://aclanthology.org/D19-1107/
-   Ratner et al. (2016). Data Programming. NeurIPS.
-   Ratner et al. (2017). Snorkel. VLDB.
    https://www.vldb.org/pvldb/vol11/p269-ratner.pdf

**LLM como anotador e dados sintéticos**

-   Gilardi et al. (2023). https://arxiv.org/abs/2303.15056
-   Törnberg (2023). https://arxiv.org/abs/2304.06588
-   Pangakis et al. (2023). https://arxiv.org/abs/2306.00176
-   Ziems et al. (2024). *Computational Linguistics* 50(1).
    https://aclanthology.org/2024.cl-1.8/
-   Tan et al. (2024). LLMs for data annotation: a survey. EMNLP.
    https://aclanthology.org/2024.emnlp-main.54/
-   Baumann et al. (2025). LLM Hacking (preprint).
    https://arxiv.org/abs/2509.08825
-   Meng et al. (2022). https://arxiv.org/abs/2202.04538
-   Wang et al. (2023). Self-Instruct.
    https://aclanthology.org/2023.acl-long.754/
-   Li et al. (2023). https://arxiv.org/abs/2310.07849
-   Yu et al. (2023). AttrPrompt. NeurIPS Datasets & Benchmarks.
-   Shumailov et al. (2024). *Nature* 631.
    https://www.nature.com/articles/s41586-024-07566-y

**Ética**

-   Benton, Coppersmith & Dredze (2017). https://aclanthology.org/W17-1612/
-   Chancellor et al. (2019). A Taxonomy of Ethical Tensions in Inferring
    Mental Health States from Social Media. FAT*.
-   Fiesler & Proferes (2018). *Social Media + Society* 4(1).
-   Steiger et al. (2021). CHI.
    https://dl.acm.org/doi/10.1145/3411764.3445092

**Domínio**

-   Leite et al. (2020). ToLD-Br. AACL.
    https://aclanthology.org/2020.aacl-main.91/
-   Lima & Oliveira. Risk Patterns in Brazilian Police Reports Preceding
    Femicides. https://arxiv.org/abs/2401.12980
-   Subramani et al. (2018). https://arxiv.org/abs/1804.03497
-   Wang et al. (2026). Digital Voices of Survival.
    https://arxiv.org/abs/2509.12288
-   Campbell, Webster & Glass (2009). The Danger Assessment. *J
    Interpers Violence* 24(4). doi:10.1177/0886260508317180
-   Guia CNJ do FONAR (nov/2025).
    https://www.cnj.jus.br/wp-content/uploads/2025/11/versao-final-rev-guia-interinstitucional-de-avaliacao-de-risco-para-aplicacao-do-fonar.pdf
