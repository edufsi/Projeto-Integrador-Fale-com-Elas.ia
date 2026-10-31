# Notas.ia — Planejamento do Agente Conversacional

> Status: **rascunho v0.1 para discussão**. Interface (app de notas camuflado) fica fora deste documento; aqui só entram os *ganchos* que o agente exige dela.
> Base: Desafio 42 do CPSI/MPRS ("Fale com Elas.ia").

---

## 1. Requisitos do desafio que o agente precisa cumprir

| # | Requisito do desafio | Onde é tratado neste plano |
|---|---|---|
| R1 | Acolhimento empático, 24/7, tom não revitimizante | §5 (persona), §9 |
| R2 | Detecção de intenção: dúvida, relato de violência, emergência, orientação geral | §4.1 |
| R3 | Classificação de risco em tempo real com **Violentômetro** + **FONAR** | §6 |
| R4 | Identificação de padrões de violência (dimensões do **IAVP**) | §6.4 |
| R5 | Escalonamento de emergência (links diretos p/ 180 e 153) | §4.2 |
| R6 | Encaminhamento por geolocalização (CRAS, CREAS, DEAMs, Justiça) | §8 |
| R7 | Tradução de linguagem jurídica para linguagem cidadã | §7 |
| R8 | Texto e áudio (STT com WER ≤ 10%) | §10 |
| R9 | Taxa de alucinação (HAM) ≤ 10% | §7, §9, §11 |
| R10 | Privacidade: limpeza imediata de sessão, saída rápida | §12 |
| R11 | API-first, Docker/OCI, RBAC, Entra ID, TLS ≥ 1.2, SBOM, trilha de auditoria/WORM | §3, §13 |

> Observação: o desafio cita **IAVP** além de FONAR e Violentômetro. Você não listou o IAVP, mas ele é requisito da MVP; proponho incluir (ver §6.4). **A confirmar com você.**

---

## 2. Princípios de projeto (o que guia todas as decisões)

1. **O LLM conversa; o código decide.** Pontuação de risco, gatilhos de emergência e escolha de encaminhamento são **determinísticos e auditáveis**, nunca "opinião" do modelo.
2. **Nenhuma afirmação jurídica ou de procedimento sem fonte curada.** Se não há fonte recuperada, o agente diz que não sabe e encaminha (abstenção é um resultado válido).
3. **Segurança da usuária antes de completude do questionário.** Se há risco iminente, interrompe a entrevista e vai para o protocolo de emergência.
4. **O agente não é advogada, psicóloga nem polícia.** Ele informa, acolhe, estratifica e encaminha. Nunca promete resultado ("você vai ganhar a medida protetiva").
5. **Conteúdo sensível validado por humanos especialistas** (serviço social, psicologia, assessoria jurídica do MP/Defensoria) antes de ir para produção.
6. **Mínimo de dados, mínimo de tempo.** Coletar só o necessário; sessão persistida só pelo prazo necessário, com consentimento informado e opção de não guardar.
7. **Ela controla o ritmo.** Pode pular perguntas, parar, retomar. Nunca insistir.

---

## 3. Visão geral da arquitetura

