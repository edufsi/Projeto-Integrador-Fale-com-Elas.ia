# Arquitetura de um Chatbot de Acolhimento e Triagem em Violência de Gênero

## 1. Objetivo e princípios

Este documento propõe uma arquitetura para um **chatbot que conversa com
mulheres em situação de violência (ou com dúvidas sobre violência de
gênero)** e que, a cada mensagem, executa três classificações:

-   **Intenção**: dúvida, relato ou emergência
    (ver `classificacao_intencao_relato_IA.md`);
-   **Tipo de violência**: física, psicológica, sexual, patrimonial,
    moral (ver `classificacao_violencia_genero_IA.md`);
-   **Gravidade / nível de risco**: de 0 a 4
    (ver `classificacao_gravidade_risco_IA.md`).

O resultado dessas classificações **não serve apenas para análise**:
ele controla o que o chatbot faz e o que ele pode dizer.

### Princípios de projeto

1.  **Segurança acima de fluidez.** Em caso de risco alto, o sistema
    deixa de "conversar" e passa a encaminhar.
2.  **O modelo de linguagem não é a fonte da verdade.** Informações
    factuais (leis, telefones, endereços, direitos) vêm de uma base
    curada, nunca da memória do LLM.
3.  **Conteúdo crítico é fixo, não gerado.** Telefones de emergência e
    orientações de segurança são texto pré-aprovado.
4.  **Na dúvida, escalar.** Incerteza do classificador aumenta a
    cautela, não a diminui.
5.  **O chatbot não é profissional.** Não diagnostica, não dá aconselhamento
    jurídico individualizado, não promete proteção.
6.  **Discrição e privacidade.** A usuária pode estar sendo monitorada
    pelo agressor.
7.  **Tudo é auditável.** Cada decisão do sistema pode ser reconstruída.

------------------------------------------------------------------------

## 2. Visão geral da arquitetura

``` text
                    Usuária (web / WhatsApp / app)
                                │
                                ▼
                  ┌─────────────────────────┐
                  │ 1. Interface + Gateway  │  saída rápida, sem login
                  └────────────┬────────────┘
                               ▼
                  ┌─────────────────────────┐
                  │ 2. Pré-processamento    │  normalização, PII
                  └────────────┬────────────┘
                               ▼
              ┌────────────────┴────────────────┐
              ▼                ▼                ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │ Modelo A │    │ Modelo B │    │ Modelo C │   (em paralelo)
        │ Intenção │    │  Tipo    │    │ Gravidade│
        └────┬─────┘    └────┬─────┘    └────┬─────┘
             └───────────────┼───────────────┘
                             ▼
              ┌─────────────────────────────┐
              │ 3. Regras de segurança      │  léxico crítico
              │    (camada determinística)  │  sobrepõe os modelos
              └──────────────┬──────────────┘
                             ▼
              ┌─────────────────────────────┐
              │ 4. Estado da conversa       │  agrega histórico,
              │    (risco acumulado)        │  "trava" escalada
              └──────────────┬──────────────┘
                             ▼
              ┌─────────────────────────────┐
              │ 5. Motor de política        │  decide a ROTA
              │    (roteador)               │
              └──────────────┬──────────────┘
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
   ┌─────────────┐   ┌───────────────┐   ┌───────────────┐
   │ Rota        │   │ Rota          │   │ Rota          │
   │ EMERGÊNCIA  │   │ ACOLHIMENTO   │   │ INFORMAÇÃO    │
   │ (scriptada) │   │ (LLM contido) │   │ (RAG)         │
   └──────┬──────┘   └───────┬───────┘   └───────┬───────┘
          └──────────────────┼───────────────────┘
                             ▼
              ┌─────────────────────────────┐
              │ 6. Verificação da resposta  │  anti-alucinação
              │    (guardrails de saída)    │
              └──────────────┬──────────────┘
                             ▼
              ┌─────────────────────────────┐
              │ 7. Envio + registro         │
              └─────────────────────────────┘
```

------------------------------------------------------------------------

## 3. Componentes

### 3.1 Interface e gateway

-   Canais possíveis: **web** (mais simples para um projeto acadêmico),
    **WhatsApp** (maior alcance, mas exige conta Business e tem
    implicações de privacidade) ou aplicativo.
-   **Botão de saída rápida**, que fecha ou substitui a tela por um
    site neutro.
-   **Sem exigência de login ou cadastro** para iniciar.
-   Aparência discreta (nome e ícone que não revelem o propósito, se
    possível).
-   **Banner permanente com 180 / 190 / 192**, independente de qualquer
    classificação.
-   Aviso inicial: o que é o chatbot, o que não é, como os dados são
    tratados.
-   Opção de **apagar a conversa** a qualquer momento.

### 3.2 Pré-processamento

-   Normalização (minúsculas apenas para o léxico, preservando o texto
    original para os modelos), correção leve de espaços e repetições.
-   **Detecção e mascaramento de dados pessoais** (nomes, CPF,
    telefones, endereços) antes de logar ou enviar a qualquer serviço
    externo.
