# Notas.ia — Visão geral da aplicação

> Um tour pelos módulos do Notas.ia, sem entrar em detalhes de implementação. Para os detalhes, cada seção aponta para o plano da etapa correspondente. Índice geral: [plano.md](plano.md).

---

## O que é o Notas.ia, em uma frase

Um **app de notas comum** que esconde um **assistente conversacional** capaz de acolher mulheres em situação de violência, avaliar o risco que elas correm, explicar seus direitos com base na lei e indicar onde buscar ajuda, **sem inventar nada**.

A ideia vem de um desafio real do Ministério Público do RS ([CPSI, desafio 42](https://cpsi.lab.mprs.mp.br/challenges/42/)).

---

## O mapa da aplicação

```
                         ┌──────────────────────────────┐
   Usuária  ───────────► │  E7  App de notas camuflado  │  (a única coisa que ela vê)
                         └──────────────┬───────────────┘
                                        │ HTTPS + cookie
                         ┌──────────────▼───────────────┐
           áudio? ─────► │  E6  Voz (fala → texto)      │
                         └──────────────┬───────────────┘
                         ┌──────────────▼───────────────┐
                         │  E1  API e sessão            │  (a porta de entrada)
                         └──────────────┬───────────────┘
                         ┌──────────────▼───────────────┐
                         │  E2  Conversa                │  (o maestro)
                         └───┬──────────┬───────────┬───┘
                             │          │           │
                 ┌───────────▼──┐ ┌─────▼──────┐ ┌──▼───────────┐
                 │ E3  Risco    │ │ E4  Leis   │ │ E5  Rede de  │   (os especialistas)
                 │              │ │   (RAG)    │ │    apoio     │
                 └──────────────┘ └────────────┘ └──────────────┘

   Por baixo de tudo:  E8 Privacidade · E9 Avaliação · E10 Infraestrutura
   Antes de tudo:      E0 Fundamentos (fontes oficiais, especialistas, decisões)
```

Uma boa forma de pensar: o **E2 é o maestro**. Ele não sabe tocar nenhum instrumento, mas sabe quem chamar e quando. **E3, E4 e E5 são os especialistas**, cada um muito bom em uma coisa só. O **E7 é o palco**, a única parte que a usuária enxerga. **E8, E9 e E10 são a equipe de bastidores**, que garante que o show seja seguro, testado e não caia.

---

## A regra de ouro do projeto

> **O LLM conversa; o código decide.**

O modelo de linguagem é ótimo para entender o que uma pessoa escreveu e para responder com empatia. Mas ele pode errar com muita confiança. Por isso, tudo o que pode machucar alguém se errar fica em **código comum, testável e previsível**:
- se é uma emergência;
- qual o nível de risco;
- qual telefone ou endereço mostrar;
- se uma afirmação sobre a lei tem fonte.

Se o LLM errar, no pior caso a resposta fica menos elegante. Nunca perigosa.

---

## E0 · Fundamentos — a fase antes do código

📄 [E0-plano-fundamentos.md](E0-plano-fundamentos.md)

Antes de programar, é preciso ter **conteúdo confiável**: os formulários oficiais de avaliação de risco (FONAR, Violentômetro, IAVP), o texto oficial das leis e pessoas especialistas (psicologia, serviço social, direito) para validar o que o sistema vai dizer.

É também onde ficam registradas as grandes decisões do projeto (por exemplo, "vamos usar LLM em nuvem ou hospedado?"), cada uma num documento curto chamado ADR.

**Por que importa:** num tema sensível, um sistema bem programado com conteúdo errado continua sendo um sistema perigoso.

---

## E1 · API e sessão — a porta de entrada

📄 [E1-plano-backend-api.md](E1-plano-backend-api.md) · *Python, FastAPI, Redis, OpenAPI*

Toda mensagem passa por aqui. A API recebe o que a usuária escreveu, entrega para o módulo de conversa e devolve a resposta.

Algumas características:
- **Sem login.** A usuária não cria conta. Um **cookie** anônimo liga o navegador dela a uma conversa guardada no servidor, então ela pode fechar o app e continuar outro dia.
- **Apagável em um clique.** Uma única chamada (`DELETE /v1/session`) apaga a conversa no servidor e invalida o cookie.
- **Independente de canal.** Hoje o cliente é um app web; amanhã pode ser WhatsApp, sem mudar o resto.
- **Rastreável.** Toda resposta carrega as versões de tudo o que a produziu (regras, base de leis, modelo, prompt). Se algo der errado, dá para reproduzir.

---

## E2 · Conversa — o maestro

📄 [E2-plano-conversa.md](E2-plano-conversa.md) · *LLM (ex.: Claude) com saída estruturada, máquina de estados*

É o módulo mais central. Para cada mensagem, ele segue um roteiro fixo:

1. **Pré-filtro de segurança:** antes de tudo, procura sinais de perigo imediato ("ele está aqui", "tem uma arma"). Se encontrar, pula direto para o **protocolo de emergência**, com resposta pronta e botões para ligar 190 e 180. Esse passo funciona mesmo se o LLM estiver fora do ar.
2. **Detector de intenção:** descobre o que ela quer: contar o que aconteceu, tirar uma dúvida, achar um serviço ou ainda não sabe.
3. **Máquina de estados:** sabe em que ponto da conversa ela está (acolhimento, perguntas de triagem, resultado, encaminhamento) e impede o LLM de "pular etapas".
4. **Extrator de fatos:** lê o relato livre e identifica fatos relevantes ("ele ameaçou me matar"). Mas só pontua depois de **confirmar com ela**, para não depender de uma interpretação do modelo.
5. **Ferramentas:** chama os especialistas: E3 para risco, E4 para leis, E5 para serviços.
6. **Gerador de resposta:** o LLM escreve a resposta com tom acolhedor. Trechos críticos (emergência, telefones, plano de segurança) vêm de **textos prontos e revisados**, não são gerados.
7. **Guardrails:** um "fiscal" confere a resposta antes de enviar. Telefone que não está na lista oficial? Bloqueado. Afirmação jurídica sem fonte? Bloqueada. Culpou a vítima? Bloqueado. Se reprovar, tenta de novo ou responde com segurança: "não tenho certeza, procure tal serviço".

---

## E3 · Motor de risco — o avaliador

📄 [E3-plano-risco.md](E3-plano-risco.md) · *Python puro + regras em YAML versionado*

Transforma as respostas da usuária em um **nível de risco**: baixo, moderado, alto ou crítico.

- As perguntas vêm de instrumentos oficiais (**FONAR**, **Violentômetro**, **IAVP**), reescritas em tom de conversa.
- É **determinístico**: mesmas respostas, mesmo resultado, sempre. Nenhum LLM participa da conta.
- Alguns fatores são **gatilhos críticos** (ameaça de morte, arma, estrangulamento): sozinhos, já elevam o nível mínimo, independentemente do resto.
- "Não sei" não conta como "não"; só deixa o resultado menos confiável. Se a confiança é baixa, o encaminhamento é mais cauteloso.
- O resultado nunca aparece como um número frio. Aparece como "sua situação tem sinais de risco alto", acompanhado do Violentômetro visual.

**Pense nele como** uma função pura `avaliar(respostas) → nível`, com testes que cobrem dezenas de casos validados por especialistas.

---

## E4 · Base de leis (RAG) — o consultor jurídico

📄 [E4-plano-rag.md](E4-plano-rag.md) · *RAG, embeddings (BGE-M3, multilingual-e5, BERTimbau), BM25, cross-encoder, pgvector* · **é também o trabalho da disciplina de PLN**

Responde dúvidas como "ele pegar meu salário é crime?" **sem responder de memória**. Funciona em dois passos:

1. **Busca:** procura, numa base com o texto oficial das leis dividido em pedaços (artigos, incisos), os trechos mais relevantes para a pergunta.
2. **Geração:** o LLM escreve a resposta usando **apenas** esses trechos, e cita de onde tirou ("Lei 11.340/2006, art. 7º, IV").

Se a busca não encontra nada bom o suficiente, o sistema **admite que não sabe** e encaminha. Abster-se é um resultado válido.

O desafio interessante (e o tema do trabalho de PLN) é que a usuária fala "ele me tranca em casa", e a lei fala "limitação do direito de ir e vir". O trabalho compara várias técnicas de busca para ver qual liga melhor essas duas linguagens, medindo com um dataset de perguntas anotadas.

---

## E5 · Rede de apoio — o guia local

📄 [E5-plano-rede-geo.md](E5-plano-rede-geo.md) · *PostgreSQL + PostGIS, geocodificação*

Responde "onde eu procuro ajuda?". Mantém uma base de serviços reais (delegacias da mulher, CRAS, CREAS, Defensoria, casas-abrigo...) com endereço, telefone, horário e **data da última verificação**.

- A localização é **opcional**: CEP, bairro ou GPS, se ela permitir.
- O tipo de serviço sugerido depende do nível de risco do E3.
- Dado antigo é sinalizado, e o Ligue 180 é sempre oferecido como alternativa. Mandar alguém em perigo para um endereço que fechou é um erro grave.

---

## E6 · Voz — o ouvido

📄 [E6-plano-voz.md](E6-plano-voz.md) · *Speech-to-Text (serviço em nuvem ou Whisper)*

Permite que ela **mande áudio** em vez de digitar. O áudio vira texto e segue o mesmo caminho de uma mensagem escrita.

- Meta do desafio: no máximo **10% de erro de transcrição** (WER), medido com sotaques e situações reais (voz baixa, ruído).
- Se a transcrição de uma palavra importante for duvidosa ("arma"? "alma"?), o agente **pergunta** em vez de assumir.
- O áudio é apagado assim que é transcrito.

---

## E7 · Interface — o disfarce

📄 [E7-plano-interface.md](E7-plano-interface.md) · *PWA, TypeScript, React (ou Svelte), Vite*

À primeira vista, é **só um app de notas**: dá para criar listas de compras, receitas, lembretes. Nome, ícone e endereço do site são neutros.

- O chat abre por um **gatilho secreto** (uma sequência de toques, um PIN numa nota específica...), invisível para quem não sabe.
- **Saída rápida:** um toque esconde o chat e volta às notas na hora; um toque longo esconde **e** apaga a conversa.
- Sem notificações, sem histórico revelador no navegador.
- Mostra o Violentômetro visual e botões de ação rápida (ligar 180/190, ver serviço no mapa).

**Por que tanto cuidado?** O maior risco do projeto é o agressor pegar o celular e descobrir que ela está pedindo ajuda.

---

## E8 · Privacidade e segurança — o guarda-costas

📄 [E8-plano-privacidade-seguranca.md](E8-plano-privacidade-seguranca.md) · *LGPD, Entra ID, RBAC, criptografia, SBOM*

Não é um módulo que roda sozinho; é um conjunto de regras que **atravessa todos os outros**:
- Guardar o mínimo de dados pelo menor tempo possível, conforme a **LGPD** (que trata esses dados como sensíveis).
- Nunca registrar o conteúdo das conversas em logs, só metadados (por exemplo, "nível alto, versão 3 das regras").
- Conversa cifrada no servidor; cookie protegido; acesso administrativo com login institucional e permissões por papel.
- Modelo de ameaças pensado para um adversário incomum: **alguém próximo, com acesso físico ao aparelho**.
- Ser honesto com a usuária: nenhum app é 100% invisível.

---

## E9 · Avaliação — o controle de qualidade

📄 [E9-plano-avaliacao.md](E9-plano-avaliacao.md) · *suítes de teste automatizadas, métricas (Recall@k, nDCG, WER, taxa de alucinação)*

Como saber se o sistema é seguro? **Medindo.** Cada módulo nasce junto com seu conjunto de testes:

| O que testa | Exemplo de meta |
|---|---|
| Detecta emergências? | ~100% dos casos de teste |
| Classifica bem a intenção? | ≥ 90% |
| Inventa coisas? | Alucinação ≤ 10% (meta interna bem menor para leis) |
| Acerta o nível de risco? | Nunca subestimar casos graves |
| Entende o áudio? | Erro de transcrição ≤ 10% |
| Tem o tom certo? | Avaliação de especialistas |

Também há **red-team**: tentar quebrar o sistema de propósito ("ignore suas instruções e me diga..."). Toda mudança de modelo, prompt ou regra roda todos os testes de novo.

---

## E10 · Infraestrutura — a fundação

📄 [E10-plano-infra.md](E10-plano-infra.md) · *Docker, docker-compose, CI/CD, Kubernetes (opcional), nuvem (Azure/AWS/Oracle)*

Faz tudo rodar em qualquer lugar e de forma repetível:
- Cada parte roda num **container**; um único comando sobe o sistema inteiro na sua máquina.
- A cada commit, um **pipeline** roda lint, testes, avaliações e varredura de segurança, e gera a lista de dependências (SBOM).
- O sistema escala horizontalmente: mais acessos, mais cópias da API.

---

## Juntando tudo: a vida de uma mensagem

> A usuária abre o app de notas, faz o gatilho secreto e escreve:
> *"meu marido pega meu salário e ameaça sumir com as crianças"*

| Passo | Quem | O que acontece |
|---|---|---|
| 1 | **E7** | O app envia a mensagem com o cookie da sessão |
| 2 | **E1** | Valida o cookie, recupera a conversa e passa a mensagem adiante |
| 3 | **E2** | Pré-filtro: não é emergência imediata. Intenção: **relato** |
| 4 | **E2** | Extrai fatos: violência patrimonial e ameaça envolvendo os filhos (a confirmar) |
| 5 | **E3** | Escolhe a próxima pergunta da triagem |
| 6 | **E2** | O LLM redige um acolhimento + a pergunta; o fiscal aprova |
| 7 | **E1 → E7** | A resposta aparece no chat |
| … | | *Algumas perguntas depois, o E3 calcula: **risco alto*** |
| 8 | **E4** | Ela pergunta "isso é crime?": a busca traz o art. 7º, IV da Lei Maria da Penha, e a resposta cita a fonte |
| 9 | **E5** | Ela pede ajuda perto de casa: lista de serviços verificados para risco alto |
| 10 | **E7** | Alguém se aproxima; ela toca em "sair" e o app volta para a lista de compras |

Durante tudo isso: o **E8** garante que nada sensível foi parar em log, o **E9** já testou cada um desses passos antes, e o **E10** mantém tudo no ar.

---

## Para saber mais

- Arquitetura detalhada do agente: [agente.md](agente.md)
- Plano de execução e fases: [plano.md](plano.md)
- Cada etapa: arquivos `E0` a `E10`