```
 Usuária (app de notas / web chat / WhatsApp / áudio)
            │  HTTPS (TLS ≥ 1.2)
            ▼
 ┌────────────────────────────────────────────────────────┐
 │ API Gateway (REST) — auth, rate limit, RBAC (Entra ID) │
 └───────────────┬────────────────────────────────────────┘
                 ▼
 ┌────────────────────────────────────────────────────────┐
 │ ORQUESTRADOR DE CONVERSA (máquina de estados)          │
 │  1. Pré-filtro de segurança (regras + classificador)   │──► EMERGÊNCIA ► Protocolo §4.2
 │  2. Detector de intenção                               │
 │  3. Roteador de fluxo                                  │
 └───┬──────────────┬───────────────┬─────────────┬───────┘
     ▼              ▼               ▼             ▼
 Fluxo de       Fluxo de        Fluxo de      Fluxo de
 TRIAGEM        DÚVIDA          RELATO        ORIENTAÇÃO
 (Violentômetro (RAG jurídico   (acolhimento  GERAL
 + FONAR + IAVP)+ citações)     + triagem)    (rede/serviços)
     │              │               │             │
     ▼              ▼               ▼             ▼
 ┌─────────────┐ ┌───────────┐ ┌───────────┐ ┌────────────┐
 │ Motor de    │ │ Base de   │ │ Extrator  │ │ Serviço de │
 │ Risco       │ │ Conhec.   │ │ de fatos  │ │ Geo/Rede   │
 │ (determinís-│ │ curada    │ │ (LLM →    │ │ (CRAS,     │
 │ tico)       │ │ (RAG)     │ │ JSON)     │ │ CREAS,DEAM)│
 └──────┬──────┘ └─────┬─────┘ └─────┬─────┘ └─────┬──────┘
        └──────────────┴──────┬──────┴─────────────┘
                              ▼
 ┌────────────────────────────────────────────────────────┐
 │ GERADOR DE RESPOSTA (LLM com prompt de persona)        │
 │  → Camada de GUARDRAILS de saída (verificação, §9)     │
 └───────────────┬────────────────────────────────────────┘
                 ▼
     Resposta à usuária  +  log de auditoria (sem PII, §12)
```

**Módulos-chave**

| Módulo | Responsabilidade | Tecnologia sugerida |
|---|---|---|
| Orquestrador | Estado da sessão, fluxo, timeouts, retomada | Máquina de estados (ex.: LangGraph ou implementação própria simples) |
| Pré-filtro de segurança | Detectar perigo iminente/autolesão em **toda** mensagem | Regras/lexicon + classificador leve, *antes* do LLM |
| Detector de intenção | 4 classes (R2) + "ambígua" | LLM com saída estruturada + fallback por regras |
| Motor de risco | Pontuar e estratificar | Código puro (Python), configuração em YAML versionado |
| Base de conhecimento (RAG) | Leis, direitos, procedimentos, serviços | Busca híbrida (BM25 + embeddings) sobre corpus curado |
| Serviço de rede/geo | Encontrar equipamentos por localização | Base própria de serviços + geocodificação |
| Gerador de resposta | Redação empática e clara | LLM com temperatura baixa, templates para trechos críticos |
| Guardrails | Verificar respostas antes de enviar | Verificador de citações + regras + juiz-LLM secundário |
| STT | Áudio → texto | Serviço com WER ≤ 10% em pt-BR, validado em dataset regional |
| Auditoria | Registro imutável (WORM) de decisões, sem conteúdo identificável | Armazenamento append-only |

---

## 4. Fluxos de conversa

### 4.1 Detecção de intenção (R2)

| Intenção | Exemplo | Fluxo |
|---|---|---|
| `emergencia` | "ele está aqui, vai me matar" | Protocolo §4.2 (prioridade absoluta) |
| `relato` | "ontem ele me empurrou de novo" | Acolhimento → triagem de risco |
| `duvida` | "o que é medida protetiva?" | RAG jurídico com citação |
| `orientacao_geral` | "onde tem ajuda perto de mim?" | Rede de apoio/geo |
| `ambigua` | "tô mal, não sei" | Pergunta aberta e acolhedora; nunca assumir |

Uma mesma sessão pode transitar entre intenções (ex.: dúvida → relato). A reclassificação ocorre a cada turno; **emergência sempre tem precedência**.

### 4.2 Protocolo de emergência (R5)

Gatilhos (regras + classificador, ajustados por especialistas): ameaça de morte em curso, agressor presente/próximo, arma mencionada, agressão física em andamento, estrangulamento recente, menção de filhos em perigo imediato, ideação suicida da usuária.

