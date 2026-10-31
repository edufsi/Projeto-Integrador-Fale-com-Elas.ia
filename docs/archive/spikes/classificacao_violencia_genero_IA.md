# Classificação de Violência de Gênero com IA

## 1. Viabilidade do projeto

É totalmente viável desenvolver gratuitamente, usando o **Google
Colab**, um modelo de IA capaz de receber algumas frases em texto e
classificar o tipo de violência de gênero descrito.

O principal desafio não é o poder computacional, mas encontrar ou
construir um **dataset suficientemente grande, bem rotulado e
consistente em português**.

Um exemplo de funcionamento:

``` text
Entrada:
"Ele controla todo o meu dinheiro e não deixa eu trabalhar."

Saída:
Violência patrimonial/econômica
```

Outro exemplo:

``` text
Entrada:
"Ele me ameaça dizendo que vai me matar se eu terminar o relacionamento."

Saída:
Violência psicológica
```

Também é possível utilizar classificação multilabel, permitindo que uma
mesma situação pertença a mais de uma categoria.

------------------------------------------------------------------------

## 2. Possível arquitetura

Uma arquitetura simples poderia ser:

``` text
                 Texto de entrada
                       │
                       ▼
             Pré-processamento
                       │
                       ▼
             Modelo pré-treinado
            (BERTimbau / mBERT)
                       │
                       ▼
                Classificador
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
         Física   Psicológica  Sexual
             │         │         │
             └─────────┼─────────┘
                       ▼
                  Resultado
```

Por exemplo:

``` text
Entrada:
"Ele sempre diz que eu sou inútil e que ninguém vai
querer ficar comigo."

Saída:

Violência psicológica: 0.94
Violência moral:       0.38
Violência física:      0.02
Violência sexual:      0.01
Violência patrimonial: 0.04
```

Nesse caso, poderia ser definido um limiar, por exemplo:

``` text
probabilidade > 0.50 → categoria presente
```

Isso caracteriza uma tarefa de **classificação multilabel**.

------------------------------------------------------------------------

## 3. Treinar do zero ou fazer fine-tuning?

Não seria necessário treinar um modelo de linguagem do zero.

### Treinar do zero

``` text
bilhões de parâmetros
        ↓
muitos GB/TB de dados
        ↓
GPU muito potente
        ↓
alto custo computacional
```

### Fine-tuning

``` text
BERTimbau pré-treinado
        ↓
dataset sobre violência
        ↓
GPU do Google Colab
        ↓
modelo especializado
```

A segunda abordagem é muito mais realista para um projeto acadêmico.

Modelos que poderiam ser avaliados:

-   BERTimbau
-   mBERT
-   DistilBERT
-   modelos multilíngues
-   modelos como XLM-R

------------------------------------------------------------------------

## 4. O Google Colab é suficiente?

Para esse tipo de projeto, **o Google Colab gratuito pode ser
suficiente**, principalmente se forem utilizados modelos pré-treinados e
for feito apenas fine-tuning.

Tecnologias que podem ser utilizadas:

-   Python
-   Google Colab
-   PyTorch
-   Hugging Face Transformers
-   scikit-learn
-   pandas
-   NumPy

Não seria necessário possuir uma GPU local.

------------------------------------------------------------------------

## 5. Quanto de dados gratuitos existe?

Existe uma quantidade razoável de dados públicos *vizinhos* ao problema,
mas, pela pesquisa feita (ver `guia_datasets_metodologia_fontes.md`),
**não foi encontrado nenhum corpus público em português rotulado pelos
tipos de violência da Lei Maria da Penha**. Isso precisa ser reconfirmado
na revisão bibliográfica, mas o planejamento mais seguro é assumir que
**os rótulos terão de ser construídos pela equipe**.