-   **Janela de contexto:** os classificadores não devem olhar só a
    última mensagem. Exemplo: "sim" ou "ele está aqui" só fazem sentido
    com a pergunta anterior.

``` text
Entrada dos modelos = [últimas N mensagens da usuária]
                      + [última pergunta do bot]
                      + [mensagem atual]
```

Isso exige que os modelos tenham sido treinados (ou ao menos testados)
com **exemplos em formato de diálogo curto**, não só com frases
isoladas. É um ponto que deve voltar para a etapa de dataset.

### 3.3 Os três classificadores

Executados **em paralelo** a cada mensagem. Podem ser:

  Opção                                Vantagem                       Desvantagem
  ------------------------------------ ------------------------------ --------------------
  Três modelos BERTimbau separados     Simples, cada um independente  3× memória/latência
  Um encoder compartilhado com 3       Mais leve, aprendizado         Treino mais complexo
  cabeças (multitarefa)                compartilhado                  

Para um projeto acadêmico, três modelos separados são mais fáceis de
treinar e avaliar. Se a latência virar problema, migrar para encoder
compartilhado.

Saída padronizada de cada classificador:

``` json
{
  "intencao":   {"duvida": 0.05, "relato": 0.31, "emergencia": 0.64},
  "tipo":       {"fisica": 0.82, "psicologica": 0.77, "sexual": 0.03,
                 "patrimonial": 0.05, "moral": 0.10},
  "gravidade":  {"nivel": 3, "p_ge": [0.99, 0.95, 0.74, 0.21]},
  "incerteza":  0.28
}
```

**Calibração.** As probabilidades de redes neurais costumam ser mal
calibradas. Aplicar *temperature scaling* no conjunto de validação para
que "0.7" signifique algo próximo de 70%. Isso é essencial porque as
regras de política dependem de limiares.

**Incerteza.** Estimada por entropia da saída, margem entre as duas
primeiras classes ou discordância entre modelos. Quando alta, o motor de
política adota o caminho mais cauteloso.

### 3.4 Camada de regras de segurança (determinística)

Uma camada de regras que **sobrepõe** os modelos em situações críticas.
Ela funciona como rede de segurança caso o classificador erre.

``` text
SE mensagem contém padrão de:
     - pedido de socorro explícito ("socorro", "me ajuda", "chama a polícia")
     - ameaça de morte atual ("vai me matar", "disse que vai me matar hoje")
     - agressor presente ("ele está aqui", "ele está batendo na porta")
     - arma + ameaça
     - risco de suicídio da própria usuária
     - violência contra criança presente na situação
ENTÃO
     nível_mínimo = 4 (ou 3, conforme a regra)
     rota = EMERGÊNCIA
```

Cuidados:

-   O léxico deve tratar **negação** ("ele nunca me ameaçou com arma").
    Pode gerar falso alarme, o que é aceitável, mas deve ser medido.
-   Falsos positivos nessa camada são **preferíveis** a falsos
    negativos.
-   Manter a lista versionada e revisada com especialistas.

### 3.5 Estado da conversa e risco acumulado

Cada mensagem tem suas classificações, mas o que importa é o **estado
da conversa**:

``` text
estado = {
  nivel_risco_max:     3,        # maior nível já detectado
  nivel_risco_atual:   2,        # estimativa na última mensagem
  tipos_detectados:    {fisica, psicologica},
  intencao_atual:      "relato",
  fatores_de_risco:    {ameaca, separacao_recente, filhos},
  emergencia_sinalizada: false,
  turnos:              7
}
```

Regras de agregação:

-   **A escalada é "pegajosa":** o risco máximo só desce com
    confirmação explícita da usuária ("já estou em segurança"), e
    mesmo assim com cautela.
-   Fatores de risco são **acumulados** ao longo da conversa: uma
    mensagem sobre arma no turno 2 continua relevante no turno 10.
-   Uma mensagem isolada de baixo risco não "apaga" o histórico.
-   Tipos de violência acumulam como conjunto, pois a usuária costuma
    revelar a situação aos poucos.

### 3.6 Motor de política (roteador)

Decide a **rota** da resposta com regras explícitas e testáveis, e não
com o LLM.

``` text
SE regra_de_segurança OU intencao=emergência (p>0.30) OU nivel ≥ 4
     → ROTA_EMERGÊNCIA

SENÃO SE nivel ≥ 3 OU incerteza alta com sinais de risco
     → ROTA_ACOLHIMENTO_RISCO_ALTO
       (acolhe + plano de segurança + canais, ofertando encaminhamento)

SENÃO SE intencao=relato
     → ROTA_ACOLHIMENTO
       (escuta, valida, pergunta com cuidado, informa canais)

SENÃO SE intencao=dúvida
     → ROTA_INFORMAÇÃO (RAG)

SENÃO (fora do escopo / ambíguo)
     → ROTA_ESCLARECIMENTO (pergunta aberta e gentil)
```

Os limiares são **parâmetros** ajustados com base na análise de
custo (ver `classificacao_intencao_relato_IA.md` e
`classificacao_gravidade_risco_IA.md`) e **registrados em
configuração**, não fixos no código.