Ao disparar:
1. Interrompe qualquer questionário.
2. Resposta curta, calma, imperativa e sem jargão: o que fazer **agora**.
3. Exibe ações diretas: **Ligar 190** (Polícia Militar — emergência), **Ligar 180** (Central de Atendimento à Mulher) e o serviço **153** citado pelo desafio *(confirmar com o MPRS o que é o 153 no contexto do projeto antes de exibir ao público)*.
4. Se a usuária não puder falar: orientar a usar canais silenciosos/texto quando existirem no município *(validar disponibilidade real antes de citar qualquer canal)*.
5. Marca a sessão como risco `CRÍTICO` (independente da pontuação).
6. Só retoma a triagem se ela quiser.

Regra de ouro: **nunca** enviar a mulher de volta a "conversar com o agressor", "esperar acalmar" ou qualquer conselho de mediação.

---

## 5. Persona e tom (R1)

- Acolhedor, calmo, sem julgamento, sem infantilizar. Frases curtas. Português claro (nível de leitura acessível).
- **Acredita** no relato ("Sinto muito que você esteja passando por isso. O que você descreve não é aceitável.") — sem interrogar nem duvidar.
- **Nunca** culpar ("por que você não saiu?"), nunca minimizar ("é só uma briga").
- Não dizer "você precisa denunciar"; explicar opções e deixar a decisão com ela.
- Perspectiva de gênero e **interseccionalidade**: perguntas e exemplos que não presumem perfil (mulheres negras, indígenas, quilombolas, do campo, LBT, com deficiência, migrantes, idosas, sem renda própria, sem acesso a telefone próprio). Linguagem sem pressupor relação heterossexual ou agressor "marido".
- Transparência: deixa claro que é uma IA, que não substitui atendimento profissional e que pode encaminhar a pessoas reais.
- Toda pergunta de triagem vem precedida de **licença**: "Posso te fazer algumas perguntas para entender melhor como te ajudar? Você pode pular qualquer uma."

---

## 6. Avaliação de risco (R3, R4)

### 6.1 Instrumentos e papéis

| Instrumento | Papel no agente | Observação |
|---|---|---|
| **Violentômetro** | Régua de *escalada* (comportamentos do cotidiano → gravidade). Fornece o **nível** apresentado à usuária de forma didática | Origem mexicana; existe adaptação para o contexto brasileiro. **Precisamos definir com especialistas qual versão usar.** |
| **FONAR** (Formulário Nacional de Avaliação de Risco — CNJ/CNMP, Lei 14.149/2021) | Fatores de **risco de letalidade/reincidência**; alimenta a decisão de urgência e o encaminhamento | Formulário é oficial: perguntas e redação devem seguir o texto oficial. |
| **IAVP** (citado no desafio) | Classificação por **dimensões** da violência psicológica | Obter documentação oficial com o MPRS. |

> ⚠️ **Não vamos inventar itens, pesos ou faixas.** O banco de perguntas será transcrito das fontes oficiais, e os **pesos/pontos de corte serão definidos e assinados por especialistas** (equipe do MPRS/rede de proteção). Este documento só define a *estrutura*.

### 6.2 Do formulário para a conversa

O FONAR é um formulário; o agente o transforma em **conversa**:

1. **Banco de itens** (arquivo versionado) — cada item tem: `id`, fonte (FONAR/Violentômetro/IAVP), texto oficial, reformulação empática aprovada, tipo de resposta (sim/não/não sei/não quero responder), peso, dimensão, e flag de "gatilho crítico".
2. **Extração passiva**: se ela já relatou algo espontaneamente, o LLM extrai o fato para JSON estruturado com **trecho de evidência**; o item é marcado como *"inferido — confirmar"* e **confirmado por pergunta direta** antes de pontuar (evita pontuar por interpretação do modelo).
3. **Perguntas adaptativas**: ordem por relevância; pula itens já respondidos; perguntas mais sensíveis ficam depois de criar vínculo; para se houver gatilho crítico.
4. **Respostas possíveis**: `sim`, `não`, `não sei`, `prefiro não responder`. "Não sei / prefiro não responder" **não** contam como "não" — reduzem a *confiança* do resultado.
5. Máx. de perguntas por turno: **1** (opcionalmente 2 curtas). Progresso pode ser retomado depois.

