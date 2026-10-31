# Classificação de Gravidade e Nível de Risco com IA

## 1. Viabilidade do projeto

É viável desenvolver gratuitamente, usando o **Google Colab**, um modelo
de IA capaz de receber um relato em texto e estimar a **gravidade da
situação**, ou seja, o quanto a pessoa que escreveu está correndo perigo.

Esse é provavelmente o mais difícil dos três problemas (tipo de
violência, intenção do usuário e gravidade), por três motivos:

1.  A gravidade é **subjetiva** e depende de muitos fatores, nem sempre
    escritos no texto.
2.  As classes são **ordenadas** (risco baixo < moderado < alto), o que
    exige técnicas e métricas apropriadas.
3.  Um erro de subestimação pode ter **consequências graves**, então o
    modelo precisa ser avaliado com muito cuidado.

Exemplo de funcionamento:

``` text
Entrada:
"Ele me xingou durante a discussão de hoje."

Saída:
Gravidade: Baixa
```

``` text
Entrada:
"Ele já me empurrou outras vezes e agora está me ameaçando
porque eu disse que quero me separar."

Saída:
Gravidade: Alta
```

``` text
Entrada:
"Ele tem uma arma, disse que vai me matar hoje à noite e está
na frente da minha casa."

Saída:
Gravidade: Crítica
```

O principal desafio, como nos outros projetos, não é o poder
computacional, mas **definir um critério de gravidade defensável e
conseguir dados anotados por quem entende do assunto**.

> **Importante:** um modelo desse tipo deve ser tratado como uma
> **ferramenta de apoio à triagem**, nunca como uma avaliação de risco
> definitiva. A avaliação formal de risco deve ser feita por
> profissionais.

------------------------------------------------------------------------

## 2. Como definir "gravidade"

Este é o ponto central do projeto. Se a escala não for bem definida, o
modelo aprenderá apenas a opinião de quem anotou.

### Proposta de escala ordinal

  Nível   Nome                Descrição resumida
  ------- ------------------- --------------------------------------------------
  0       Sem risco aparente  Não há indício de violência ou perigo no texto
  1       Baixo               Conflito ou violência isolada, sem ameaça nem escalada
  2       Moderado            Violência recorrente, controle ou ameaças não letais
  3       Alto                Escalada, ameaça de morte, agressão grave, fatores de risco múltiplos
  4       Crítico             Perigo iminente ou em curso, risco de morte imediato

### Base conceitual: fatores de risco

Em vez de inventar critérios, é possível se apoiar na literatura e em
instrumentos já usados no Brasil. Um ponto de partida é o **Formulário
Nacional de Avaliação de Risco**, previsto na Lei 14.149/2021 e usado em
contexto de violência doméstica, além de trabalhos acadêmicos sobre
fatores de risco para feminicídio. (Recomenda-se consultar o formulário
original e a bibliografia para definir os critérios, em vez de depender
desta lista.)

Fatores de risco que costumam aparecer na literatura e que podem ser
reconhecidos em texto:

``` text
Letalidade
  - ameaça de morte
  - uso ou posse de arma
  - tentativa de enforcamento/estrangulamento
  - ameaça com faca, fogo, veículo

Escalada
  - violência aumentando em frequência ou intensidade
  - violência que passou a ocorrer na gravidez
  - agressões que antes não existiam

Gatilhos
  - separação recente ou desejo de se separar
  - ciúme extremo, controle de movimentos
  - perseguição (stalking), vigilância, mensagens insistentes
  - descumprimento de medida protetiva

Contexto
  - presença de filhos ou outros dependentes
  - isolamento social
  - dependência financeira
  - agressor com uso abusivo de álcool/drogas
  - ameaça de suicídio do agressor
  - risco de suicídio da própria vítima

Imediatismo
  - perigo "agora" ou "hoje"
  - agressor presente no local
  - vítima escondida / impedida de sair
```

Esses fatores ajudam em duas frentes: orientam o **guia de anotação** e
podem servir como **variáveis auxiliares** do modelo (ver seção 7).

------------------------------------------------------------------------