### O que existe e qual papel pode ter

  Fonte                          Idioma   Rótulos relevantes                Papel no projeto
  ------------------------------ -------- --------------------------------- ----------------------------------
  **WomenHelp** (IberLEF 2026)   es       Tipos de violência, multilabel    **Principal análogo.** Transfer
                                          (7 rótulos, 4.845 exemplos de     multilíngue e referência de
                                          treino); acesso **não             esquema. Conferir a taxonomia
                                          confirmado**                      antes de mapear
  **EXIST** (2021--2025)         en/es    Sexismo; categorias incl.         Transferência; contexto de
                                          violência sexual                  sexismo, não de relato
  **EDOS** (SemEval-2023)        en       Ameaças, derrogação, etc.         Transferência fraca (CC0)
  Ha et al. (2022)               en       Violência geral, física,          **Ideia metodológica:** treinar com
  *DetectIPV*                             emocional, sexual                 itens de questionários
  ToLD-Br, HateBR, Fortuna,      pt       Misoginia/sexismo/ódio            **Negativos difíceis** e
  OLID-BR, TuPyE                                                            transferência; não são tipos da Lei
  LexMis-BR (léxico)             pt       Termos de misoginia e violência   Filtro e funções de rotulagem
  FAQs, cartilhas e definições   pt       Texto institucional               Base do **guia de anotação** e de
  do TJDFT                                                                  exemplos por tipo
  Jurisprudência (CEIA-          pt       Sem rótulos                       Frases jurídicas; linguagem formal
  COREJUR/processos)
  Painel do Ligue 180, SSP-RS    pt       Estatísticas por tipo             **Calibrar proporções** entre tipos
  BOs da PCDF (Lima & Oliveira)  pt       Risco, 162 BOs                    Restrito; só referência

### Lacunas confirmadas

-   Nenhum corpus PT-BR rotulado como física/psicológica/sexual/
    patrimonial/moral.
-   Relatos em primeira pessoa existem (campanhas, redes sociais), mas
    em geral como **análises qualitativas**, não como corpus
    distribuído.
-   Os dados mais ricos (boletins de ocorrência, prontuários) são
    **restritos**.

### Consequência para o projeto

``` text
Dados públicos  →  negativos, transferência, léxicos, definições
Dados próprios  →  rótulos de tipo (treino, validação, TESTE OURO)
```

------------------------------------------------------------------------

## 6. Categorias de violência

Antes de coletar os dados, é importante definir uma taxonomia.

No contexto brasileiro, a Lei Maria da Penha trabalha com categorias
como:

-   violência física
-   violência psicológica
-   violência sexual
-   violência patrimonial
-   violência moral

Porém, datasets internacionais podem utilizar categorias diferentes, por
exemplo:

``` text
physical
sexual
emotional
economic
verbal
stalking
coercive_control
```

Não é recomendável simplesmente misturar todos esses datasets.

É necessário definir uma **taxonomia comum** e estabelecer como as
categorias de cada dataset serão mapeadas para ela.

------------------------------------------------------------------------

## 7. Uma estratégia possível para aumentar os dados

Uma alternativa é combinar dados em português com dados em espanhol e
inglês e utilizar um modelo multilíngue.

``` text
Português ───────┐
                 │
Espanhol ────────┼──► XLM-R / mBERT ──► classificação
(WomenHelp)      │
Inglês ──────────┘
(EXIST, EDOS)
```

O candidato mais interessante é o **WomenHelp**, único corpus encontrado
com relatos de vítimas e **tipos de violência em multilabel**, embora em
espanhol e com acesso ainda a confirmar. O EXIST e o EDOS trazem
sexismo e ameaças, que são tarefas relacionadas, mas diferentes.

### Cuidados

-   **Taxonomias diferentes.** Os 7 rótulos do WomenHelp não são
    necessariamente os 5 da Lei Maria da Penha. É preciso construir um
    **mapeamento explícito** (muitos-para-um, ou "sem equivalente") e
    documentá-lo.
-   **Domínio diferente.** Relatos de um centro de atendimento no norte
    do México não são iguais a mensagens de chatbot no Brasil.
-   **Uso ético.** São textos de vítimas; respeitar os termos de acesso
    e não redistribuir.

### Desenho experimental sugerido

  Experimento                          Treino            Teste
  ------------------------------------ ----------------- ----------------------
  E1 --- só português                  PT próprio        Teste ouro PT
  E2 --- zero-shot translingual        ES (WomenHelp)    Teste ouro PT
  E3 --- multilíngue                   PT + ES (+ EN)    Teste ouro PT
  E4 --- multilíngue + ajuste fino     ES → depois PT    Teste ouro PT

A comparação responde à pergunta de pesquisa da seção 16. O **teste
ouro em português deve ser exclusivamente humano** (ver seção 8.6).

------------------------------------------------------------------------

## 8. Construir um dataset próprio

Como não há corpus pronto, a construção do dataset é a parte central do
projeto. A metodologia geral (ciclo MATTER, concordância, desacordo,
documentação, ética) está em `guia_datasets_metodologia_fontes.md`; aqui
está a aplicação a esta tarefa.

### 8.1 Dimensionamento