### 6.3 Motor de pontuação (determinístico)

Entrada: respostas confirmadas. Saída:

```json
{
  "score": 0-100,
  "nivel": "BAIXO | MODERADO | ALTO | CRITICO",
  "confianca": "alta | media | baixa",
  "fatores_criticos": ["..."],
  "dimensoes": {"psicologica": 0.0, "fisica": 0.0, "sexual": 0.0, "patrimonial": 0.0, "moral": 0.0},
  "itens_sem_resposta": 4,
  "versao_regras": "2026-xx-xx"
}
```

Regras estruturais (valores a definir com especialistas):
- **Piso por gatilho crítico**: certos fatores (ex.: ameaça de morte, uso/acesso a arma, estrangulamento, escalada recente) elevam o nível mínimo *independente da soma*. A soma nunca "dilui" um sinal crítico.
- **Soma ponderada** dos demais itens → faixas.
- **Confiança baixa** (muitos "não sei") → o resultado é apresentado como *estimativa*, e o encaminhamento é **conservador** (tratar como o nível imediatamente superior no encaminhamento).
- **Reavaliação**: novas informações na conversa recalculam; histórico de scores da sessão é preservado para detectar escalada.
- Regras em arquivo **versionado**; cada resposta guarda `versao_regras` para auditoria e reprodutibilidade.

Apresentação à usuária: **nunca** um número frio. Ex.: "Pelo que você me contou, sua situação tem sinais de **risco alto**. Isso significa que vale a pena buscar ajuda o quanto antes. Posso te mostrar como?" + Violentômetro visual como ferramenta educativa (as situações que ela vive em degraus de gravidade).

### 6.4 Padrões de violência (IAVP e tipos da Lei Maria da Penha)

Além da pontuação, o motor devolve as **dimensões identificadas** (física, psicológica, sexual, patrimonial, moral — Art. 7º da Lei 11.340/2006 — e as dimensões do IAVP). Serve para (a) explicar a ela "isso também é violência", (b) orientar a informação jurídica pertinente, (c) alimentar o encaminhamento.

### 6.5 Validação do motor de risco

- Casos de teste "gabarito" elaborados por especialistas (dezenas a centenas de vinhetas com nível esperado).
- Métrica prioritária: **sensibilidade para ALTO/CRÍTICO** (não subestimar risco). Aceita-se mais falsos positivos que falsos negativos, com monitoramento para evitar alarme excessivo.
- Testes de regressão a cada mudança de regra.
- O escore é **apoio à decisão**, nunca sentença; isso deve constar em documentação e nos termos.

---

## 7. Conhecimento jurídico e de direitos (R7, R9)

### 7.1 Estratégia: RAG sobre corpus curado, não conhecimento "de memória" do modelo

O LLM **não deve** responder sobre lei a partir do que "lembra". Toda resposta jurídica é gerada **somente** a partir de trechos recuperados de uma base curada, com citação.

**Corpus inicial (fontes primárias — texto oficial, com data de vigência):**

| Tema | Norma / fonte |
|---|---|
| Lei Maria da Penha | Lei 11.340/2006 (formas de violência, medidas protetivas de urgência, atendimento policial e judicial, rede de atendimento) |
| Alteração: MPU independe de boletim/processo | Lei 14.550/2023 |
| Descumprimento de medida protetiva é crime | Art. 24-A da Lei 11.340/2006 (Lei 13.641/2018) |
| Medida protetiva concedida por delegado/policial em certos casos | Lei 13.827/2019 |
| Feminicídio | Lei 13.104/2015 e legislação posterior sobre pena/regime *(verificar texto vigente)* |
| Violência psicológica como crime | Art. 147-B do Código Penal (Lei 14.188/2021) e programa "Sinal Vermelho" |
| FONAR | Lei 14.149/2021 |
| Perseguição (stalking) | Art. 147-A do Código Penal |
| Registro de medidas protetivas | Lei 14.310/2022 |
| Direitos gerais | CF/88 (art. 226 §8º), Convenção de Belém do Pará, resoluções CNJ/CNMP sobre o tema |
| Direitos sociais/trabalhistas ligados à violência | Ex.: afastamento do trabalho por violência doméstica (Art. 9º §2º, Lei Maria da Penha) |
| Redes e serviços | Cartilhas do MPRS, CNJ, Defensoria Pública, Secretaria da Mulher/SPM, Ligue 180 |