## 3. Classificação, regressão ou ordinal?

Há três formas de modelar o problema.

### Opção A --- Classificação multiclasse comum

``` text
Baixo / Moderado / Alto / Crítico
```

Simples, mas **ignora a ordem**: errar "Crítico" como "Baixo" é tratado
como o mesmo erro que errar "Crítico" como "Alto".

### Opção B --- Regressão

``` text
Texto → escore contínuo (0 a 10) → faixas
```

Respeita a ordem, mas exige definir escores finos que raramente têm
sustentação em anotação humana.

### Opção C --- Classificação ordinal

``` text
Texto → P(nível ≥ 1), P(nível ≥ 2), P(nível ≥ 3), P(nível ≥ 4)
```

Cada saída responde "a gravidade é pelo menos X?". Preserva a ordem e
mantém as classes discretas. Existem abordagens como CORAL e CORN para
isso.

**Recomendação:** começar com a Opção A como baseline e comparar com a
Opção C. A comparação entre elas já é um resultado interessante para o
trabalho.

Também é possível usar uma versão simplificada com **3 níveis** (baixo,
médio, alto) se a quantidade de dados não permitir 5.

------------------------------------------------------------------------

## 4. Possível arquitetura

``` text
                 Texto de entrada
                       │
                       ▼
             Pré-processamento
                       │
                       ▼
             Modelo pré-treinado
            (BERTimbau / XLM-R)
                       │
                       ▼
          Cabeça de classificação ordinal
                       │
                       ▼
        P(≥1)  P(≥2)  P(≥3)  P(≥4)
                       │
                       ▼
               Nível de gravidade
```

Exemplo de saída:

``` text
P(gravidade ≥ Baixa):    0.99
P(gravidade ≥ Moderada): 0.93
P(gravidade ≥ Alta):     0.71
P(gravidade ≥ Crítica):  0.18

→ Nível previsto: Alta
```

Como o custo de subestimar é maior que o de superestimar, pode-se
**deslocar os limiares** para o lado conservador:

``` text
P(gravidade ≥ Alta) > 0.40  →  classificar como Alta
```

------------------------------------------------------------------------

## 5. Treinar do zero ou fazer fine-tuning?

Mais uma vez, o fine-tuning de um modelo pré-treinado é o caminho
adequado.

``` text
BERTimbau pré-treinado
        ↓
relatos com nível de gravidade
        ↓
GPU do Google Colab
        ↓
modelo especializado
```

Modelos para avaliar:

-   BERTimbau (base; large se houver GPU/tempo)
-   XLM-R
-   mBERT
-   DistilBERT multilíngue

Textos de gravidade tendem a ser **mais longos** que perguntas curtas, e
detalhes importantes podem aparecer no final. Convém usar comprimento
máximo de 256 a 512 tokens e verificar quantos relatos estouram esse
limite.

------------------------------------------------------------------------

## 6. O Google Colab é suficiente?

Sim, para o BERTimbau base e datasets de poucos milhares de exemplos, a
GPU gratuita do Colab é suficiente. Com textos de 512 tokens, pode ser
necessário reduzir o *batch size* ou usar *gradient accumulation* e
precisão mista (fp16).

Tecnologias:

-   Python
-   Google Colab
-   PyTorch
-   Hugging Face Transformers
-   scikit-learn
-   pandas
-   bibliotecas de classificação ordinal (por exemplo, implementações de
    CORAL/CORN para PyTorch)

------------------------------------------------------------------------

## 7. Estratégias para melhorar a modelagem

### 7.1 Modelo apenas texto

``` text
Texto → BERTimbau → gravidade
```

### 7.2 Modelo com fatores de risco como tarefa auxiliar (multitarefa)

``` text
Texto → BERTimbau ─┬─► gravidade (ordinal)
                   └─► fatores de risco (multilabel)
                        arma? ameaça de morte? estrangulamento?
                        perseguição? separação recente? filhos?
```

Essa abordagem tem vantagens:

-   força o modelo a identificar os **sinais concretos** de risco;
-   fornece **explicabilidade** ("gravidade alta porque foram detectados
    arma e ameaça de morte");
-   a anotação dos fatores é **mais objetiva** que a anotação direta da
    gravidade, pois pergunta "o texto menciona arma?" em vez de "quão
    grave é?".

### 7.3 Modelo em duas etapas

``` text
Texto → extrai fatores de risco → regra/ponderação → gravidade
```

Mais transparente, porém depende de boa extração dos fatores.

### 7.4 Modelo híbrido (recomendado para uso prático)

``` text
Texto
  │
  ├──► Regras de segurança (arma + ameaça de morte, "hoje", ...)
  │            │ se disparar → piso mínimo "Alta"
  │            ▼
  └──► Modelo ordinal ──► nível + probabilidades
                                   │
                                   ▼
                  Interface sempre mostra 180 / 190
```

------------------------------------------------------------------------

## 8. Quanto de dados gratuitos existe?

Pela pesquisa feita (ver `guia_datasets_metodologia_fontes.md`),
**não foi encontrado nenhum corpus público em português com relatos
rotulados por gravidade**. O único trabalho brasileiro encontrado com
texto e rótulo de risco usa dados policiais restritos. Existem, no
entanto, análogos úteis em outros idiomas e instrumentos oficiais para
fundamentar a escala.

### O que existe e qual papel pode ter

  Fonte                           Idioma   Conteúdo                         Papel no projeto
  ------------------------------- -------- -------------------------------- ---------------------------------
  **WomenHelp** (IberLEF 2026)    es       Relatos de centros de            **Principal análogo.** Escala
                                           atendimento a vítimas.           ordinal de gravidade com texto
                                           Gravidade 0--3: 13.630 treino /  real. Acesso **não confirmado**
                                           3.405 dev / 4.219 teste; a
                                           classe grave é ~4,5% do treino
  **UMD Reddit Suicidality v2**   en       Risco None/Low/Moderate/Severe   Análogo de escala ordinal e de
                                           (11.129 usuários + controles)    "iminente". **Exige IRB e
                                                                            acordo assinado**
  **RSD-15K**                     en       14.613 posts, risco de suicídio  Análogo; acesso por formulário
                                                                            institucional
  Boamente (ideação suicida)      pt       3.777 frases, 3 psicólogas       Análogo em PT, mas **risco de
                                                                            suicídio**, não de violência
  Lima & Oliveira (BOs do DF)     pt       162 BOs; risco por proximidade   **Dados restritos.** Referência
                                           do feminicídio; 66% de acurácia  metodológica (e aviso sobre
                                                                            rótulos-proxy)
  **FONAR** (Guia CNJ 2025)       pt       Formulário e guia de avaliação   **Rubrica** de fatores e níveis
                                           de risco                         para anotar
  Danger Assessment, DASH, LAP,   en       Itens de risco e pesos           Lista de fatores de risco com
  ODARA, SARA, B-SAFER                                                      validação empírica
  Painel do Ligue 180,            pt       Estatísticas                     Contexto e calibração de
  SSP-RS, Atlas, Anuário                                                    proporções
  Crisis Text Line                ---      ---                              **Sem dados abertos**

### Lições da literatura

-   O WomenHelp, melhor análogo, reportou **macro-F1 em torno de 0,58**
    para gravidade em 4 níveis, com o principal erro na fronteira
    *moderada/grave*. Isso sugere que **a dificuldade já aparece com
    dados reais e anotação cuidadosa**: não é razoável esperar
    desempenho perfeito.
-   O estudo brasileiro com BOs usou um **rótulo-proxy** (BO feito a
    menos de 1 ano do feminicídio = "alto risco"). Rótulos-proxy são
    úteis, mas **não medem gravidade percebida no texto**: um relato pode
    ser grave e a vítima nunca ter sido assassinada, ou o contrário.
-   Rótulos de risco em dados de crise (suicídio) são mais abundantes,
    mas **não se transferem automaticamente** para violência de gênero.

### Atenção ao FONAR

O Guia CNJ de nov/2025 classifica o risco em **extremo, grave e
moderado**, enquanto uma página do TJPR menciona baixo, médio e
extremo (possivelmente versão anterior). **Conferir qual é a versão
vigente** antes de mapear a escala do projeto para a do FONAR. O guia
afirma que a classificação não é só soma de pontos e exige julgamento
profissional, o que reforça que o modelo é apenas apoio.

### Lacunas

-   Nenhum corpus PT-BR de relatos com gravidade.
-   Nenhum mapeamento validado entre **texto livre** e os níveis do
    FONAR ou do Danger Assessment.
-   Os dados reais (BOs, prontuários) são restritos.

### Consequência

``` text
Dados públicos  →  rubrica (FONAR/DA), análogos, negativos
Dados próprios  →  rótulos de gravidade e de fatores (treino e TESTE OURO)
Especialistas   →  calibração da escala e adjudicação
```

------------------------------------------------------------------------

## 9. Construção de um dataset próprio

A metodologia geral (ciclo MATTER, concordância, desacordo, BWS,
documentação, ética) está em `guia_datasets_metodologia_fontes.md`. Aqui
está a aplicação à gravidade, que é a tarefa **mais subjetiva** dos
três projetos.

### 9.1 Escala e mapeamento para o FONAR

Escala de partida (a refinar com especialistas):

  Nível   Nome                Relação sugerida com o FONAR (a validar)
  ------- ------------------- -----------------------------------------------
  0       Sem risco aparente  Fora da escala do FONAR
  1       Baixo               Abaixo de "moderado" (ou não classificável)
  2       Moderado            Moderado
  3       Alto                Grave
  4       Crítico             Extremo

O mapeamento deve ser conferido com a versão vigente do guia e com
profissional da área. Se o número de exemplos não permitir cinco níveis,
usar **três** (baixo / moderado-grave / extremo).

### 9.2 Anotar primeiro os fatores, depois a gravidade

Perguntar "o texto menciona arma?" é mais objetivo que "quão grave é?".
Duas camadas de anotação:

``` text
Camada 1 (objetiva)  →  fatores de risco presentes no texto
                        (arma, ameaça de morte, estrangulamento,
                         perseguição, separação recente, filhos,
                         descumprimento de medida protetiva, escalada,
                         agressor presente, ...)
Camada 2 (subjetiva) →  nível de gravidade 0-4
```

A lista de fatores deve vir do **FONAR e dos instrumentos validados**
(Danger Assessment, DASH, ODARA etc.), e não ser inventada. Isso também
alimenta o modelo multitarefa (seção 7.2).

### 9.3 Paradigma de anotação: descritivo e com vários anotadores

Gravidade é subjetiva, então o desacordo **carrega informação**:

-   **3 anotadores por exemplo**, ao menos no teste e em uma boa parte
    do treino.
-   **Guardar todos os rótulos individuais.**
-   Treinar com **rótulo suave** (distribuição entre anotadores) ou com
    a média; avaliar levando o desacordo em conta.
-   Reportar **κ ponderado quadrático e α ordinal**, com intervalo de
    confiança. O desacordo é um **resultado**, e não apenas problema.
-   Adjudicação por especialista **apenas quando for necessário um
    rótulo único**, sem apagar os originais.

### 9.4 *Best-worst scaling* para calibrar a escala

Escalas diretas (Likert) podem ser pouco confiáveis. Em um subconjunto
de 300--500 textos:

``` text
Mostrar 4 relatos → "qual é o MAIS grave?" "qual é o MENOS grave?"
Repetir com várias combinações
Converter em escore contínuo → definir limiares dos níveis 0-4
```

Isso calibra os limiares e fornece **exemplos âncora** para o guia. Nos
demais textos, usar a escala direta. (Os estudos de BWS usam textos
curtos; para relatos longos e pesados, o custo de leitura é maior.)

### 9.5 Quem anota

-   Pelo menos **uma pessoa com formação na área** (psicologia, serviço
    social, direito, rede de atendimento) para calibrar a escala e
    adjudicar.
-   Anotadores treinados com o guia, com sessões curtas, aviso de
    conteúdo e apoio.
-   Evitar crowd aberto neste tipo de conteúdo.
-   **Anotadores do teste diferentes dos do treino**, sempre que
    possível.

### 9.6 Trilhas de obtenção dos textos

  Trilha                            Como                                        Cuidados
  --------------------------------- ------------------------------------------- ----------------------------
  **T1 --- Elicitação por           Voluntários escrevem relatos a partir de    Principal fonte do teste.
  cartões de cenário**              cartões com **combinações de fatores** e     Pessoas diferentes das do
                                    nível-alvo, em registro realista            treino
  **T2 --- Casos públicos           Reescrever reportagens e relatos públicos   Consultar CEP/orientação;
  reescritos em 1ª pessoa**         em 1ª pessoa, removendo identificadores     atenção ao viés (notícias
                                                                                tendem ao extremo)
  **T3 --- Cartilhas e guias**      Exemplos de situações de risco em guias     Respeitar licenças
                                    institucionais
  **T4 --- Sintético com LLM**      Geração por atributos (seção 10)            **Somente treino**
  **T5 --- Dados reais anonimizados**  Parceria com instituição               Exige autorização, ética e
                                                                                anonimização rigorosa

### 9.7 Cartões de cenário para gravidade

Combinar fatores e variar o contexto, para cobrir a escala:

``` text
Fatores:  [ameaça de morte, separação recente, arma, filhos]
Tempo:    presente imediato | últimos dias | meses | passado remoto
Registro: formal | informal | fragmentado | minimizador
Tamanho:  uma frase | parágrafo curto
→ pedir 3-5 relatos diferentes por combinação
```

Incluir de propósito:

-   **Relatos minimizadores** ("foi só uma briga", "ele se exaltou")
    com fatores graves ocultos;
-   **Relatos exagerados** de situações de baixo risco;
-   **Negações** ("ele nunca me ameaçou com arma");
-   **Passado vs. presente** ("há 5 anos" × "hoje de manhã").

A gravidade-alvo do cartão é apenas um rótulo inicial: **os anotadores
independentes decidem o rótulo final**, para evitar circularidade
(escrever sabendo o nível e depois "confirmar").

### 9.8 Dimensionamento

Valores hipotéticos de partida, a ajustar com curva de aprendizado:

  Nível                  Exemplos
  ------------------ ------------
  0 --- Sem risco             500
  1 --- Baixo                 700
  2 --- Moderado              800
  3 --- Alto                  800
  4 --- Crítico               500
  **Total**              **3.300**

Os níveis extremos são raros na realidade, mas precisam de exemplos
suficientes para o treino e o teste, então são **sobreamostrados**.

### 9.9 Divisão, teste ouro e testes comportamentais

-   Desduplicar antes de dividir; dividir por autor e fonte.
-   **Teste ouro 100% humano**, 3 anotadores, congelado antes dos
    experimentos.
-   **Conjunto de desafio** com pares de sensibilidade (seção 13): a
    previsão deve subir quando se acrescenta "com uma arma", e cair
    quando o relato é de muito tempo atrás.
-   Reportar a **matriz de confusão ordinal** e o erro por nível, com
    atenção à fronteira *moderado/grave* (onde o análogo WomenHelp mais
    errou).

### 9.10 Documentação e ética

-   Datasheet com a escala, o mapeamento para o FONAR, o perfil e a
    formação dos anotadores, a concordância e a proporção de sintético.
-   **Uso indevido declarado:** não usar o modelo para decidir sozinho
    sobre risco de alguém.
-   Dados reais: CEP/orientação, LGPD, anonimização.
-   Textos de cenários graves escritos para o projeto não devem ser
    publicados de modo a ajudar a burlar o sistema.

------------------------------------------------------------------------

## 10. Data augmentation e dados sintéticos

Valem as cautelas dos outros projetos (guia, seção 3.7), e mais:

-   Textos de LLM são longos, organizados e explícitos. Relatos reais de
    gravidade alta costumam ser **curtos, fragmentados, emocionais ou,
    ao contrário, minimizadores**.
-   **Minimização é um fenômeno real:** muitas vítimas descrevem situações
    graves em tom brando. O sintético deve incluir esse estilo, e o
    teste deve avaliá-lo.
-   O LLM pode **superestimar ou subestimar** gravidade de forma
    inconsistente. O rótulo de um exemplo sintético **não é verdade**:
    deve ser conferido por anotadores humanos independentes.
-   Gerar com **atributos cruzados** (fatores, tempo, registro, tamanho)
    a partir dos cartões de cenário.
-   Marcar `origem = sintetico`; **usar só no treino**.
-   **Ablação** com teste ouro humano: sem melhoria no teste, não usar.
-   **Teste de sensibilidade** do modelo treinado: inserir/remover
    sinais de risco e verificar se a previsão muda de forma coerente.

Técnicas complementares: variação de estilo, ruído realista (erros de
digitação, falta de acento, abreviações) e retrotradução.

------------------------------------------------------------------------

## 11. LLM como anotador e pseudo-rótulos

Usar um LLM para atribuir gravidade e tratar o resultado como verdade é
**especialmente arriscado**: a tarefa é subjetiva, LLMs podem ser
inconsistentes entre execuções e sensíveis ao *prompt*, e os estudos
que mostram bom desempenho de LLMs como anotadores tratam de tarefas
menos delicadas (guia, seção 3.6). Não há evidência verificada para
gravidade de violência em português.

Protocolo:

1.  LLM só para **pré-anotar e priorizar** (*weak labels*).
2.  Congelar o prompt antes de medir.
3.  Rodar o LLM **várias vezes** e medir a **consistência entre
    execuções**.
4.  Comparar com a anotação humana em um subconjunto e reportar
    **κ ponderado, MAE e erro de subestimação** (casos Alto/Crítico
    classificados como baixo).
5.  **Nunca** usar pseudo-rótulos no teste ouro.

A concordância entre humanos, LLM e modelo ajustado é, em si, um
resultado de pesquisa possível (ver seção 19).

------------------------------------------------------------------------

# 12. Comparação entre modelos

### Modelo 0 --- Baseline por regras / escore de fatores

``` text
Detecção de palavras-chave de risco
   ↓
soma ponderada
   ↓
nível
```

### Modelo 1 --- Baseline tradicional

``` text
TF-IDF
   ↓
Regressão Logística / SVM / Ridge (ordinal por limiar)
   ↓
nível
```

### Modelo 2 --- Transformer, classificação comum

``` text
BERTimbau
   ↓
fine-tuning (cross-entropy)
   ↓
nível
```

### Modelo 3 --- Transformer, classificação ordinal

``` text
BERTimbau
   ↓
fine-tuning (CORAL / CORN)
   ↓
nível
```

### Modelo 4 --- Transformer multitarefa (gravidade + fatores)

``` text
BERTimbau
   ↓
fine-tuning (gravidade + fatores de risco)
   ↓
nível + fatores detectados
```

### Modelo 5 (opcional) --- Dados aumentados / multilíngue

``` text
BERTimbau/XLM-R + dados sintéticos ou multilíngues
```

Essa comparação permite investigar se **respeitar a ordem das classes**
e **modelar os fatores de risco** realmente ajudam.

------------------------------------------------------------------------

# 13. Métricas de avaliação

### Métricas gerais

-   Accuracy (informativa, mas insuficiente)
-   F1 macro
-   Matriz de confusão

### Métricas para escalas ordinais

-   **MAE** (erro absoluto médio entre nível real e previsto)
-   **Kappa ponderado quadrático (QWK)**
-   **Acurácia ±1** (previu o nível exato ou vizinho)
-   Correlação de Spearman

### Métricas voltadas à segurança

-   **Recall dos níveis Alto e Crítico** (principal)
-   Proporção de casos Alto/Crítico **subestimados em 2 ou mais níveis**
    (pior erro possível)
-   Precision dos níveis Alto/Crítico (para entender o volume de
    alarmes falsos)
-   Erro **assimétrico**: penalizar mais a subestimação que a
    superestimação

Matriz de custos sugerida (ilustrativa):

  Real \\ Previsto   0    1    2    3    4
  --------------- ---- ---- ---- ---- ----
  3 (Alto)          10    6    3    0    1
  4 (Crítico)       20   14    8    3    0
  1 (Baixo)          1    0    1    2    3

### Testes comportamentais

Além das métricas, vale fazer **testes de sensibilidade** com pares de
frases:

``` text
"Ele me ameaçou durante a briga."
"Ele me ameaçou com uma arma durante a briga."
→ a gravidade prevista deve aumentar.
```

``` text
"Ele me bateu há 5 anos, mas hoje estamos separados."
"Ele me bateu hoje de manhã e está aqui."
→ a gravidade prevista deve aumentar muito.
```

Também testar **minimização** e **negação**:

``` text
"Ele nunca me ameaçou com arma."
→ não deve ser tratado como presença de arma.
```

------------------------------------------------------------------------

# 14. Pipeline completo

``` text
   Literatura + instrumentos de risco (ex.: FONAR)
                        │
                        ▼
        Definição da escala e dos fatores de risco
                        │
                        ▼
              Guia de anotação detalhado
                        │
                        ▼
       Coleta/produção de textos (anonimizados)
                        │
                        ▼
   Anotação: gravidade + fatores (2–3 anotadores, QWK)
                        │
                        ▼
        Divisão treino / validação / teste
        (teste 100% humano, sem sintéticos)
                        │
                        ▼
             ┌──────────┴──────────┐
             ▼                     ▼
      TF-IDF + modelo           BERTimbau
        ordinal               (comum / ordinal / multitarefa)
             │                     │
             └──────────┬──────────┘
                        ▼
      Avaliação (MAE, QWK, recall Alto/Crítico)
                        │
                        ▼
      Análise de erros + testes comportamentais
                        │
                        ▼
        Teste com frases novas, curtas e ruidosas
```

------------------------------------------------------------------------

# 15. Exemplo de funcionamento final

Entrada:

``` text
"Faz uns meses que ele começou a me seguir depois que eu pedi
o divórcio. Ontem mandou mensagem dizendo que se eu não voltar
vai acontecer algo com a gente. Ele tem arma em casa."
```

Saída esperada (modelo multitarefa):

``` text
Gravidade prevista: ALTA (P(≥Alta) = 0.82)

Fatores detectados:
  - perseguição                      0.91
  - separação recente                0.95
  - ameaça                           0.88
  - posse de arma                    0.93
  - ameaça de morte explícita        0.35

Orientação: exibir canais 180 e 190
```

Já para:

``` text
"Tivemos uma discussão e ele falou umas coisas que me
magoaram."
```

``` text
Gravidade prevista: BAIXA (P(≥Moderada) = 0.21)
```

------------------------------------------------------------------------

# 16. Relação com os outros dois modelos

O ideal é que os três modelos funcionem de forma complementar:

``` text
                  Texto do usuário
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
   Intenção          Tipo de          Gravidade
(dúvida/relato/    violência         (nível de
  emergência)     (física, psic.,      risco)
                    sexual, ...)
        │               │                │
        └───────────────┼────────────────┘
                        ▼
              Decisão de encaminhamento
```

-   **Intenção** responde "o que a pessoa quer?".
-   **Tipo** responde "que violência está descrita?".
-   **Gravidade** responde "quão perigosa é a situação?".

Os três são independentes mas se relacionam: uma *dúvida* pode ter
gravidade alta (pergunta feita por quem está em risco), e um *relato* de
gravidade baixa pode ser apenas um desabafo. Isso justifica tratá-los
como modelos separados e depois combiná-los em regras de
encaminhamento (por exemplo, **gravidade ≥ Alta** ou **intenção =
Emergência** sempre aciona a exibição dos canais de emergência).

------------------------------------------------------------------------

# 17. Aspectos éticos e legais

-   **Dados sensíveis (LGPD).** Anonimizar tudo, não armazenar dados
    identificáveis.
-   **Comitê de ética.** Verificar com a orientação a necessidade de
    submissão se houver dados reais ou participação de voluntários.
-   **Bem-estar dos anotadores.** O material é pesado; limitar volume e
    oferecer suporte.
-   **Responsabilidade do erro.** Subestimar a gravidade pode levar a
    uma falsa sensação de segurança. O sistema **nunca** deve exibir
    mensagens do tipo "você está segura" com base no modelo.
-   **Não substituir avaliação profissional.** Deixar claro, na
    interface e no trabalho, que se trata de uma triagem automática.
-   **Canais oficiais sempre visíveis**, independentemente do resultado:
    -   **190** (Polícia Militar)
    -   **180** (Central de Atendimento à Mulher)
    -   **192** (SAMU), em caso de lesão
-   **Viés e justiça.** Testar o desempenho por tipo de linguagem
    (formal/coloquial), regionalismos, relações homoafetivas, mulheres
    trans, mulheres com deficiência e diferentes níveis de escolaridade.
-   **Cautela ao divulgar resultados.** Evitar publicar exemplos reais
    ou *prompts* que facilitem burlar o sistema de detecção.

------------------------------------------------------------------------

# 18. Viabilidade geral

O projeto é tecnicamente viável com recursos gratuitos:

``` text
Google Colab
     +
Hugging Face
     +
Python
     +
PyTorch
     +
scikit-learn
     +
Dataset construído pela equipe
```

Os principais desafios, em ordem:

1.  **Definição consistente da escala de gravidade.**
2.  **Obtenção de dados anotados** com qualidade e de forma ética.
3.  **Concordância entre anotadores** (que limita o desempenho
    possível).
4.  **Custo assimétrico dos erros.**
5.  Treinamento em si (o mais simples).

Estratégia mais realista:

1.  Estudar a literatura e o Formulário Nacional de Avaliação de Risco.
2.  Definir a escala (3 ou 5 níveis) e a lista de fatores de risco.
3.  Escrever um guia de anotação com exemplos.
4.  Construir o dataset (casos públicos reescritos, cenários e
    síntese controlada).
5.  Anotar com 2--3 pessoas e medir QWK.
6.  Separar treino, validação e teste (teste somente humano).
7.  Criar baselines (regras e TF-IDF).
8.  Fazer fine-tuning do BERTimbau em três variantes: comum, ordinal e
    multitarefa.
9.  Avaliar com MAE, QWK e recall de Alto/Crítico.
10. Realizar testes de sensibilidade e análise de erros.
11. Testar o modelo com frases novas, curtas e ruidosas.

------------------------------------------------------------------------

# 19. Possíveis perguntas de pesquisa

> **"Como modelos de linguagem pré-treinados podem ser utilizados para
> estimar automaticamente o nível de gravidade de relatos em português
> sobre violência de gênero?"**

> **"A modelagem ordinal e o uso de fatores de risco como tarefa
> auxiliar melhoram a estimativa de gravidade em relação à
> classificação multiclasse tradicional?"**

> **"Qual a concordância entre a classificação de gravidade feita por
> humanos, por LLMs e por modelos ajustados, e como isso limita o
> desempenho de um sistema automático de triagem?"**

------------------------------------------------------------------------

# 20. Conclusão

Sim, é possível desenvolver esse classificador de gravidade
gratuitamente com o Google Colab, a partir do fine-tuning de um modelo
pré-treinado como o BERTimbau.

É, porém, o **problema mais delicado dos três**: a gravidade é
subjetiva, as classes são ordenadas, os erros têm custo assimétrico e os
dados praticamente não existem prontos. O que o torna academicamente
interessante é justamente isso: ele permite explorar **classificação
ordinal, aprendizado multitarefa com fatores de risco, explicabilidade,
concordância entre anotadores e avaliação voltada à segurança**.

O ponto que precisa ser investigado antes de definir o projeto é **se
será possível ter profissionais da área participando da definição da
escala e da anotação**, e **que tipo de dado (sintético, público ou
real anonimizado) estará disponível**. Isso determinará o escopo e a
validade científica dos resultados.