Valores hipotéticos de partida, a ajustar com uma **curva de
aprendizado** (treinar com 25%, 50%, 75% e 100% e observar quando o F1
por rótulo estabiliza):

  Categoria          Exemplos
  --------------- -----------
  Física                  800
  Psicológica           1.000
  Sexual                  700
  Patrimonial             500
  Moral                   500
  Sem violência         1.000
  **Total**         **4.500**

(Em multilabel, um exemplo pode contar em mais de uma linha.) As
**proporções naturais** entre os tipos podem ser consultadas no painel do
Ligue 180, mas os tipos raros devem ser **sobreamostrados** para ter
exemplos suficientes de treino e de teste.

### 8.2 De onde vêm os textos (trilhas de obtenção)

  Trilha                              Como                                       Cuidados
  ----------------------------------- ------------------------------------------ -------------------------------
  **T1 --- Escrita por colaboradores** Voluntários escrevem relatos curtos a      Principal fonte do teste.
                                      partir de cenários (cartões com tipo,      Usar pessoas diferentes das do
                                      relação, tempo, nível de detalhe) e         treino
                                      registro informal
  **T2 --- Itens de questionários**   Transformar itens de escalas de violência   Ideia do DetectIPV. Verificar
                                      (por exemplo, a adaptação brasileira do     direitos de uso dos
                                      CTS2) em frases em 1ª pessoa                instrumentos
  **T3 --- Relatos públicos            Reescrever/parafrasear relatos de          Exige consulta ao CEP/
  reescritos**                        campanhas e reportagens, removendo          orientação; remover
                                      identificadores                            identificadores
  **T4 --- Definições e cartilhas**   Exemplos extraídos de TJDFT, cartilhas e    Respeitar licenças; reescrever
                                      FAQs, adaptados para 1ª pessoa
  **T5 --- Sintético com LLM**        Geração controlada por atributos (seção 9)  **Somente treino**
  **T6 --- Negativos difíceis**       Textos de outras fontes (ToLD-Br, HateBR,    Mantêm o modelo longe do
                                      notícias, ficção) com palavras de           atalho "palavra forte =
                                      violência fora de contexto de gênero        violência"

Meta de composição (heurística, a ajustar): o **teste ouro** vem só de
T1 e T3 (humano); o **treino** pode combinar T1--T6.

### 8.3 Esquema de anotação

``` text
id | texto | origem | fonte_id | fisica | psicologica | sexual |
patrimonial | moral | sem_violencia | fora_do_escopo |
terceira_pessoa | anotador_id | rodada | versao_guia
```

-   `origem`: `escrito_colaborador`, `publico_reescrito`,
    `questionario`, `cartilha`, `sintetico`, `negativo_dificil`.
-   Rótulos por tipo são **binários e independentes** (multilabel).
-   `sem_violencia` e `fora_do_escopo` são exclusivos dos demais.
-   `terceira_pessoa`: relato sobre outra pessoa (filha, vizinha).
-   Guardar **cada anotador separadamente**, sem apagar após a
    adjudicação.

### 8.4 Guia de anotação: decisões específicas desta tarefa

Base legal: **art. 7º da Lei 11.340/2006** (formas de violência
doméstica e familiar). Exemplos de regras a escrever e documentar:

  Situação                                      Decisão sugerida (a validar no piloto)
  --------------------------------------------- ---------------------------------------------
  Humilhação, ameaça, controle, isolamento,     Psicológica
  vigilância do celular
  Xingamento, calúnia, difamação, injúria       Moral (distinguir de psicológica pelo caráter
                                                de ataque à honra/reputação)
  Reter, destruir ou controlar dinheiro,        Patrimonial
  documentos ou instrumentos de trabalho
  Relação sexual forçada, impedir uso de        Sexual
  contracepção
  Tapa, empurrão, lesão                         Física
  Ameaça com arma de agressão física futura     Psicológica (e física, se houver agressão
                                                no relato)
  Uma frase com mais de um tipo                 Marcar **todos** os tipos com evidência no
                                                texto
  Texto ambíguo ("ele é difícil")               Sem violência, ou "ambíguo", conforme
                                                decisão do guia

Princípio: **marcar apenas o que há evidência no texto**, sem inferir
além dele. Cada discordância do piloto vira regra ou exemplo no guia.

### 8.5 Ciclo de construção e controle de qualidade

``` text
Rodada 1: 100 itens, 2-3 anotadores, discutir tudo  → guia v2
Rodada 2: 200 itens, medir α por rótulo, treinar baseline → guia v3
Rodada 3: lote maior, dupla anotação em 20-30% dos itens
Produção:  anotar o restante, com amostras de checagem
```