> ⚠️ A tabela acima é **ponto de partida de pesquisa**, escrito de memória para orientar o planejamento. **Cada item precisa ser conferido no texto oficial (planalto.gov.br etc.) e por jurista** antes de entrar no corpus. Leis mudam com frequência; o corpus terá **data de verificação** e responsável.

### 7.2 Pipeline de curadoria

1. Ingestão de textos oficiais (Planalto, CNJ, CNMP, MPRS, Defensoria) → normalização e *chunking* por artigo/inciso.
2. Metadados por chunk: norma, artigo, vigência, tema, fonte oficial (URL), data de verificação, revisor.
3. **Notas explicativas em linguagem simples** escritas/revisadas por profissional do direito ("o que isso significa para você") — vinculadas ao artigo de origem. O LLM pode usar essas notas *e* deve manter o vínculo com a fonte.
4. **Revisão periódica** (ex.: trimestral) e **alerta de mudança legislativa**.
5. Versionamento do corpus: cada resposta registra a versão da base usada.

### 7.3 Recuperação e resposta

- Busca híbrida (lexical + semântica) + reranking, filtrando por vigência.
- Resposta gerada contendo **citações** internas (ex.: "Lei 11.340/2006, art. 22") e um resumo simples.
- **Limiar de suficiência**: se a similaridade/cobertura for baixa, o agente **não responde o mérito** — diz que não tem certeza, explica o que sabe com segurança e encaminha (Defensoria Pública, DEAM, 180).
- Perguntas de **caso concreto** ("vou ganhar a guarda?", "posso perder meus filhos?") não são respondidas com previsões; o agente explica direitos gerais e encaminha a profissional.
- Cuidado com jurisdição: RS pode ter serviços/normas locais; priorizar fontes estaduais e municipais quando houver.

---

## 8. Encaminhamento e geolocalização (R6)

- Base própria de **equipamentos da rede** (DEAMs, delegacias, CRAS, CREAS, Defensoria, Juizados/Varas de Violência Doméstica, Casas-Abrigo, Patrulha Maria da Penha, serviços de saúde) com: endereço, coordenadas, telefone, horário, se aceita atendimento sem agendamento, data da última verificação.
- Localização **opcional**: aceita CEP, cidade/bairro digitados ou geolocalização do dispositivo com consentimento; não é armazenada além da sessão.
- Cuidado de segurança: **não** enviar endereços/lembretes que possam expor a usuária caso o agressor veja o aparelho. Rotas e listas são exibidas dentro do chat e somem no encerramento.
- Roteamento pelo nível de risco:

| Nível | Encaminhamento principal |
|---|---|
| CRÍTICO | Protocolo de emergência (190/180) + DEAM mais próxima + plano de segurança imediato |
| ALTO | DEAM / delegacia, orientação sobre medidas protetivas, Defensoria/Ministério Público, casa-abrigo se aplicável |
| MODERADO | CREAS/CRAS, orientação jurídica, canais de denúncia, acompanhamento |
| BAIXO | Informação, direitos, rede de apoio, Violentômetro educativo, convite para voltar |

- "Promotoria territorial": a atribuição de promotores por território é requisito do desafio; o serviço de geo deve expor uma API para o MPRS mapear município → unidade.
- Regras de **dados desatualizados**: se a última verificação do serviço tem mais de X dias, mostrar aviso e sempre oferecer o Ligue 180 como alternativa.

### 8.1 Plano de segurança

