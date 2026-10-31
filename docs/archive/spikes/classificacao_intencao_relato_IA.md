# Classificação de Intenção do Usuário com IA (Dúvida, Relato ou Emergência)

## 1. Viabilidade do projeto

É viável desenvolver gratuitamente, usando o **Google Colab**, um modelo
de IA capaz de receber um texto e classificar a **intenção** de quem o
digitou em uma de três situações:

-   **Dúvida**: a pessoa quer se informar sobre violência de gênero, seus
    direitos, a legislação, como denunciar, etc.;
-   **Relato**: a pessoa quer contar o que viveu ou vive, desabafar ou
    registrar uma situação;
-   **Emergência**: a pessoa está em perigo agora e está pedindo socorro.

Esse problema é tecnicamente mais simples que a classificação do *tipo*
de violência, porque as classes diferem muito na forma como o texto é
escrito (perguntas, narrativas, pedidos urgentes). Em contrapartida, ele
tem uma característica que o torna mais delicado: **os erros não têm o
mesmo custo**. Classificar uma emergência como dúvida é muito pior do que
o contrário.

Exemplos de funcionamento:

``` text
Entrada:
"Quais são as medidas protetivas previstas na Lei Maria da Penha?"

Saída:
Dúvida
```

``` text
Entrada:
"Meu ex-marido me persegue há meses e eu não sei mais o que fazer."

Saída:
Relato
```

``` text
Entrada:
"Ele está dentro de casa agora, trancou a porta e disse que vai me
matar. Me ajudem."

Saída:
Emergência
```

O principal desafio, novamente, não é o poder computacional, mas
**construir um dataset em português, bem rotulado, com exemplos
suficientes da classe de emergência**, que é naturalmente a mais rara.

------------------------------------------------------------------------

## 2. Definição das classes