-   Metas de concordância (convenções da literatura, não garantias):
    α por rótulo ≥ 0,67 como mínimo tentativo e ≥ 0,80 como desejável.
    Rótulos com concordância baixa indicam **definição ruim**, não
    "anotador ruim".
-   Reportar **α ou κ por rótulo, com intervalo de confiança**.
-   Rótulos raros (por exemplo, patrimonial, moral) tendem a ter κ
    instável; garantir ao menos 30--50 positivos na amostra de dupla
    anotação.
-   **Active learning:** depois da rodada 2, priorizar para anotação os
    exemplos em que o baseline está mais incerto.

### 8.6 Divisão e teste ouro

-   Desduplicar (inclusive quase-duplicatas) **antes** de dividir.
-   Dividir por **fonte e por anotador/autor**.
-   O **teste ouro** é 100% humano, com dupla anotação adjudicada e
    **congelado antes dos experimentos**.
-   Criar um **conjunto de desafio** (contrast sets, negação,
    terceira pessoa, minimização). Exemplo: "ele ameaçou o time
    adversário" × "ele me ameaçou".

### 8.7 Documentação e ética

-   Preencher um **datasheet** (Gebru et al.) com origem de cada trilha,
    proporção de texto sintético, perfil dos anotadores e concordância.
-   Anotadores: tempo de exposição limitado, aviso de conteúdo, opção de
    pular, apoio psicológico.
-   Dados reais: consulta ao CEP/orientação **antes** de coletar.
-   Divulgação: sob pedido e com termo de uso.

------------------------------------------------------------------------

## 9. Data augmentation e dados sintéticos

Dados sintéticos podem ajudar nos rótulos raros, mas com regras (ver
seção 3.7 do guia).

-   **Gerar com atributos cruzados**, e não apenas pedir "um relato de
    violência patrimonial": variar relação com o agressor, região,
    registro (formal/informal), tamanho, nível de detalhe, presença de
    erros de digitação e abreviações ("vc", "tbm", "n").
-   Evitar o **estilo de LLM** (textos longos, organizados,
    explicativos): misturar com instruções de fragmentação e ruído.
-   Marcar `origem = sintetico` e **usar só no treino**.
-   **Revisar manualmente uma amostra** (por exemplo, 10%) e descartar
    exemplos com rótulo discutível.
-   **Ablação obrigatória:** treinar com e sem sintético e comparar no
    teste ouro humano. Se não melhorar, não usar.
-   Outras técnicas: paráfrase, retrotradução (PT→EN→PT), troca de
    pessoa gramatical e de tempo verbal.
-   Cuidado com o risco de **colapso de diversidade** ao gerar dados em
    sequência a partir de dados já gerados.

Exemplos artificiais **não são verdade absoluta**: a qualidade da
anotação humana deve ser preservada.

------------------------------------------------------------------------

## 10. LLM como anotador e pseudo-rótulos

Pegar textos da internet e pedir a um LLM que os classifique, usando o
resultado como verdade, introduz **ruído e viés de anotação**. A
literatura mostra que LLMs podem igualar ou superar anotadores em
algumas tarefas, mas também que **a anotação automática exige validação
humana**, e esses estudos não são sobre este domínio (ver seção 3.6 do
guia).

Protocolo recomendado:

1.  Usar o LLM para **pré-anotar e priorizar**, tratando a saída como
    *weak labels* / pseudo-rótulos.
2.  **Congelar o prompt antes de medir** o desempenho.
3.  Medir κ e F1 **por tipo** contra o ouro humano, em amostra
    estratificada (principalmente nos tipos raros).
4.  Se o LLM concordar bem em um tipo, usar pré-anotação nele para
    acelerar; onde concordar mal, anotar manualmente.
5.  Usar **funções de rotulagem** (léxico LexMis-BR, regex) apenas para
    recuperar candidatos, **não para rotular o teste**.
6.  Nunca incluir pseudo-rótulos no teste ouro.

A concordância entre LLM e humanos pode virar um resultado do trabalho.

------------------------------------------------------------------------

# 11. Comparação entre modelos

Para um projeto acadêmico de NLP, seria interessante não utilizar apenas
um modelo.

Uma comparação possível seria:

### Modelo 1 --- Baseline tradicional

``` text
TF-IDF
   ↓
SVM
   ↓
categoria
```

### Modelo 2 --- Transformer