Módulo com conteúdo pré-aprovado (não gerado livremente): itens como reunir documentos, rota de saída, pessoa de confiança, o que levar. **Conteúdo redigido por especialistas**; o agente apenas seleciona e personaliza a ordem/linguagem.

---

## 9. Anti-alucinação e segurança das respostas (R9)

A meta contratual é **HAM ≤ 10%**; nosso objetivo interno deve ser bem menor para conteúdo jurídico/de segurança. Estratégia em camadas:

| Camada | Mecanismo |
|---|---|
| 1. Fundamentação | RAG obrigatório para fatos jurídicos/serviços; nada de fatos "de memória" |
| 2. Templates aprovados | Trechos críticos (emergência, plano de segurança, avisos legais, números de telefone) vêm de **texto fixo revisado**, não de geração livre |
| 3. Números e contatos | Telefones, endereços e links só de **tabela verificada**; qualquer número que o LLM escrever fora da tabela é bloqueado |
| 4. Saída estruturada | O LLM devolve `{resposta, citacoes[], confianca}`; sem citações onde exigido → resposta rejeitada |
| 5. Verificador de fidelidade | Segundo passo (juiz-LLM + checagens por regra) confere se cada afirmação está apoiada nos trechos recuperados; falhou → regenera ou abstém |
| 6. Abstenção | "Não tenho certeza. O melhor é falar com [serviço]." é resposta legítima e preferida a chutar |
| 7. Proibições duras | Sem diagnóstico, sem previsão de resultado judicial, sem aconselhar confronto/mediação com agressor, sem aconselhar ação que aumente perigo, sem afirmar que "vai dar certo" |
| 8. Temperatura baixa e modelo fixado | Versão do modelo/prompt travada e registrada |
| 9. Revisão humana contínua | Amostragem de conversas (anonimizadas) revisada por especialistas; casos com "polegar para baixo" vão para fila |

**Lista de "nunca faça" do agente (testável)**
- Nunca dizer que a violência é culpa dela.
- Nunca sugerir permanecer/voltar ao agressor, mediação ou "dar mais uma chance".
- Nunca prometer proteção, resultado judicial ou sigilo absoluto.
- Nunca inventar artigo, prazo, endereço, telefone ou serviço.
- Nunca dar orientação jurídica de caso concreto como se fosse advogado.
- Nunca minimizar risco por falta de marcas físicas.
- Nunca pedir que ela confronte o agressor ou produza prova colocando-se em risco.

---

## 10. Entrada de áudio e canais (R8)

- Áudio → **STT** → mesmo pipeline de texto. Meta: **WER ≤ 10%** medido em amostra de pt-BR com sotaques e ruído realistas do RS e de outros perfis (mulheres rurais, idosas, etc.).
- Mostrar à usuária a transcrição (opcional) para confirmar, sobretudo em trechos críticos.
- Baixa confiança de STT em palavras de risco → o agente **pergunta de volta** em vez de assumir.
- Não guardar o áudio após a transcrição (ver §12).
- Canais: o núcleo é **API-first** e independente do canal; adaptadores para app/web chat agora e WhatsApp depois. (WhatsApp exige cuidado extra: histórico fica no aparelho. Tratar na fase de interface.)

---

## 11. Avaliação e métricas

| Métrica | Meta inicial | Como medir |
|---|---|---|
| Taxa de alucinação (HAM) | ≤ 10% (interno: ≤ 3% em jurídico) | Conjunto de perguntas com gabarito + revisão humana |
| Fidelidade às fontes (groundedness) | ≥ 95% das afirmações jurídicas apoiadas | Verificador + auditoria por amostragem |
| Recall de emergência | ~100% nos casos de teste críticos | Suíte de vinhetas de emergência |
| Sensibilidade risco ALTO/CRÍTICO | Alta; definir com especialistas | Vinhetas gabaritadas |
| Concordância da intenção | ≥ 90% | Conjunto rotulado |
| WER (STT) | ≤ 10% | Dataset regional |
| Tom (não revitimização) | Aprovação de especialistas | Rubrica de revisão + red-team |
| Latência | Resposta em poucos segundos | Telemetria |
| Taxa de abstenção adequada | Monitorar | Casos "fora da base" |