Antes de qualquer coleta, é necessário definir com precisão o que
significa cada classe. A fronteira entre elas é o ponto mais difícil do
projeto.

  ----------------------------------------------------------------------------
  Classe           Característica principal      Pistas linguísticas típicas
  ---------------- ----------------------------- -----------------------------
  Dúvida           Busca informação, geralmente  "como", "posso", "qual",
                   formulada como pergunta ou    "o que acontece se", "é
                   cenário hipotético            crime"

  Relato           Narra fatos vividos,          verbos no passado ou
                   normalmente sem pedido        presente habitual ("ele
                   imediato de ajuda             sempre", "há meses")

  Emergência       Perigo presente ou iminente   tempo presente, "agora",
                   e/ou pedido explícito de      "socorro", "vai me matar",
                   socorro                       "ele está aqui"
  ----------------------------------------------------------------------------

### Casos de fronteira

Esses casos precisam estar descritos em um **guia de anotação**:

``` text
"Se meu marido me bater de novo, posso chamar a polícia?"
→ Dúvida (hipotético) ou Relato (há indício de violência anterior)?

"Ontem ele tentou me enforcar. Hoje ele voltou pra casa."
→ Relato ou Emergência?

"Minha vizinha está gritando e sendo agredida agora."
→ Emergência de terceiro. Entra na mesma classe?

"Quero denunciar o que aconteceu comigo, como faço?"
→ Relato + Dúvida ao mesmo tempo.
```

Decisões a tomar e documentar:

1.  **Textos de terceiros** (vizinha, amiga, filha) contam como a mesma
    classe de quem sofre a violência?
2.  Um texto que é relato **e** contém pedido de socorro é emergência?
    (Sugestão: sim, a classe de maior urgência prevalece.)
3.  Um relato com pergunta embutida é relato ou dúvida?
4.  Textos sem relação com violência de gênero entram em uma classe
    "outros / fora do escopo"?

------------------------------------------------------------------------

## 3. Single-label ou multilabel?

Há duas formulações possíveis.

### Opção A --- Single-label com regra de prioridade

``` text
Emergência  >  Relato  >  Dúvida
```

Cada texto recebe uma única classe. Se houver sinais de mais de uma, vale
a de maior prioridade. É a opção mais simples e a mais adequada se o
objetivo é **encaminhar** o usuário (por exemplo, exibir telefones de
emergência).

### Opção B --- Multilabel

``` text
Entrada:
"Ele me bateu ontem e eu quero saber como pedir uma medida protetiva."

Saída:
Dúvida:     0.82
Relato:     0.91
Emergência: 0.12
```

Permite capturar textos mistos, mas torna a anotação mais difícil e a
avaliação mais complexa.

**Recomendação:** começar com single-label e prioridade (Opção A) e, se
houver tempo, tratar a Opção B como extensão.

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
                Classificador
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
          Dúvida     Relato   Emergência
             │         │         │
             └─────────┼─────────┘
                       ▼
                  Resultado
```

Exemplo de saída:

``` text
Dúvida:     0.03
Relato:     0.21
Emergência: 0.76
```

Como o custo dos erros é assimétrico, o limiar **não precisa ser 0.50**
para a classe de emergência:

``` text
P(Emergência) > 0.30  →  tratar como emergência
```

Reduzir o limiar aumenta o recall (menos emergências perdidas) ao custo
de mais falsos alarmes. Esse trade-off deve ser analisado e justificado
no trabalho.

------------------------------------------------------------------------

## 5. Treinar do zero ou fazer fine-tuning?

Assim como no projeto de tipo de violência, **não é necessário treinar um
modelo de linguagem do zero**.

``` text
BERTimbau pré-treinado
        ↓
dataset com 3 intenções
        ↓
GPU do Google Colab
        ↓
modelo especializado
```

Modelos que podem ser avaliados:

-   BERTimbau (base)
-   XLM-R (se houver dados em mais de um idioma)
-   mBERT
-   DistilBERT multilíngue

Para um problema com três classes bem distintas e poucos milhares de
exemplos, o BERTimbau base costuma ser suficiente e cabe na GPU gratuita
do Colab.

------------------------------------------------------------------------

## 6. O Google Colab é suficiente?

Sim. O fine-tuning de um modelo base com textos curtos (até 128--256
tokens) e alguns milhares de exemplos leva minutos na GPU gratuita do
Colab.

Tecnologias:

-   Python
-   Google Colab
-   PyTorch
-   Hugging Face Transformers
-   scikit-learn
-   pandas

Ressalva: as sessões gratuitas do Colab expiram. Convém salvar
*checkpoints* e o dataset no Google Drive.

------------------------------------------------------------------------

## 7. Quanto de dados gratuitos existe?

Pela pesquisa feita (ver `guia_datasets_metodologia_fontes.md`),
**não foi encontrado nenhum dataset, em qualquer idioma, que tenha
exatamente as três classes dúvida / relato / emergência** no domínio de
violência de gênero. Há, porém, fontes parciais para cada classe.

### Fontes por classe

  Classe       Fonte                                    Tipo de uso
  ------------ ---------------------------------------- ---------------------------------------
  **Dúvida**   FAQ da Lei Maria da Penha (Agência Gov,  Perguntas reais de cidadãos escritas por
               25 perguntas); FAQ do CEVID/TJRS;        instituições; **base para escrever
               cartilhas e FAQs de TJPR, TJSC,          perguntas** em linguagem coloquial
               Defensoria do RS, Senado, MPDFT (a abrir
               e conferir)
  **Dúvida**   Guan et al. (2025, *JMIR*): 8            **Taxonomia** de necessidades de
               necessidades de informação de vítimas    informação (jurídico, abrigo, polícia,
               no Reddit (inglês, N pequeno)            plano de segurança…) para subtemas
  **Relato**   Subramani et al. (2018): *abuse*         **Desenho de tarefa** relato × conselho
               (relato) × *advice* (conselho), κ = 0,85 (dataset não divulgado)
  **Relato**   Al-Garadi (2022), Guo (2023), Wang       Detecção de relato (binária) em
               (2026): auto-relato de violência         inglês; referência de método
  **Relato**   EXIST: intenção *direct / reported /     Conceito próximo de "relato", mas de
               judgemental*; MeTooMA: *allegation*      sexismo/MeToo
  **Emergência** *Nenhuma fonte encontrada*             Lacuna
  **Emergência** (análogo) UMD Reddit Suicidality,      Rótulo *Severe* como risco iminente.
               RSD-15K, Boamente (pt)                   Acesso controlado (UMD); Boamente é
                                                        aberto, mas é suicídio
  **Fora do   ToLD-Br, HateBR, Fortuna, OLID-BR,        Textos de outros assuntos e de
  escopo**     TuPyE                                    violência verbal fora do domínio

### Lacunas

-   **Classe Emergência:** não há dados públicos. Pedidos reais de socorro
    vão para canais privados (telefone, aplicativos), e o Crisis Text Line
    não tem dados abertos.
-   **Dados oficiais** (Ligue 180, SSP-RS, SINAN, Anuário) são
    **estatísticas, não texto livre**.
-   Não há dataset de dúvidas de leigos sobre violência doméstica em
    português.

### Consequência

``` text
Dúvida      →  FAQs/cartilhas como semente  + escrita pela equipe
Relato      →  escrita pela equipe + relatos públicos reescritos
Emergência  →  escrita pela equipe, revisada por especialistas
Fora escopo →  corpora de toxicidade/ódio + outros assuntos
```

------------------------------------------------------------------------

## 8. Construir um dataset próprio

A metodologia geral está em `guia_datasets_metodologia_fontes.md`. Aqui
está a aplicação a esta tarefa, cuja particularidade é que **a classe
mais importante é a mais rara e a mais difícil de obter**.

### 8.1 Dimensionamento

Valores hipotéticos de partida, a ajustar com curva de aprendizado:

  Classe                    Exemplos
  ----------------------- ----------
  Dúvida                       1.000
  Relato                       1.000
  Emergência                     600
  Fora do escopo                 600
  **Total**                **3.200**

Para a classe **Emergência**, é mais importante garantir **diversidade**
(situações, registros, tamanhos, ruído) do que apenas volume, e reservar
uma parte própria para o teste.

### 8.2 Trilhas de obtenção por classe

  Classe          Trilha                                               Observação
  --------------- ---------------------------------------------------- --------------------------------
  Dúvida          FAQs reescritas em linguagem coloquial; perguntas    Variar entre perguntas diretas,
                  escritas por voluntários a partir de cartões de      hipotéticas e implícitas ("e
                  tema (medida protetiva, denúncia, pensão, guarda)    se ele me bater de novo?")
  Relato          Voluntários escrevem a partir de cenários; relatos   Variar tempo verbal (passado
                  públicos reescritos (com consulta ao CEP)            vs. habitual) e grau de emoção
  Emergência      **Elicitação com cartões de cenário** (ver 8.3),     Revisão por profissional;
                  escrita por voluntários e depois revisada            textos escritos, e não reais,
                                                                       reduzem o dano aos anotadores
  Fora do escopo  Outros assuntos do cotidiano + violência verbal      Incluir **negativos difíceis**
                  fora do domínio                                      (seção 8.4)

### 8.3 Elicitação de textos de emergência

Em vez de depender de dados reais, usar **cartões de cenário** com
atributos combinados, para que voluntários escrevam mensagens realistas:

``` text
Cartão de cenário (exemplo):
  tempo:        presente imediato
  agressor:     presente no local
  ameaça:       de morte
  arma:         sim
  vítima:       escondida, com filho
  possibilidade de falar: não
  registro:     informal, pouca pontuação, erros de digitação
  tamanho:      uma frase curta
```

-   Pedir **mensagens como realmente seriam digitadas** (curtas,
    fragmentadas, sem acento).
-   Variar os atributos de modo sistemático (combinações) para cobrir
    situações diferentes, inclusive **pedidos de socorro indiretos** ("se
    eu não responder, chama a polícia").
-   Quem escreve os textos de teste **não escreve os de treino** (evita
    que o modelo aprenda o estilo do autor).
-   Revisão por pessoa com experiência em atendimento.

### 8.4 Negativos difíceis (essenciais nesta tarefa)

Sem negativos difíceis, o modelo aprende "palavra forte = emergência".

``` text
Falso-emergência (figurado):  "esse trabalho está me matando"
                              "socorro, esqueci a senha do wifi"
                              "vou matar ele de tanto rir"
Dúvida com palavras fortes:   "quanto tempo dura uma medida protetiva?"
Relato antigo:                "há 10 anos ele me ameaçava de morte"
Terceiros:                    "vi no jornal que um homem matou a esposa"
```

### 8.5 Esquema de anotação e regras de decisão

``` text
id | texto | contexto_anterior | origem | intencao | terceira_pessoa |
tempo (presente/passado/hipotético) | pedido_explicito_de_ajuda |
anotador_id | rodada | versao_guia
```

-   Definir **emergência de forma prescritiva**: perigo presente ou
    iminente **e/ou** pedido explícito de socorro, com critérios
    escritos.
-   Registrar atributos auxiliares (`tempo`, `pedido_explicito_de_ajuda`,
    `terceira_pessoa`): ajudam a resolver divergências e a analisar
    erros.
-   Regra de precedência: **Emergência > Relato > Dúvida** quando
    houver sinais mistos.
-   Decidir e documentar a **terceira pessoa** (a vizinha está sendo
    agredida agora = emergência ou classe própria?).
-   Incluir `contexto_anterior` (última pergunta do bot e mensagens
    anteriores): o chatbot classificará mensagens dentro de um diálogo
    (ver seção 3.2 da arquitetura). Incluir exemplos como "sim", "agora",
    "ele está aqui".

### 8.6 Ciclo de construção e qualidade

-   Ciclo MATTER com 3 rodadas e guia versionado.
-   **κ por classe**, e **F1 de concordância na classe Emergência**: o κ
    global esconde a classe rara.
-   **Dupla anotação de toda a classe Emergência** e de uma amostra das
    demais.
-   **Active learning** para encontrar candidatos a emergência em textos
    ambíguos.
-   Metas de concordância são convenções da literatura (por exemplo,
    ≥ 0,67 tentativo, ≥ 0,80 desejável), não garantias.

### 8.7 Divisão, teste ouro e desafio

-   Desduplicar antes de dividir; dividir por autor e fonte.
-   **Teste ouro 100% humano**, estratificado, com emergências de autores
    diferentes dos do treino, congelado antes dos experimentos.
-   **Conjunto de desafio:** os negativos difíceis (8.4), textos
    ruidosos, mensagens de uma palavra, falta de acentuação e
    pontuação, e contrast sets ("ele vai me matar" × "ele vai matar o
    jogo").
-   Reportar o recall da emergência com **intervalo de confiança**:
    com poucas emergências no teste, a incerteza é grande.

### 8.8 Documentação e ética

-   Datasheet com origem das trilhas, proporção de texto sintético,
    perfil dos anotadores.
-   Mensagens de emergência escritas para o projeto **não devem ser
    publicadas** de modo que ajudem a burlar o sistema.
-   Anotadores: exposição limitada, aviso de conteúdo, apoio.
-   Dados reais: CEP/orientação antes de coletar.

------------------------------------------------------------------------

## 9. Data augmentation e dados sintéticos

Com tão poucos dados reais da classe Emergência, é tentador gerar
exemplos com um LLM. Pode ser útil, mas com regras (guia, seção 3.7):

-   Gerar a partir dos **cartões de cenário (8.3)**, para que a
    diversidade seja controlada por atributos, e não por acaso.
-   Textos de LLM tendem a ser **mais limpos, completos e didáticos**
    que mensagens reais de pessoas em perigo, que são curtas,
    fragmentadas e emocionais. O modelo pode aprender o **estilo do
    LLM** em vez do conceito.
-   Injetar ruído realista: erros de digitação, ausência de acentos,
    gírias e abreviações ("vc", "tbm", "n sei"), mensagens de uma
    palavra.
-   Marcar `origem = sintetico`; **usar só no treino**.
-   **Teste ouro sem nenhum exemplo sintético.**
-   **Ablação:** comparar treino com e sem sintético em teste humano,
    olhando especificamente o recall da emergência.

Outras técnicas: paráfrase, retrotradução (PT→EN→PT), e variação de
pessoa e tempo verbal (a diferença entre "ele me bateu" e "ele está me
batendo" é central nesta tarefa).

------------------------------------------------------------------------

## 10. LLM como anotador e pseudo-rótulos

Usar um LLM para classificar textos e tratar o resultado como verdade
introduz ruído e viés. Aqui o risco é maior, porque um erro de rótulo na
classe Emergência ensina o modelo a errar justamente onde o custo é
mais alto. Os estudos que mostram bom desempenho de LLMs como
anotadores tratam de outras tarefas; não há evidência verificada para
este domínio (guia, seção 3.6).

Protocolo:

1.  LLM só para **pré-anotar e priorizar** (*weak labels*).
2.  Congelar o prompt antes de medir.
3.  Medir κ e F1 **por classe** contra o ouro humano, **reportando a
    classe Emergência separadamente**.
4.  **Nunca** usar pseudo-rótulos no teste ouro.
5.  Usar regras e palavras-chave só para **recuperar candidatos** de
    anotação.

A concordância entre LLM e humanos pode ser um resultado do trabalho, e
a medida mais relevante é **quantas emergências reais o LLM classificou
como dúvida ou relato**.

------------------------------------------------------------------------

# 11. Comparação entre modelos

### Modelo 0 --- Baseline por regras

``` text
Lista de palavras-chave
("socorro", "agora", "vai me matar", "?", "como", "posso")
   ↓
classe
```

Serve como referência mínima e, no caso da emergência, pode inclusive ser
mantido no sistema final como **camada de segurança** (ver seção 14).

### Modelo 1 --- Baseline tradicional

``` text
TF-IDF
   ↓
Regressão Logística / SVM
   ↓
classe
```

### Modelo 2 --- Transformer

``` text
BERTimbau
   ↓
fine-tuning
   ↓
classe
```

### Modelo 3 --- Transformer + dados aumentados/sintéticos

``` text
BERTimbau + dados aumentados
   ↓
fine-tuning
   ↓
classe
```

### Modelo 4 (opcional) --- Multilíngue

``` text
XLM-R + dados em PT/EN/ES
   ↓
fine-tuning
   ↓
classe
```

------------------------------------------------------------------------

# 12. Aspectos éticos e legais

Este é um dos pontos que mais pesa neste projeto e deve constar do
trabalho.

-   **Dados pessoais e sensíveis (LGPD).** Relatos de violência são dados
    sensíveis. Não coletar nem armazenar dados identificáveis (nomes,
    endereços, telefones). Anonimizar tudo.
-   **Comitê de ética.** Se houver uso de textos de pessoas reais ou
    participação de voluntários, verificar com a orientação se é
    necessária submissão ao comitê de ética em pesquisa.
-   **Bem-estar dos anotadores.** Ler centenas de relatos de violência
    pode ser emocionalmente pesado. Limitar volume por sessão e oferecer
    suporte.
-   **Não substituir atendimento humano.** O modelo é uma ferramenta de
    apoio e triagem, nunca um serviço de emergência. A interface deve
    sempre exibir os canais oficiais, independentemente da classe
    prevista:
    -   **190** (Polícia Militar)
    -   **180** (Central de Atendimento à Mulher)
    -   **192** (SAMU), quando houver lesão física
-   **Evitar falsa sensação de segurança.** O sistema não deve passar a
    mensagem de que "não foi detectada emergência" como se isso
    garantisse que a pessoa está segura.
-   **Viés.** O modelo pode funcionar pior para certos grupos
    (linguagem coloquial, regionalismos, mulheres com baixa
    escolaridade, mulheres trans, relações homoafetivas, pessoas com
    deficiência). Isso deve ser testado, não presumido.

------------------------------------------------------------------------

# 13. Métricas de avaliação

Métricas gerais:

-   Accuracy (informativa, mas insuficiente)
-   Precision, Recall e F1 **por classe**
-   F1 macro
-   Matriz de confusão

Métricas que importam mais neste problema:

-   **Recall da classe Emergência** (principal): quantas emergências
    reais o modelo deixou passar?
-   Precision da classe Emergência: quantos alarmes falsos?
-   Curva Precision-Recall para a classe Emergência (mais informativa
    que ROC em classes raras)
-   Quantidade de **Emergências classificadas como Dúvida** (pior erro
    possível)

Matriz de custos sugerida (apenas ilustrativa, a ser discutida):

  Real \\ Previsto      Dúvida   Relato   Emergência
  ------------------- -------- -------- ------------
  Dúvida                     0        1            2
  Relato                     2        0            2
  Emergência                20        8            0

A avaliação pode incluir o **custo médio esperado** com base em uma
matriz desse tipo.

------------------------------------------------------------------------

# 14. Pipeline completo

``` text
         FAQs / depoimentos / textos escritos
                        │
                        ▼
            Anonimização + limpeza
                        │
                        ▼
          Anotação (2+ anotadores, Kappa)
                        │
                        ▼
        Divisão treino / validação / teste
        (teste 100% humano, sem sintéticos)
                        │
                        ▼
             ┌──────────┴──────────┐
             ▼                     ▼
      TF-IDF + LogReg          BERTimbau
             │                     │
             └──────────┬──────────┘
                        ▼
        Avaliação (foco em recall de emergência)
                        │
                        ▼
              Análise de erros
                        │
                        ▼
        Teste com frases novas e ruidosas
```

### Sugestão de arquitetura híbrida para uso real

``` text
Texto
  │
  ├──► Regras de segurança ("socorro", "vai me matar", ...)
  │            │ se disparar → Emergência (sobrepõe o modelo)
  │            ▼
  └──► Modelo BERTimbau ──► classe + probabilidade
                                   │
                                   ▼
                  Interface sempre mostra 180 / 190
```

------------------------------------------------------------------------

# 15. Exemplo de funcionamento final

``` text
"Ele quebrou a porta do quarto, estou escondida no banheiro
com meu filho, por favor mandem alguém"
```

Saída esperada:

``` text
Emergência: 0.96
Relato:     0.04
Dúvida:     0.00
```

Já para:

``` text
"Minha mãe sofreu violência do meu pai por anos. Hoje ela
tem direito a alguma coisa? Ela pode pedir pensão?"
```

``` text
Dúvida:     0.88
Relato:     0.30
Emergência: 0.02
```

------------------------------------------------------------------------

# 16. Viabilidade geral

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
Dataset próprio e/ou público
```

Os maiores desafios, em ordem:

1.  **Dados da classe Emergência** (raros, sensíveis, difíceis de obter).
2.  **Definição e consistência das fronteiras entre classes.**
3.  **Questões éticas.**
4.  Treinamento em si (o mais simples).

Estratégia mais realista:

1.  Definir claramente as classes e escrever o guia de anotação.
2.  Levantar o que existe de dados públicos em português.
3.  Construir o dataset (público + escrito pela equipe).
4.  Anotar com pelo menos dois anotadores e medir concordância.
5.  Separar treino, validação e teste (teste somente humano).
6.  Criar baseline por regras e baseline TF-IDF.
7.  Fazer fine-tuning de BERTimbau.
8.  Ajustar o limiar da classe Emergência.
9.  Avaliar com foco em recall de emergência e análise de erros.
10. Testar com frases ruidosas, curtas e com erros de digitação.

------------------------------------------------------------------------

# 17. Possíveis perguntas de pesquisa

> **"Como modelos de linguagem pré-treinados podem ser utilizados para
> identificar automaticamente se um texto em português sobre violência de
> gênero corresponde a uma dúvida, um relato ou um pedido de socorro?"**

> **"Qual o impacto do ajuste do limiar de decisão e da ponderação de
> custos no recall da detecção de pedidos de emergência em textos sobre
> violência de gênero?"**

> **"Dados sintéticos gerados por LLM são suficientes para treinar um
> classificador de emergência que generalize para textos escritos por
> humanos?"**

------------------------------------------------------------------------

# 18. Conclusão

Sim, é possível desenvolver esse classificador gratuitamente usando o
Google Colab, com fine-tuning de um modelo pré-treinado como o
BERTimbau.

Comparado à classificação do tipo de violência, este problema tem
**menos ambiguidade conceitual entre as classes**, mas traz duas
dificuldades próprias: a **escassez de dados da classe de emergência** e
a **assimetria do custo dos erros**, que obriga a priorizar o recall e a
tratar o sistema como apoio à triagem, não como substituto do
atendimento humano.

O ponto que precisa ser investigado antes de definir o projeto é
**onde obter exemplos realistas e éticos da classe Emergência** e quem
poderá revisar essas anotações. Isso determinará se o projeto pode
depender de dados públicos ou se terá de se apoiar em dados escritos e
validados pela própria equipe.
