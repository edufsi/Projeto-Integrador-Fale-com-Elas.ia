# Arquitetura do MVP agentivo

## Escopo

O MVP substitui o fluxo de geração única por um agente deliberadamente limitado. Ele
mantém o histórico completo em SQLite, envia uma janela recente à LLM e permite que o
próprio modelo escolha entre responder, pesquisar fontes jurídicas ou solicitar
transbordo. A classificação experimental agora pode ser desligada, executada em modo
sombra ou apresentada como hipótese auxiliar; RAG geral, autenticação, frontend e
atendimento humano real continuam fora deste incremento.

## Componentes

```text
Frontend futuro
      ↓
FastAPI
      ↓
TurnService ──→ ConversationRepository / SQLite
      ├──────→ ClassificationService (opcional, separado da memória)
      ↓
AgentRuntime ─→ Ollama ou endpoint OpenAI compatível
      ↓
FastMCP ClientGroup
  ├── legal_search_legal_sources        (MCP HTTP)
  └── operations_offer_human_handoff / operations_escalate_immediate  (MCP em memória)
  └── information_get_general_help_resources / information_get_violence_type_overview
                                                     (MCP em memória, conteúdo curado)
```

O host é o backend. Ele abre um cliente para cada servidor MCP, unifica os schemas com
`ClientGroup` e acrescenta os prefixos `legal_` e `operations_`. Todas as ferramentas
disponíveis são enviadas à LLM em cada turno; não existe roteador semântico no MVP.

## Ciclo de um turno

1. A FastAPI valida a conversa e a chave idempotente.
2. O serviço persiste a mensagem da usuária e monta a memória configurada.
3. Se habilitada, a classificação recebe um snapshot factual congelado. Em modo sombra,
   ela termina aqui; em modo de contexto, somente uma hipótese compacta e não factual é
   acrescentada ao prompt do agente.
4. O catálogo tenta conectar o MCP jurídico e sempre registra a ferramenta operacional.
5. A LLM recebe o contexto e todos os schemas disponíveis.
6. O runtime valida o nome e os argumentos de cada chamada antes de executá-la.
7. Resultados jurídicos recebem referências transitórias `[F1]`, `[F2]` e voltam somente
   ao contexto do turno.
8. O backend valida as referências da resposta; há uma tentativa de correção e, se ela
   falhar, uma resposta conservadora substitui a orientação sem fonte.
9. Resposta, tentativas, fontes citadas, ferramentas, classificação e eventual transbordo
   são persistidos em áreas separadas.

O loop aceita no máximo duas rodadas e três chamadas, sempre sequenciais. Resultados
jurídicos têm orçamento próprio de 1.600 tokens.

## Memória

`recent-window-v1` é o padrão: o banco guarda tudo e o modelo recebe apenas a janela
recente. `summary-window-v1` permanece opcional. Um resumo nunca deve transformar
resultados do RAG, classificações ou afirmações da assistente em fatos da usuária; deve
preservar tempo, negações e correções.

O campo `memory_profile` fica associado à conversa. A abstração permite acrescentar
memória estruturada depois sem alterar os endpoints básicos.

## Classificação experimental

`disabled` é a condição de referência e não instancia classificadores. `shadow` persiste
inferências para auditoria sem mudar o agente. `agent_context` exige exatamente um
classificador e lhe entrega apenas rótulos, confiança diagnóstica, evidências literais e
nota curta, explicitamente como hipótese. Nenhum dos modos causa transbordo automático.

O snapshot e seus resultados ficam em tabelas próprias, com hash e JSON congelado para
replay. O snapshot contém apenas o resumo factual e declarações da usuária; respostas da
assistente, RAG e ferramentas são excluídos para não contaminar a classificação com texto
gerado. Isso permite rodar Kev ou outro modelo System One sobre exatamente a mesma entrada
depois de descarregar o modelo de conversa da GPU. Veja o [guia de integração](classificacao-integracao.md).

## Pesquisa jurídica

O MCP jurídico expõe apenas `search_legal_sources`. Ingestão, indexação e avaliação são
comandos administrativos. `strategy=null` significa `auto` e `top_k=null` significa 5.
O servidor informa estratégia solicitada e efetiva, fallback, versão do corpus e
metadados de cada trecho; não declara que a fonte responde definitivamente à pergunta.