**Red-team obrigatório**: tentativas de fazer o agente dar conselho perigoso, revelar dados, ser manipulado por *prompt injection* ("ignore as instruções…"), ou testar o agente como se fosse o agressor tentando descobrir se ela usou o app.

---

## 12. Privacidade, sigilo e auditoria (R10, R11)

Contexto especial: **o maior risco de privacidade é o agressor ter acesso ao aparelho.** O agente precisa de ganchos com a interface:

- **Sessão anônima persistida por cookie**: sem conta; a conversa continua na próxima visita, por prazo limitado. Ela pode escolher "não lembrar neste aparelho". Detalhes em [E1-plano-backend-api.md](E1-plano-backend-api.md) §3.
- **Saída rápida e apagar conversa**: a saída rápida esconde o chat na hora; o toque longo nela, ou "apagar conversa", apaga a sessão no servidor e expira o cookie.
- **Sem PII desnecessária**: sem nome, CPF ou endereço exato; se ela informar, o pré-processador pode *mascarar* antes de logar.
- **Logs de auditoria (WORM)** guardam *metadados de decisão* (nível de risco, versão de regras, versão do corpus, intenção, tempos), **não** o conteúdo da conversa.
- **LGPD**: dados sensíveis (art. 11); base legal e finalidade documentadas; RIPD (relatório de impacto); retenção mínima; direito de eliminação; definir controlador (MPRS) e operador.
- Consentimento claro e curto no início (o que é guardado, o que não é, limites do sigilo).
- Se usar provedor de LLM em nuvem: contrato que **proíbe treino com os dados** e retenção zero; região/residência de dados; avaliar modelo hospedado em ambiente controlado.
- Compartilhamento de dados com a rede (ex.: repassar relato ao MP/DEAM): **só com consentimento explícito e específico dela**, salvo hipóteses legais a definir com jurídico (ex.: risco iminente de vida — **decisão jurídica a ser tomada com o MPRS**, não do agente).
- Segurança técnica: TLS ≥ 1.2, criptografia em repouso, Entra ID + RBAC para painéis administrativos, segredo em cofre, SBOM (SPDX/CycloneDX), containers Docker/OCI, escalabilidade horizontal (agente **stateless** com estado de sessão em store com prazo igual ao do cookie, cifrado em repouso).

---

## 13. Stack sugerida (a discutir)

| Camada | Opção principal | Alternativa |
|---|---|---|
| Linguagem/API | Python + FastAPI (REST) | Node/TypeScript |
| Orquestração | Máquina de estados própria ou LangGraph | — |
| LLM | Modelo Claude via API (saída estruturada, tool use) com contrato de retenção zero | Modelo aberto hospedado (soberania de dados) |
| RAG | Postgres + pgvector + BM25 (ou OpenSearch) | Qdrant |
| Motor de risco | Python puro + YAML versionado + testes | — |
| Sessão | Cookie `HttpOnly` + Redis com persistência (prazo do cookie) | Postgres |
| STT | Serviço de nuvem com validação de WER | Whisper hospedado |
| Geo | Base própria (PostGIS) + geocodificação | — |
| Observabilidade | OpenTelemetry sem conteúdo sensível | — |
| Infra | Docker/OCI, Kubernetes (escala horizontal), Entra ID | — |

---

## 14. API (esboço, API-first)

```
POST /v1/session                     → cria sessão anônima e define o cookie
GET  /v1/session                     → retoma a conversa (se o cookie for válido)
POST /v1/session/messages            → texto ou áudio; retorna resposta + metadados (nível de risco, ações sugeridas)
GET  /v1/session/risk                → estado atual do risco (para a interface exibir o Violentômetro)
GET  /v1/network?lat&lon|cep         → serviços próximos
DELETE /v1/session                   → apagar conversa: apaga tudo e expira o cookie
GET  /v1/health, /v1/version         → operação (inclui versão de regras/corpus/modelo)
```

