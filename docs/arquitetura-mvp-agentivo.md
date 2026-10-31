# Arquitetura do MVP agentivo

## Escopo

O MVP substitui o fluxo de geração única por um agente deliberadamente limitado. Ele
mantém o histórico completo em SQLite, envia uma janela recente à LLM e permite que o
próprio modelo escolha entre responder, pesquisar fontes jurídicas ou solicitar
transbordo. Classificadores, RAG geral, autenticação, frontend e atendimento humano real
continuam fora deste incremento.

## Componentes

```text
Frontend futuro
      ↓
FastAPI
      ↓
TurnService ──→ ConversationRepository / SQLite
      ↓
AgentRuntime ─→ Ollama ou endpoint OpenAI compatível
      ↓
FastMCP ClientGroup
  ├── legal_search_legal_sources        (MCP HTTP)
  └── operations_request_human_handoff  (MCP em memória)
```

O host é o backend. Ele abre um cliente para cada servidor MCP, unifica os schemas com
`ClientGroup` e acrescenta os prefixos `legal_` e `operations_`. Todas as ferramentas
disponíveis são enviadas à LLM em cada turno; não existe roteador semântico no MVP.

## Ciclo de um turno

1. A FastAPI valida a conversa e a chave idempotente.
2. O serviço persiste a mensagem da usuária e monta a memória configurada.
3. O catálogo tenta conectar o MCP jurídico e sempre registra a ferramenta operacional.
4. A LLM recebe o contexto e todos os schemas disponíveis.
5. O runtime valida o nome e os argumentos de cada chamada antes de executá-la.
6. Resultados jurídicos recebem referências transitórias `[F1]`, `[F2]` e voltam somente
   ao contexto do turno.
7. O backend valida as referências da resposta; há uma tentativa de correção e, se ela
   falhar, uma resposta conservadora substitui a orientação sem fonte.
8. Resposta, tentativas, fontes citadas, ferramentas e eventual transbordo são persistidos.

O loop aceita no máximo duas rodadas e três chamadas, sempre sequenciais. Resultados
jurídicos têm orçamento próprio de 1.600 tokens.

## Memória

`recent-window-v1` é o padrão: o banco guarda tudo e o modelo recebe apenas a janela
recente. `summary-window-v1` permanece opcional. Um resumo nunca deve transformar
resultados do RAG, classificações ou afirmações da assistente em fatos da usuária; deve
preservar tempo, negações e correções.

O campo `memory_profile` fica associado à conversa. A abstração permite acrescentar
memória estruturada depois sem alterar os endpoints básicos.

## Pesquisa jurídica

O MCP jurídico expõe apenas `search_legal_sources`. Ingestão, indexação e avaliação são
comandos administrativos. `strategy=null` significa `auto` e `top_k=null` significa 5.
O servidor informa estratégia solicitada e efetiva, fallback, versão do corpus e
metadados de cada trecho; não declara que a fonte responde definitivamente à pergunta.

BM25 é obrigatório. Busca densa e híbrida são opcionais, carregadas sob demanda, mas
nunca baixadas durante uma consulta. Se a camada densa não estiver pronta, `auto` usa
BM25 e registra o fallback. Um pedido explícito denso/híbrido retorna erro tipado.

## Transbordo

`request_human_handoff` recebe somente modo e motivo enumerados. O backend injeta o ID da
conversa e bloqueia dados pessoais nos argumentos. `immediate` só é permitido para
possível perigo atual. Se pesquisa e transbordo forem pedidos juntos, o transbordo vence,
encerra o loop e seleciona um template controlado que a LLM não pode reescrever.

No MVP, `SimulatedHandoffService` sempre informa `human_available=false`. O template de
oferta explica a ausência de atendente; o imediato também informa 190 e Ligue 180 em até
90 palavras.

## Degradação e expansão

Se o MCP jurídico estiver indisponível, o catálogo mantém o transbordo, marca `legal`
como degradado e o prompt proíbe orientação jurídica específica. A arquitetura admite
novos provedores, servidores MCP, memória, autenticação e políticas de acesso sem mudar
os contratos atuais. Quando o catálogo crescer, uma `ToolAccessPolicy` poderá limitar o
conjunto estrutural e um `ToolRouter` poderá selecionar ferramentas por turno.

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