BM25 é obrigatório. Busca densa e híbrida são opcionais, carregadas sob demanda, mas
nunca baixadas durante uma consulta. Se a camada densa não estiver pronta, `auto` usa
BM25 e registra o fallback. Um pedido explícito denso/híbrido retorna erro tipado.

## Informação curada e localização futura

O backend também possui dois recursos locais, versionados e independentes do RAG:
`information_get_general_help_resources` traz canais nacionais e limites da informação
geral; `information_get_violence_type_overview` traz explicações educativas dos tipos
adotados no protótipo. Ambos carregam conteúdo, data de revisão, escopo e fontes oficiais
em `apps/backend/src/notas_ia/information/resources/`. Eles não confirmam disponibilidade
local e não substituem fonte jurídica para uma dúvida específica.

Uma futura busca de instituições próximas não será exposta até que haja: consentimento
explícito e revogável para usar localização; minimização e retenção definida dos dados;
uma fonte institucional de serviços georreferenciados; e uma resposta que distinga local
aproximado de confirmação de atendimento. A localização não deve ser inserida no resumo
factual, em logs ou no contexto de modelos sem necessidade e consentimento registrados.

## Transbordo

`operations_offer_human_handoff` e `operations_escalate_immediate` são ferramentas distintas. A primeira
aceita o motivo `explicit_human_request` ou `insufficient_confidence`; a segunda não aceita
argumentos e sempre representa `possible_current_danger`. O backend injeta o ID da conversa
e bloqueia dados pessoais nos argumentos. Se pesquisa e transbordo forem pedidos juntos,
uma escalada imediata válida vence, encerra o loop e seleciona um template controlado que a
LLM não pode reescrever.

Erros esperados de uma ferramenta retornam ao modelo como resultado transitório
estruturado (`status=error`, ferramenta e código), sem instruir a próxima ação. A LLM
pode tentar outra operação ou responder, dentro dos limites configurados de rodadas e
chamadas; o backend continua bloqueando ferramentas desconhecidas e transbordos revogados.

No MVP, `SimulatedHandoffService` sempre informa `human_available=false`. O template de
oferta explica a ausência de atendente; o imediato também informa 190 e Ligue 180 em até
90 palavras. Fora desse template, a saída não pode exibir ou associar canais de emergência
sem que `information_get_general_help_resources` tenha retornado no mesmo turno; uma
resposta que viole essa regra é substituída por fallback conservador.

## Degradação e expansão

Se o MCP jurídico estiver indisponível, o catálogo mantém o transbordo, marca `legal`
como degradado e o prompt proíbe orientação jurídica específica. A arquitetura admite
novos provedores, servidores MCP, memória, autenticação e políticas de acesso sem mudar
os contratos atuais. Quando o catálogo crescer, uma `ToolAccessPolicy` poderá limitar o
conjunto estrutural e um `ToolRouter` poderá selecionar ferramentas por turno.

## Avaliação integrada

O módulo `notas_ia.evaluation` chama a API pública em vez de atalhos internos. Assim,
cada rodada exercita persistência, memória, classificação, ferramentas, RAG e resposta
da mesma forma que a CLI. O manifesto grava o modo de classificação e se uma hipótese
entrou no contexto. Resultados são separados por nível de revisão do corpus; o executor
não transforma material draft em teste ouro nem inventa turnos ausentes da suíte de
emergência. O [guia do executor](avaliacao-executor.md) define presets e métricas.

## Limitações

- aplicação restrita a `127.0.0.1`, sem autenticação e com um worker;
- transbordo apenas simulado;
- sem streaming;
- qualidade e segurança ainda dependem de avaliação experimental;
- corpus e gabarito jurídico ainda carecem de revisão especializada.

## Implantação local com Compose

O ambiente reproduzível possui os seguintes serviços:

```text
host:8000 → backend → ollama:11434
                    → legal-mcp:8001/mcp

legal-index ──(volume legal-index)──→ legal-mcp
ollama-model ──(volume ollama-models)──→ ollama
```

`legal-index` e `ollama-model` são tarefas de inicialização que precisam terminar com
sucesso antes do backend. O SQLite permanece em `data/private/`; modelos e índice usam
volumes nomeados. Apenas portas ligadas a `127.0.0.1` são publicadas. O arquivo
`compose.gpu.yaml` acrescenta uma reserva NVIDIA ao Ollama sem alterar os serviços de
aplicação. A CLI é um serviço opcional, executado interativamente com
`docker compose run --rm cli`.