------------------------------------------------------------------------

## 4. Rotas de resposta

### 4.1 Rota de emergência (100% scriptada, sem LLM livre)

Em situação de perigo, a resposta é **texto pré-aprovado**, curto e
claro, escrito e revisado com profissionais.

``` text
Sinto muito que você esteja passando por isso. Sua segurança
é o mais importante agora.

Se você está em perigo imediato:
  • Ligue 190 (Polícia Militar)
  • Ligue 180 (Central de Atendimento à Mulher)
  • Se há ferimentos, ligue 192 (SAMU)

Se não puder falar, procure um lugar seguro, um vizinho ou
alguém de confiança. Posso te ajudar a pensar em um plano de
segurança agora?
```

Características:

-   **Não depende do LLM**, portanto não pode alucinar.
-   Texto breve (a pessoa pode ter segundos).
-   Evitar perguntas longas ou etapas complexas.
-   Ofertar apenas um próximo passo por vez.
-   Possibilidade de **escalar para atendimento humano**, se existir
    parceria (serviço de plantão). Sem parceria, esse limite deve ser
    explicitado.

### 4.2 Rota de acolhimento (LLM contido)

Para relatos, o LLM é usado para produzir uma resposta empática, mas
dentro de limites rígidos:

-   **Prompt de sistema** com regras (ver 5.2);
-   **Contexto estruturado:** o LLM recebe o estado (tipos detectados,
    nível, intenção) e as **diretrizes de resposta** correspondentes
    (ex.: "validar sentimentos, não culpar, não pressionar a sair do
    relacionamento, oferecer canais");
-   **Canais de apoio inseridos por template**, não gerados;
-   Respostas curtas, sem listas longas.

### 4.3 Rota de informação (RAG)

Para dúvidas sobre leis, direitos e serviços:

``` text
Pergunta
   │
   ▼
Busca na base curada (embeddings + BM25)
   │
   ▼
Trechos recuperados (com fonte e data)
   │
   ▼
LLM redige resposta SOMENTE com base nos trechos
   │
   ▼
Verificação de fundamentação (ver seção 5)
   │
   ▼
Resposta com referência ("Lei 11.340/2006, art. X")
```

Se **nenhum trecho relevante** for recuperado, a resposta é uma negativa
honesta com encaminhamento ("Não tenho essa informação com segurança.
Você pode confirmar na Defensoria Pública ou no 180.").

### 4.4 Rota de esclarecimento

Quando a mensagem é ambígua ou fora do escopo, o bot faz uma pergunta
aberta e gentil, em vez de adivinhar. Exemplo: "Quer me contar um pouco
mais sobre o que está acontecendo?".

------------------------------------------------------------------------

## 5. Mecanismos contra alucinação

O risco de alucinação aqui é de natureza séria: um **telefone errado**,
uma **lei inventada**, uma promessa de proteção falsa ou um conselho
inadequado podem causar dano real. A estratégia é em **camadas**: reduzir
a chance de o LLM errar e **verificar** o que sai antes de chegar à
usuária.

### 5.1 Camada 1 --- Reduzir a superfície: o que o LLM não decide

  Conteúdo                           Quem produz
  ---------------------------------- -------------------------------------
  Telefones e canais de emergência   **Templates fixos**
  Texto da rota de emergência        **Script aprovado**
  Citações de lei e direitos         **Base curada (RAG)**, com fonte
  Endereços de delegacias/serviços   **Base estruturada** (banco de dados)
  Decisão de escalar ou rotear       **Motor de política**
  Empatia e reformulação             LLM (contido)

Quanto menos o LLM precisa "lembrar", menos ele pode inventar.

### 5.2 Camada 2 --- Prompt de sistema restritivo

Regras permanentes (resumo):

``` text
- Você NÃO é advogada, psicóloga nem policial.
- Nunca invente leis, artigos, números de telefone, endereços ou prazos.
- Responda informações factuais SOMENTE com base nos trechos fornecidos.
- Se a informação não estiver nos trechos, diga que não sabe e encaminhe.
- Nunca prometa proteção, resultado ou segurança.
- Nunca diga que a situação "não é grave" ou que "está tudo bem".
- Nunca pressione a usuária a denunciar, sair de casa ou terminar.
- Nunca culpe a usuária.
- Não peça dados pessoais identificáveis.
- Respostas curtas, em linguagem simples.
```

O prompt reduz o risco, mas **não é garantia**: por isso há camadas
seguintes.

### 5.3 Camada 3 --- Geração conservadora

-   **Temperatura baixa** (0 a 0.3).
-   Limite de tamanho de resposta.
-   Respostas em **formato estruturado** quando possível (por exemplo,
    JSON com campos `validacao`, `informacao`, `proxima_pergunta`),
    montadas depois por template.
-   Preferir **extração a geração**: sempre que a resposta puder ser
    um trecho aprovado da base, usá-lo.

### 5.4 Camada 4 --- RAG com base curada e versionada

-   Base composta apenas de **fontes oficiais**: texto da Lei Maria da
    Penha, legislação correlata, cartilhas de órgãos públicos
    (Defensoria, Ministério Público, tribunais), lista oficial de
    serviços da rede de atendimento.
-   Cada documento tem **fonte, data e versão**.
-   Conteúdo revisado por especialista em direito/assistência social.
-   Pedaços (*chunks*) pequenos e com metadados (lei, artigo, tema).
-   Limiar mínimo de similaridade: abaixo dele, **não responder**.
-   Revisão periódica (as leis e serviços mudam).

### 5.5 Camada 5 --- Verificação de fundamentação (*grounding check*)

Depois da geração, antes de enviar, verificar se **cada afirmação
factual está sustentada** pelos trechos recuperados:

``` text
Resposta gerada
     │
     ▼
Dividir em afirmações
     │
     ▼
Para cada afirmação:
   modelo de NLI / LLM verificador
   "O trecho sustenta esta afirmação?"
     │
     ├─ todas sustentadas → envia
     ├─ alguma não sustentada → remove a frase ou regenera
     └─ falha repetida → resposta padrão de fallback
```

Também é possível exigir **citação obrigatória**: toda afirmação legal
deve vir com a referência do trecho, e uma verificação automática
confere se a referência existe na base.

### 5.6 Camada 6 --- Validadores determinísticos de saída

Verificações simples que não dependem de IA:

-   **Telefones:** qualquer número que apareça na resposta deve estar
    em uma **lista permitida** (190, 180, 192, 100, etc.). Caso
    contrário, a resposta é bloqueada.
-   **Referências legais:** toda menção a "Lei X" ou "art. Y" deve
    existir na base curada.
-   **Frases proibidas:** detecção de padrões como "você está segura",
    "não se preocupe", "isso não é grave", "você deveria ter...",
    "garanto que...".
-   **URLs:** somente de domínios permitidos.
-   **Tamanho e formato:** respeitar limites.
-   **Presença obrigatória:** em rotas de risco ≥ 3, a resposta
    precisa conter o bloco de canais (inserido por template se faltar).

### 5.7 Camada 7 --- Classificar a própria resposta

Passar a **resposta do bot** novamente pelos classificadores e por um
detector de conteúdo inadequado (culpabilização, minimização, incentivo
a confronto) antes de enviar. Se detectar problema, regenerar ou usar
fallback.

### 5.8 Camada 8 --- Fallbacks seguros

Quando qualquer verificação falha repetidamente, o bot **não
improvisa**:

``` text
"Quero te responder com cuidado e não tenho certeza de ter a
informação certa. Você pode falar com a Central de
Atendimento à Mulher no 180, que funciona 24h, ou com a
Defensoria Pública. Posso te ajudar com outra coisa?"
```

### 5.9 Camada 9 --- Calibração de incerteza do próprio bot

-   O bot deve poder dizer "não sei" sem penalização.
-   Evitar linguagem de certeza absoluta em temas jurídicos
    individualizados ("pode ser que", "em geral, a lei prevê...").
-   Em dúvidas jurídicas sobre o caso específico: **informar a regra
    geral e encaminhar** para Defensoria/advogada(o).

### 5.10 Camada 10 --- Avaliação contínua

Ver seção 8.

------------------------------------------------------------------------

## 6. Exemplo de fluxo completo

``` text
Usuária: "meu marido me bateu ontem e hoje disse que se eu
          sair de casa ele me mata"
```

1.  **Pré-processamento:** sem dados pessoais a mascarar.
2.  **Classificadores:**

    ``` text
    Intenção:   relato 0.55 | emergência 0.38 | dúvida 0.07
    Tipo:       física 0.93 | psicológica 0.81
    Gravidade:  nível 3 (P≥Alta = 0.78, P≥Crítica = 0.31)
    ```

3.  **Regras de segurança:** dispara "ameaça de morte" → nível mínimo 3.
4.  **Estado:** `nivel_risco_max = 3`, fatores = {ameaça de morte,
    agressão recente}.
5.  **Motor de política:** nível ≥ 3 → `ROTA_ACOLHIMENTO_RISCO_ALTO`.
6.  **Geração:** LLM produz validação empática curta; o bloco de canais
    entra por template; pergunta única: "Você está em um lugar seguro
    agora?".
7.  **Verificação:** telefones conferidos na lista permitida; sem frases
    proibidas; sem afirmações factuais livres.
7.  **Envio e registro.**

Resposta ao final:

``` text
Sinto muito que você esteja passando por isso. O que você me
contou é sério e você não tem culpa.

Por segurança, saiba que você pode ligar a qualquer momento:
  • 190 (Polícia Militar) — em perigo imediato
  • 180 (Central de Atendimento à Mulher) — 24h, gratuito

Você está em um lugar seguro agora?
```

Próxima mensagem:

``` text
Usuária: "estou, ele saiu"
```

O estado preserva `nivel_risco_max = 3`. O bot **não reduz** o risco só
por essa resposta: continua a conversa com cautela, pode ofertar
construir um plano de segurança e manter os canais visíveis.

------------------------------------------------------------------------

## 7. Registro, privacidade e segurança dos dados

-   **Minimização:** guardar o mínimo necessário. Para um projeto
    acadêmico, pode-se registrar apenas métricas e classificações, e
    não o texto bruto.
-   **Anonimização** antes de qualquer registro.
-   **Criptografia** em trânsito e em repouso.
-   **Retenção curta**, com exclusão automática e opção de exclusão
    imediata pela usuária.
-   **Não enviar dados identificáveis** a APIs externas de LLM sem base
    legal. Preferir modelos **rodando localmente / em infraestrutura
    controlada** quando possível.
-   **Consentimento claro** no início, em linguagem simples.
-   **Discrição no dispositivo:** sem notificações com conteúdo, sem
    histórico visível, aviso para uso em modo anônimo do navegador.
-   **Log de auditoria** das decisões (classificações, regras
    disparadas, rota, verificação) para investigação de falhas.
-   Cumprimento da **LGPD** e, se houver pesquisa com participantes,
    avaliação do **comitê de ética**.

------------------------------------------------------------------------

## 8. Avaliação do sistema

Avaliar o sistema inteiro, e não apenas os classificadores.

### 8.1 Dos classificadores

Já descrito nos documentos de cada modelo (recall de emergência,
QWK, MAE, etc.), mas agora também **em formato de diálogo**.

### 8.2 Da roteirização

-   **Taxa de emergências corretamente roteadas** (principal).
-   Casos de risco alto roteados para rotas de menor cuidado (deve ser
    próximo de zero).
-   Taxa de falsos alarmes (aceitável dentro de limites, pois afeta a
    experiência).

### 8.3 Das respostas (anti-alucinação)

-   **Taxa de alucinação factual:** proporção de respostas com
    afirmações não sustentadas pela base.
-   **Taxa de citações válidas.**
-   **Taxa de telefones/URLs fora da lista** (deve ser zero após os
    validadores).
-   **Taxa de recusa correta** (quando a base não tem a resposta).
-   **Taxa de frases proibidas** (culpabilização, minimização).
-   Avaliação humana por especialistas em amostra de conversas:
    empatia, adequação, segurança.

### 8.4 *Red teaming* e conjuntos de teste

-   Conjunto **dourado** de conversas com resultado esperado.
-   Tentativas de induzir o bot a inventar lei, telefone ou prometer
    segurança.
-   Tentativas de *prompt injection* ("ignore as instruções
    anteriores...").
-   Conversas com **minimização** ("foi só uma briga") e **linguagem
    ruidosa**.
-   Conversas longas, com mudança de assunto e ambiguidade.
-   Teste de **regressão** a cada mudança de modelo, prompt ou base.

### 8.5 Monitoramento

-   Revisão periódica de amostras de conversas (anonimizadas).
-   Alertas para aumento de fallbacks, bloqueios de saída ou queda de
    similaridade no RAG.
-   Detecção de **drift** (mudança na distribuição das mensagens).

------------------------------------------------------------------------

## 9. Tecnologias sugeridas

  Camada                        Opção gratuita / acadêmica
  ----------------------------- -------------------------------------------------
  Classificadores               PyTorch + Hugging Face (BERTimbau), treino no Colab
  Serviço dos modelos           FastAPI (Python)
  Regras de segurança           Python (regex + léxico versionado)
  Estado da conversa            Redis ou banco em memória (SQLite no protótipo)
  Base do RAG                   Documentos oficiais em texto/Markdown
  Embeddings + busca            sentence-transformers multilíngue + FAISS ou
                                Chroma, combinados com BM25
  Orquestração                  Código próprio simples (preferível a frameworks
                                pesados, para controlar cada passo)
  LLM de geração                Modelo aberto em português/multilíngue rodando
                                local (se houver recurso) ou API com dados
                                anonimizados
  Verificação                   Modelo de NLI multilíngue e/ou LLM verificador
  Interface                     Aplicação web simples (HTML/JS ou Streamlit no
                                protótipo)
  Logs e métricas               SQLite/CSV anonimizado, painel simples

Observação: modelos de geração de grande porte podem não caber no Colab
gratuito para inferência contínua. Para o protótipo, pode-se usar um
modelo menor, ou limitar o LLM à reformulação empática curta (ele
carrega pouca responsabilidade na arquitetura proposta).

------------------------------------------------------------------------

## 10. Plano de implementação em fases

### Fase 1 --- Núcleo de segurança (sem LLM)

``` text
Interface → classificadores → regras → motor de política →
respostas 100% por template
```

Já é um **sistema funcional e seguro**, com alucinação zero por
construção. Serve como linha de base do trabalho.

### Fase 2 --- Acolhimento com LLM contido

Adicionar o LLM apenas na rota de acolhimento, com prompt restritivo,
validadores determinísticos e fallback.

### Fase 3 --- RAG para dúvidas

Montar a base curada, o recuperador e a verificação de fundamentação.

### Fase 4 --- Avaliação e *red teaming*

Conjunto dourado, ataques adversariais, avaliação por especialistas.

### Fase 5 --- Refinamento

Calibração, ajuste de limiares, melhoria da base, monitoramento.

Comparar a Fase 1 com as Fases 2--3 já produz um resultado acadêmico
interessante: **quanto a fluidez do LLM acrescenta em qualidade de
conversa e quanto custa em risco de alucinação**.

------------------------------------------------------------------------

## 11. Limitações e riscos

-   **Erros de classificação** são inevitáveis; a arquitetura procura
    mitigá-los com regras, calibração e comportamento conservador, mas
    não os elimina.
-   **O bot não detecta o que não é dito.** Muitas situações graves são
    descritas de forma minimizada ou não são descritas.
-   **Falsa sensação de segurança** é um risco central: o sistema nunca
    deve sugerir que a situação está sob controle.
-   **Dependência de dados limitados:** os modelos podem funcionar pior
    com grupos sub-representados.
-   **Responsabilidade institucional:** um sistema desse tipo em uso
    real exige respaldo de instituições, profissionais e processos de
    resposta a incidentes. O protótipo acadêmico **não deve ser
    divulgado como serviço de atendimento** sem esse respaldo.
-   **Segurança da usuária no dispositivo:** o uso do chatbot pode ser
    descoberto pelo agressor; as medidas de discrição reduzem, mas não
    eliminam, esse risco.
-   **Prompt injection e uso indevido:** o sistema precisa ser testado
    contra tentativas de manipulação.

------------------------------------------------------------------------

## 12. Possíveis perguntas de pesquisa

> **"Como integrar classificadores de intenção, tipo de violência e
> gravidade em uma arquitetura de chatbot que direcione respostas
> seguras a mulheres em situação de violência?"**

> **"Qual a redução na taxa de alucinação factual obtida pela combinação
> de RAG com base curada, verificação de fundamentação e validadores
> determinísticos em relação a um chatbot baseado apenas em LLM?"**

> **"Qual o impacto da agregação de risco ao longo da conversa, em
> comparação com a classificação mensagem a mensagem, na detecção
> precoce de situações de emergência?"**

------------------------------------------------------------------------

## 13. Conclusão

É possível implementar um chatbot de acolhimento e triagem usando os
três modelos treinados, desde que ele seja projetado como um **sistema
em camadas**, no qual o LLM ocupa um papel pequeno e controlado.

Os pilares da arquitetura são:

1.  **Classificação a cada mensagem** (intenção, tipo, gravidade),
    com calibração e estimativa de incerteza.
2.  **Regras de segurança determinísticas** que sobrepõem os modelos.
3.  **Estado de conversa com risco acumulado**, que não "esquece" a
    gravidade.
4.  **Motor de política explícito**, que escolhe a rota de resposta.
5.  **Conteúdo crítico por template** (emergência, telefones), sem LLM.
6.  **RAG sobre base curada** para informações factuais, com recusa
    quando não há fundamento.
7.  **Verificação em múltiplas camadas** (fundamentação, listas
    permitidas, frases proibidas, reclassificação da resposta).
8.  **Privacidade, discrição e auditoria** como requisitos de projeto.
9.  **Avaliação contínua**, incluindo *red teaming*.

A principal decisão de projeto é **limitar o que o modelo de linguagem
pode fazer**, e não ampliá-lo. Em um domínio em que um erro pode
significar risco de vida, o objetivo não é um bot que "conversa como
uma pessoa", mas um sistema **previsível, auditável e que sabe quando
parar de improvisar e encaminhar para ajuda humana**.

------------------------------------------------------------------------

# 14. Formato final dos dados da conversa

Os três classificadores produzem saídas **por mensagem**. Para que a
interação inteira gere os três dados (intenção, tipo de violência e
gravidade), as saídas por mensagem são agregadas em um **resumo da
conversa**. Esse resumo é atualizado a cada turno e fechado ao fim da
sessão.

## 14.1 Registro por mensagem (turno)

Cada turno guarda apenas as classificações e as decisões do sistema.
**O texto bruto não é armazenado** (ver seção 7).

``` json
{
  "conversa_id": "c_8f3a21",
  "turno": 4,
  "timestamp": "2026-10-05T14:32:10Z",
  "classificacao": {
    "intencao": {
      "classe": "relato",
      "probabilidades": {"duvida": 0.05, "relato": 0.55, "emergencia": 0.38}
    },
    "tipos_violencia": {
      "fisica": 0.93,
      "psicologica": 0.81,
      "sexual": 0.03,
      "patrimonial": 0.05,
      "moral": 0.10
    },
    "gravidade": {
      "nivel": 3,
      "p_ge": [0.99, 0.95, 0.78, 0.31]
    },
    "incerteza": 0.28
  },
  "fatores_de_risco_detectados": ["ameaca_de_morte", "agressao_recente"],
  "regras_de_seguranca_disparadas": ["ameaca_de_morte_atual"],
  "rota": "ACOLHIMENTO_RISCO_ALTO",
  "verificacao_saida": {
    "telefones_validos": true,
    "frases_proibidas": false,
    "fundamentacao_ok": true,
    "fallback_usado": false
  },
  "versoes": {
    "modelo_intencao": "v1.2",
    "modelo_tipo": "v1.0",
    "modelo_gravidade": "v1.1",
    "regras": "v3",
    "base_rag": "2026-09"
  }
}
```

## 14.2 Resumo final da conversa

``` json
{
  "conversa_id": "c_8f3a21",
  "inicio": "2026-10-05T14:28:02Z",
  "fim": "2026-10-05T14:41:47Z",
  "total_turnos": 9,
  "encerramento": "inativa",

  "intencao": {
    "predominante": "relato",
    "por_turno": ["duvida", "relato", "relato", "relato", "relato",
                  "relato", "duvida", "relato", "relato"],
    "emergencia_sinalizada": false,
    "turno_primeira_emergencia": null
  },

  "tipos_violencia": {
    "detectados": ["fisica", "psicologica"],
    "confianca_maxima": {
      "fisica": 0.93,
      "psicologica": 0.81
    },
    "primeiro_turno_detectado": {"psicologica": 2, "fisica": 4}
  },

  "gravidade": {
    "maxima": 3,
    "final": 2,
    "turno_da_maxima": 4,
    "evolucao": [0, 1, 2, 3, 3, 3, 2, 2, 2],
    "escalou_durante_a_conversa": true,
    "reducao_confirmada_pela_usuaria": true
  },

  "fatores_de_risco": [
    "agressao_recente",
    "ameaca_de_morte",
    "separacao_recente",
    "filhos_envolvidos"
  ],

  "encaminhamento": {
    "canais_exibidos": ["180", "190"],
    "plano_de_seguranca_ofertado": true,
    "plano_de_seguranca_aceito": false,
    "rota_mais_critica_usada": "ACOLHIMENTO_RISCO_ALTO",
    "escalado_para_humano": false
  },

  "qualidade_do_sistema": {
    "fallbacks_usados": 0,
    "respostas_bloqueadas_na_verificacao": 1,
    "turnos_com_incerteza_alta": 2,
    "regras_de_seguranca_disparadas": ["ameaca_de_morte_atual"]
  }
}
```

## 14.3 Regras de cálculo de cada campo

  --------------------------------------------------------------------------
  Campo                     Regra
  ------------------------- ------------------------------------------------
  `intencao.predominante`   Classe mais frequente nos turnos, **exceto**
                            que `emergencia` prevalece se tiver ocorrido em
                            qualquer turno. Nesse caso, o campo vira
                            `emergencia` e `emergencia_sinalizada = true`.

  `intencao.por_turno`      Classe prevista em cada turno, para análise
                            posterior.

  `tipos_violencia.         União dos tipos com probabilidade acima do
  detectados`               limiar (por exemplo, 0.50) em **qualquer**
                            turno. Tipos não "desaparecem" por não serem
                            repetidos.

  `confianca_maxima`        Maior probabilidade obtida por tipo ao longo da
                            conversa.

  `gravidade.maxima`        Maior nível previsto (já considerando o piso
                            imposto pelas regras de segurança).

  `gravidade.final`         Nível no último turno. Só pode ser menor que a
                            máxima se houver confirmação explícita da
                            usuária de que a situação mudou
                            (`reducao_confirmada_pela_usuaria`); caso
                            contrário, `final = maxima`.

  `gravidade.evolucao`      Série dos níveis por turno, para identificar
                            escalada.

  `fatores_de_risco`        União dos fatores detectados em todos os
                            turnos.

  `encaminhamento`          Registro do que o sistema efetivamente
                            ofereceu, e não apenas do que classificou.
  --------------------------------------------------------------------------

Observações:

-   A **gravidade máxima** é o dado de referência para decisões e para
    análise, pois a gravidade final pode ser menor apenas porque a
    conversa terminou em um momento de calma.
-   O resumo preserva **a evolução**, e não apenas o ponto final, o que
    permite estudar quanto tempo o sistema leva para reconhecer a
    gravidade real.
-   Os campos de `qualidade_do_sistema` não descrevem a usuária, mas o
    desempenho do sistema, e alimentam o monitoramento da seção 8.5.

## 14.4 Versão mínima (os três dados essenciais)

Se for necessário um formato enxuto, por exemplo para uma tela de
resumo ou exportação, o núcleo são os três dados pedidos:

``` json
{
  "conversa_id": "c_8f3a21",
  "intencao": "relato",
  "tipos_violencia": ["fisica", "psicologica"],
  "gravidade": {"maxima": 3, "final": 2}
}
```

## 14.5 Privacidade do resumo

-   O resumo **não contém texto da usuária**, nem nomes, nem
    identificadores pessoais. O `conversa_id` é aleatório e não está
    ligado a telefone, e-mail ou conta.
-   Mantê-lo apenas pelo tempo necessário para a finalidade
    (monitoramento, avaliação ou, se existir parceria, encaminhamento).
-   Se houver uso para pesquisa, agregar os dados (contagens e
    distribuições) em vez de manter conversas individuais.
-   Se houver encaminhamento a um serviço humano, **só enviar o resumo
    com consentimento explícito** da usuária.
-   Cuidado com a **reidentificação**: combinações raras de campos (por
    exemplo, tipo + fatores de risco + data) podem identificar alguém
    em bases pequenas.

------------------------------------------------------------------------

# 15. Capacidade de treinar e rodar a arquitetura

Esta seção avalia se a arquitetura proposta é viável em uma máquina
pessoal, usando o Google Colab apenas para treinar os classificadores.

> **Nota:** os valores de memória abaixo vêm da conta de parâmetros ×
> bytes por parâmetro. Os valores de velocidade são **estimativas**, não
> medições. Antes de citá-los no trabalho, convém medir.

## 15.1 Máquina de referência

  Item        Especificação
  ----------- ---------------------------------------------
  Chip        Apple M4 Max
  CPU         14 núcleos (10 de desempenho e 4 de eficiência)
  GPU         32 núcleos
  Memória     36 GB unificada (compartilhada entre CPU e GPU)
  Disco       ~730 GB livres
  Python      3.12 (PyTorch ainda não instalado)

## 15.2 Os três classificadores são a parte leve

  Item                                           Estimativa
  ---------------------------------------------- ----------------------------
  BERTimbau base (~110M parâmetros)              ~0,45 GB cada, em fp32
  Três modelos base carregados                   ~1,3 GB no total
  Três modelos large (~335M parâmetros)          ~4 GB no total
  Latência por mensagem (textos curtos, base)    dezenas de milissegundos

Uma conversa gera uma mensagem por vez, então três inferências em
paralelo são imperceptíveis para a usuária. Se for necessário reduzir
ainda mais, é possível exportar para ONNX ou quantizar em int8, mas isso
não é necessário para um protótipo.

## 15.3 O LLM é a parte pesada

  Componente                                       Memória aproximada
  ------------------------------------------------ --------------------
  3 classificadores BERTimbau base                 ~1,3 GB
  Embeddings do RAG (multilíngue, ~280M)           ~1 GB
  Modelo de NLI para verificar fundamentação       ~1 GB
  LLM de 7--8B, quantizado em 4 bits               ~5 GB
  LLM de ~14B, quantizado em 4 bits                ~9 GB
  Sistema operacional e margem                     ~6--8 GB

O conjunto completo fica em ~10 a 20 GB dos 36 GB disponíveis, mesmo com
um LLM de 14B. Um LLM de 7--8B quantizado costuma gerar na casa de
dezenas de tokens por segundo em Apple Silicon (por exemplo, via
Ollama, llama.cpp ou MLX). Como as respostas do chatbot são curtas, isso
representa alguns segundos por resposta.

O risco principal não é de recursos, mas de **qualidade**: modelos
menores seguem o prompt restritivo pior e alucinam mais, o que reforça a
importância das camadas de verificação da seção 5.

## 15.4 Fluxo de treino e execução

``` text
Dataset (Drive) ──► Treino no Colab (GPU gratuita)
                          │
                          ▼
              Salvar pesos + tokenizer
              (Drive ou Hugging Face)
                          │
                          ▼
              Baixar para a máquina local
                          │
                          ▼
     FastAPI carrega os 3 modelos uma vez na inicialização
                          │
                          ▼
              Chatbot chama os modelos a cada mensagem
```

-   **Treino no Colab:** fine-tuning do BERTimbau base com alguns
    milhares de exemplos leva minutos. As sessões gratuitas expiram,
    então é preciso salvar checkpoints no Drive.
-   **Treino local (alternativa):** a máquina de referência também
    consegue fazer o fine-tuning usando a GPU via backend MPS do
    PyTorch, em minutos a dezenas de minutos. O MPS tem algumas
    limitações de operações e de precisão mista, então vale testar
    antes de depender dele.
-   **Execução:** os modelos são carregados uma única vez e mantidos na
    memória, e não recarregados a cada mensagem.

## 15.5 Limites desta configuração

-   **Máquina de desenvolvimento, não servidor.** Serve para protótipo,
    demonstração e avaliação. Disponibilidade 24h ou muitos usuários
    simultâneos exigiriam um servidor. Usuárias reais em risco só
    deveriam usar o sistema com respaldo institucional (ver seção 11).
-   **Concorrência:** poucas conversas simultâneas funcionam bem; a GPU
    é compartilhada entre classificadores e LLM.
-   **Privacidade:** executar tudo localmente é uma vantagem, pois as
    mensagens não saem da máquina para APIs externas.
-   **Dependências:** é preciso instalar PyTorch, Transformers e o
    servidor do LLM, e validar a compatibilidade com Apple Silicon.

## 15.6 Conclusão sobre a capacidade

Treinar os classificadores no Colab e depois apenas chamá-los durante as
conversas **não é pesado**. O custo computacional está no LLM e nos
componentes de verificação, e mesmo assim cabe com folga na máquina de
referência. Os gargalos reais do projeto continuam sendo **dados,
anotação e avaliação**, não hardware.

Medições a fazer na implementação, para substituir as estimativas desta
seção:

-   latência por mensagem de cada classificador (CPU e MPS);
-   memória total com todos os componentes carregados;
-   tempo de resposta de ponta a ponta (classificação + RAG + geração +
    verificação);
-   tokens por segundo do LLM escolhido.
