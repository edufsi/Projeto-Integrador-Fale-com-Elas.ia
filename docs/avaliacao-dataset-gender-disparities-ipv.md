# Avaliação do dataset *Gender Disparities in LLM-Based Intimate Partner Violence Detection*

Fonte: [repositório público](https://github.com/TabiaTanzin/Gender-Disparities-in-LLM-Based-Intimate-Partner-Violence-Detection)

Snapshot auditado: commit `e5643abc53bf334469c0667fdd827cb17182290d`, de 19 de maio de 2026.

## Conclusão

O material é interessante como fonte de narrativas reais em inglês, inspiração para a ontologia e teste de viés por gênero. Ele não deve ser incorporado diretamente como conjunto de treinamento ou gabarito do baseline.

Os principais motivos são:

- somente 100 posts possuem anotações humanas identificáveis;
- o conjunto humano é pequeno, desbalanceado e não apresenta adjudicação final;
- urgência e intenção comunicativa da usuária não são anotadas;
- a taxonomia não coincide com as categorias jurídicas usadas no projeto;
- as versões contrafactuais apresentam resumos, truncamentos e alterações textuais além de gênero;
- o repositório não contém licença de uso;
- os arquivos brutos preservam autores, identificadores, links e textos completos do Reddit.

## O que existe no repositório

| Camada | Arquivo ou diretório | Conteúdo | Natureza dos rótulos |
|---|---|---|---|
| Corpus bruto | `data/relationship_advice...submissions.csv` | 10.000 posts de `r/relationship_advice`, entre 2009 e 2022 | Sem rótulo de IPV |
| Seleção por gênero | `data/Gender_related_sextual_violence.csv` | 491 registros, com idade e gênero inferidos | Sem gabarito de violência |
| Contrafactuais | `data by Dyad/` e CSVs equivalentes | Quatro versões por configuração vítima/agressor | Transformação textual, não anotação humana |
| Avaliações de modelos | CSVs com GPT, Grok, Gemini e Llama | Respostas e campos extraídos das LLMs | Predições dos modelos |
| Anotações humanas | `annotations_export_real_20260218_annotator_numid.csv` | 212 anotações sobre 100 posts principais e alguns registros de teste | Dois anotadores regulares, mais registros de teste |

O arquivo `data/2026_IPV_dataset.csv`, apesar do nome, não é um conjunto integralmente rotulado por especialistas. Seus campos de IPV são predominantemente resultados processados de modelos.

## Anotações humanas

Removendo os 12 registros do conjunto `Trial A`, restam:

- 100 posts;
- duas anotações por post;
- anotadores `2` e `3`;
- textos com mediana de aproximadamente 395 palavras;
- mínimo de 35 e máximo de 1.780 palavras.

O notebook de análise remove os anotadores `3` e `4` e utiliza o anotador `2` como referência. Não foi encontrada uma justificativa metodológica ou uma coluna de adjudicação que transforme as duas opiniões em um gabarito final.

### Distribuição do anotador usado pelo notebook

| Campo | Positivo | Negativo | Indeterminado |
|---|---:|---:|---:|
| `IS_IPV` | 9 | 83 | 8 |
| `HAS_INTENT` | 10 | 81 | 9 |
| `HAS_IMPACT` | 12 | 78 | 10 |
| `ABUSE_PHYS` | 3 | 97 | 0 |
| `ABUSE_SEXL` | 5 | 95 | 0 |
| `ABUSE_EMOT` | 31 | 69 | 0 |
| `ABUSE_PSYC` | 5 | 95 | 0 |
| `ABUSE_FINL` | 2 | 98 | 0 |
| `ABUSE_TECH` | 5 | 95 | 0 |

A quantidade de positivos é insuficiente para treinar ou comparar de forma estável classificadores para várias dessas classes.

### Concordância entre os dois anotadores

| Campo | Concordância observada | Cohen κ |
|---|---:|---:|
| `IS_IPV` | 82% | 0,435 |
| `HAS_INTENT` | 82% | 0,470 |
| `HAS_IMPACT` | 79% | 0,414 |
| `ABUSE_PHYS` | 98% | 0,656 |
| `ABUSE_SEXL` | 97% | 0,559 |
| `ABUSE_EMOT` | 80% | 0,477 |
| `ABUSE_PSYC` | 85% | 0,348 |
| `ABUSE_FINL` | 97% | 0,385 |
| `ABUSE_TECH` | 98% | 0,823 |

A concordância percentual elevada em classes raras deve ser interpretada com cuidado. Por exemplo, quase todos os registros são negativos para violência financeira, o que aumenta a concordância bruta sem produzir um κ alto.

Para `IS_IPV`, houve concordância em 82 posts. Em 18 houve divergência; seis eram conflitos diretos entre positivo e negativo, e doze envolviam valor indeterminado ou ausente.

## Compatibilidade com o baseline

| Necessidade do projeto | Campo mais próximo | Compatibilidade |
|---|---|---|
| Violência física | `ABUSE_PHYS` | Boa em conceito, poucos positivos |
| Violência sexual | `ABUSE_SEXL` | Boa em conceito, poucos positivos |
| Violência psicológica | `ABUSE_PSYC` e `ABUSE_EMOT` | Exige regra de consolidação e revisão |
| Violência patrimonial | `ABUSE_FINL` | Aproximação parcial; financeira é mais estreita |
| Violência moral | Nenhum | Não coberta diretamente |
| Violência vicária | Nenhum | Não coberta diretamente |
| Violência facilitada por tecnologia | `ABUSE_TECH` | Dimensão útil, mas não é uma categoria jurídica equivalente |
| Urgência | Nenhum | Não coberta |
| Intenção comunicativa da usuária | Nenhum | Não coberta |
| Intenção de exercer poder e controle | `HAS_INTENT` | Conceito diferente da intenção comunicativa |
| Ações já tomadas | `IS_ACTIONTAKEN_IPV` e referências | Útil para enriquecer memória e estado |

O conceito de `IS_IPV` adotado nas explicações dos anotadores enfatiza intenção e padrão de poder e controle. Isso pode classificar como `IS_IPV = 0` situações com dano emocional ou outra conduta inadequada. Portanto, `IS_IPV` não deve substituir diretamente o rótulo multirrótulo de indícios usado no baseline brasileiro.

## Problemas das versões contrafactuais

O README afirma que as quatro versões preservam integralmente a narrativa e alteram programaticamente pronomes, marcadores de gênero e identificadores familiares. Os arquivos não sustentam essa afirmação em todos os registros.

Nos 479 casos com as quatro versões preenchidas:

- a versão original tem mediana de 344 palavras;
- as versões contrafactuais têm medianas entre 125 e 150 palavras;
- 55 casos apresentam diferença superior a 1,5 vez entre a maior e a menor versão;
- sete apresentam diferença superior a duas vezes;
- a similaridade mediana de caracteres entre a versão `M/M` e as demais é aproximadamente 0,745;
- 268 dos 479 casos têm similaridade mínima inferior a 0,8;
- existem células que resumem a história em poucas palavras ou terminam incompletas.

Essas diferenças introduzem um fator de confusão: uma mudança na resposta do modelo pode ser causada pela alteração do conteúdo, extensão ou formulação, além do gênero. Para um teste contrafactual rigoroso, as variações precisam ser reconstruídas a partir de uma representação estruturada e validadas antes da avaliação.

## Proveniência, privacidade e licença

O corpus bruto contém colunas como `author`, `id` e `permalink`, além do texto integral. Mesmo sendo conteúdo público, o tema é sensível e alguns textos podem conter informações pessoais no corpo da postagem.

O repositório não possui `LICENSE` nem uma licença indicada no README. Isso torna incerta a autorização para redistribuição, tradução e criação de derivados. Antes de incorporar textos ao projeto, é necessário esclarecer a licença com os autores e avaliar as regras aplicáveis ao conteúdo do Reddit.

Se o material for usado internamente para pesquisa, recomenda-se:

1. eliminar autor, link, identificadores e metadados desnecessários;
2. inspecionar o texto para nomes, locais, contatos e outros identificadores;
3. não publicar traduções ou cópias integrais sem licença clara;
4. registrar a origem e a transformação de cada exemplo;
5. impedir que o mesmo post, ou uma paráfrase dele, apareça em treino e teste.

## Uso recomendado no projeto

### 1. Avaliação externa pequena

Usar os 100 posts humanos como fonte para selecionar casos difíceis e negativos realistas. Não usar automaticamente o anotador `2` como verdade final. Preservar as duas anotações e adjudicar manualmente um subconjunto adequado ao objetivo do projeto.

Uma primeira rodada poderia selecionar:

- todos os casos positivos ou indeterminados em `IS_IPV` por pelo menos um anotador;
- todos os positivos de classes raras;
- uma amostra de negativos com linguagem ambígua;
- exemplos em que os anotadores divergiram.

Após tradução, cada caso precisaria receber novos rótulos de tipos brasileiros, urgência e intenção comunicativa.

### 2. Fonte de fenômenos para geração sintética

Usar padrões abstratos extraídos dos posts, sem copiar suas histórias. Exemplos de fenômenos úteis:

- dúvida sobre reconhecer abuso;
- normalização de controle recorrente;
- relato feito por terceira pessoa;
- episódio passado com impacto atual;
- ação de proteção já iniciada;
- uso de tecnologia;
- ambiguidade entre conflito e padrão de controle.

Esses fenômenos podem ampliar as fichas sintéticas e tornar os casos menos esquemáticos.

### 3. Teste de viés

O desenho contrafactual é valioso, mas as quatro versões devem ser regeneradas de forma determinística. O caso deve existir primeiro como fatos estruturados, com papéis separados de gênero. A renderização textual muda apenas os campos necessários, seguida de uma validação que compare eventos, relações, tempo, gravidade e extensão.

Para a aplicação atual, faz mais sentido manter a pessoa atendida como mulher e variar o gênero e o vínculo da pessoa agressora. O teste com todos os quatro pares pode permanecer como análise complementar de comportamento do modelo.

### 4. Não usar para treinamento neste momento

O conjunto humano é pequeno demais para treinar os classificadores multirrótulo planejados. O uso mais defensável no MVP é como avaliação exploratória, fonte de casos difíceis e referência para desenhar novas fichas. Um treinamento futuro exigiria mais anotações, adjudicação e uma taxonomia alinhada ao contexto brasileiro.

## Próximo experimento sugerido

1. Importar somente a tabela de anotações humanas em uma área de trabalho separada.
2. Remover identificadores e conservar um hash local da origem.
3. Selecionar de 25 a 40 posts por diversidade e dificuldade, sem usar as predições das LLMs como gabarito.
4. Fazer tradução e adaptação cultural, evitando tradução literal de instituições e procedimentos dos Estados Unidos.
5. Rotular manualmente tipos brasileiros, urgência e intenção comunicativa.
6. Manter um campo separado para os rótulos originais e para os rótulos adaptados.
7. Usar esse subconjunto como teste externo, separado das fichas sintéticas e dos prompts de desenvolvimento.

Essa estratégia aproveita a naturalidade dos relatos do Reddit sem misturar rótulos de modelo, transformações contrafactuais defeituosas e conceitos jurídicos incompatíveis.