``` text
BERTimbau
   ↓
fine-tuning
   ↓
categoria
```

### Modelo 3 --- Transformer + dados aumentados

``` text
BERTimbau + dados aumentados
   ↓
fine-tuning
   ↓
categoria
```

Isso permitiria comparar métodos tradicionais de NLP com modelos de
linguagem pré-treinados.

------------------------------------------------------------------------

# 12. Métricas de avaliação

Para classificação, algumas métricas importantes seriam:

-   Accuracy
-   Precision
-   Recall
-   F1-score
-   F1 macro
-   matriz de confusão

Para classificação multilabel, também podem ser utilizadas:

-   Micro-F1
-   Macro-F1
-   Hamming Loss
-   Subset Accuracy

A escolha das métricas deve considerar o possível desbalanceamento entre
as categorias.

------------------------------------------------------------------------

# 13. Pipeline completo

Um pipeline possível seria:

``` text
                 DATASETS PÚBLICOS
                        │
                        ▼
              Limpeza + padronização
                        │
                        ▼
               Dataset em português
                        │
                        ▼
             ┌──────────┴──────────┐
             ▼                     ▼
         TF-IDF + SVM          BERTimbau
             │                     │
             └──────────┬──────────┘
                        ▼
                    Avaliação
                        │
                        ▼
            Classificação de novas
                    frases
```

------------------------------------------------------------------------

# 14. Exemplo de funcionamento final

O sistema poderia receber:

``` text
"Meu namorado pega meu celular, verifica todas as
minhas mensagens e diz que eu não posso sair com
minhas amigas."
```

E retornar algo semelhante a:

``` text
Violência psicológica: 0.91
Violência moral:       0.55
Violência patrimonial: 0.03
Violência física:      0.02
Violência sexual:      0.01
```

Dependendo da taxonomia escolhida, a classificação poderia ser
multilabel.

------------------------------------------------------------------------

# 15. Viabilidade geral

O projeto é tecnicamente viável utilizando recursos gratuitos:

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
Datasets públicos
```

O maior desafio será a **qualidade e quantidade dos dados**, e não o
treinamento em si.

A estratégia mais realista seria:

1.  Definir claramente as categorias.
2.  Procurar datasets públicos já anotados.
3.  Verificar quais estão disponíveis em português.
4.  Avaliar datasets internacionais.
5.  Definir uma taxonomia comum.
6.  Limpar e padronizar os textos.
7.  Separar treino, validação e teste.
8.  Criar um baseline com TF-IDF + SVM.
9.  Fazer fine-tuning de BERTimbau ou outro Transformer.
10. Comparar os resultados.
11. Avaliar especialmente os erros entre categorias.
12. Testar o modelo com frases novas.

------------------------------------------------------------------------

# 16. Uma possível pergunta de pesquisa

Uma formulação possível seria:

> **"Como modelos de linguagem pré-treinados podem ser utilizados para
> classificar automaticamente diferentes tipos de violência de gênero em
> textos em língua portuguesa?"**

Outra possibilidade, caso sejam utilizados dados multilíngues:

> **"Qual é o impacto da utilização de dados multilíngues no desempenho
> de modelos Transformer para classificação de violência de gênero em
> textos em português?"**

------------------------------------------------------------------------

# 17. Conclusão

Sim, é possível desenvolver esse sistema gratuitamente usando Google
Colab.

O caminho mais indicado não seria treinar uma IA do zero, mas utilizar
um modelo de linguagem pré-treinado e fazer **fine-tuning para
classificação de violência de gênero**.

O projeto pode ser suficientemente complexo para um trabalho acadêmico
porque envolve:

-   coleta e análise de datasets;
-   definição de taxonomia;
-   pré-processamento de linguagem natural;
-   classificação supervisionada;
-   modelos tradicionais;
-   Transformers;
-   classificação multilabel;
-   avaliação estatística;
-   análise de erros;
-   possíveis questões de transferência multilíngue.

A pesquisa de fontes (ver `guia_datasets_metodologia_fontes.md`) não
encontrou um corpus público em português rotulado pelos tipos da Lei
Maria da Penha. Portanto, o dataset de rótulos terá de ser **construído
pela equipe**, com dados públicos servindo de negativos, transferência
e definições. O ponto a confirmar antes de definir definitivamente o
projeto é **o acesso a corpora de apoio** (por exemplo, WomenHelp e
EXIST) e **quem poderá anotar e revisar os dados**, pois a qualidade
da anotação limita o desempenho do modelo.