Resposta padrão do agente inclui campos estruturados (`intent`, `risk`, `actions[]`, `citations[]`, `abstained`) para que qualquer interface renderize botões de ação (ligar 180/190, abrir DEAM, sair).

---

## 15. Roadmap sugerido

| Fase | Entregas |
|---|---|
| **0 — Fundamentos** | Reunir fontes oficiais (FONAR, Violentômetro, IAVP); definir versão do Violentômetro; convidar especialistas revisores; definir lista de "nunca faça" |
| **1 — Núcleo determinístico** | Banco de itens, motor de risco, protocolo de emergência, suíte de vinhetas |
| **2 — Conversa** | Orquestrador, intenção, persona, extração de fatos, templates críticos |
| **3 — Conhecimento** | Corpus jurídico curado, RAG com citações, abstenção, verificador de fidelidade |
| **4 — Rede e geo** | Base de serviços, encaminhamento por risco, plano de segurança |
| **5 — Áudio e canais** | STT, adaptadores, testes de WER |
| **6 — Endurecimento** | Red-team, LGPD/RIPD, SBOM, auditoria WORM, testes de carga, piloto com equipe do MPRS |

---

## 16. Riscos principais e mitigação

| Risco | Mitigação |
|---|---|
| Orientação errada gera dano real | Camadas do §9, revisão humana, abstenção, templates fixos |
| Subestimar risco (falso negativo) | Pisos por gatilho crítico, encaminhamento conservador, foco em sensibilidade |
| Agressor descobre uso do app | Ganchos de privacidade §12; camuflagem e limpeza no lado da interface |
| Conteúdo jurídico desatualizado | Versionamento, revisão periódica, alerta de mudança |
| Modelo manipulado (prompt injection) | Regras no código, não no prompt; saída validada; red-team |
| Dependência de fornecedor de LLM | Camada de abstração; testes de regressão entre modelos |
| Tom inadequado / revitimização | Rubrica de tom, revisão por psicólogas/assistentes sociais |
| Serviços de rede desatualizados | Data de verificação, aviso, fallback ao 180 |

---

## 17. Pontos em aberto (para decidirmos juntos)

1. **Incluir o IAVP** como terceiro instrumento? (é requisito do desafio)
2. Qual **versão do Violentômetro** usar (adaptação brasileira/RS)? Temos acesso aos materiais oficiais?
3. Quem serão os **especialistas revisores** (pesos de risco, textos empáticos, plano de segurança, revisão jurídica)? O MPRS oferece mentoria?
4. **LLM em nuvem** (Claude via API, com retenção zero) ou modelo hospedado por nós? Impacta LGPD e a pontuação do desafio.
5. Regras de **compartilhamento com a rede** em risco iminente: o agente pode acionar alguém por conta própria ou só orientar? (decisão jurídica)
6. O que exatamente é o **153** citado no desafio?
7. Escopo geográfico da MVP: **RS inteiro** ou município-piloto (para a base de serviços ser confiável)?
8. ~~Persistência~~ **Decidido:** sessão persistida por cookie, por prazo limitado (ver [E1-plano-backend-api.md](E1-plano-backend-api.md) §3). Falta definir o prazo.
9. Idioma: só pt-BR na MVP? (Libras/outros idiomas ficam para depois?)

---

## 18. Fontes a consultar (próximos passos de pesquisa)

- Página do desafio: https://cpsi.lab.mprs.mp.br/challenges/42/
- Texto oficial do FONAR (CNJ/CNMP) e Lei 14.149/2021
- Lei 11.340/2006 e alterações (Planalto)
- Materiais do Violentômetro e sua adaptação brasileira
- Documentação do IAVP
- Cartilhas do MPRS, Defensoria Pública do RS, CNJ, Ligue 180
- Diretrizes da LGPD/ANPD para dados sensíveis
