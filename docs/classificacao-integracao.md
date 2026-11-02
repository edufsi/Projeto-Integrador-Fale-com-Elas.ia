# Classificação experimental no backend

Esta camada é de auditoria e avaliação. Ela não é uma decisão jurídica, não altera a memória factual da conversa e não aciona transbordo automaticamente.

## Modos

O arquivo de configuração possui uma única política global:

```ini
[CLASSIFICATION]
MODE = disabled                 # disabled | shadow | agent_context
ONLINE_CLASSIFIERS = local-llama8
AGENT_CONTEXT_CLASSIFIER = local-llama8
TAXONOMY_VERSION = v1
```

- `disabled` é o padrão. O backend não cria o registro de classificadores, não faz chamada extra, não salva snapshots nem adiciona qualquer contexto.
- `shadow` executa, valida e persiste cada perfil de `ONLINE_CLASSIFIERS`, em sequência. A resposta, ferramentas, RAG e memória são exatamente os mesmos do fluxo sem classificação.
- `agent_context` aceita exatamente um classificador em `ONLINE_CLASSIFIERS`, igual a `AGENT_CONTEXT_CLASSIFIER`. O agente recebe apenas uma hipótese curta e marcada como não verificada. Ela não é fato da usuária e não decide ferramentas.

Perfis de classificação são separados de perfis de conversa. Um perfil `llm` aponta para um `[MODEL.*]`; um perfil `system_one` chama o endpoint completo `/v1/systemone` do llama.cpp.

```ini
[CLASSIFIER.local-llama8]
KIND = llm
MODEL_PROFILE = local-llama8
MAX_OUTPUT_TOKENS = 500
TEMPERATURE = 0

[CLASSIFIER.kev4b]
KIND = system_one
API_URL = http://127.0.0.1:8080/v1/systemone
MODEL = ggml-org/Kev-4B-GGUF:Q4_K_M
```

## Estado e persistência

Em cada turno, a ordem é:

```text
memória factual → snapshot congelado → classificação → agente → persistência da resposta
```

O snapshot contém somente o resumo factual aplicável e as mensagens recentes da usuária, incluindo a atual. Respostas da assistente, resultados de ferramentas e trechos RAG não entram nele: podem conter exemplos, telefones, orientação ou erros anteriores e não são evidência do relato. Ele possui hash SHA-256 e é guardado com a execução para replay. Inferências ficam nas tabelas `classification_runs`, `classification_labels` e `classification_evidence`; resumos e mensagens nunca recebem esses rótulos.

A ontologia `v1` possui seis tipos com múltiplos indícios (`fisica`, `psicologica`, `sexual`, `patrimonial`, `moral`, `vicaria`), cinco intenções e quatro urgências. Confiança é somente um sinal diagnóstico sem calibração. A validação exige rótulos válidos, confiança entre 0 e 1 e, quando a LLM oferecer evidência, que a citação seja literal e aponte para a mensagem correta. Não há armazenamento de cadeia de pensamento.

O System One não gera evidência textual; sua resposta conserva probabilidades e escolhas tipadas, sendo registrada com a nota de que não há evidência gerada. A API do llama.cpp recebe um estado e perguntas `noul`/`choice` na mesma chamada. Consulte a [documentação de decision models do llama.cpp](https://huggingface.co/blog/ggml-org/decision-models-in-llamacpp) antes de atualizar o runtime.

## Auditoria e replay

Quando habilitada, a resposta de turno traz `classifications`. Também estão disponíveis:

- `GET /v1/classifier-profiles`;
- `GET /v1/conversations/{id}/classifications/latest`.

Para comparar o Kev (ou outro perfil) com os mesmos snapshots já produzidos pela LLM, pare o modelo de conversa se ambos usam a mesma GPU e execute serialmente:

```powershell
python -m notas_ia classify-replay --config apps/backend/config.ini `
  --source-profile local-llama8 --target-profile kev4b
```

`--conversation-id` e `--limit` restringem o replay. O comando nunca reconstitui um estado a partir do histórico atual: usa o JSON congelado. Não execute Llama 8B e Kev simultaneamente na RTX 4060 de 8 GB; o backend já chama classificadores em série, mas o carregamento dos processos é responsabilidade operacional.

Para uma comparação ponta a ponta, em vez de somente replay de snapshots, use o
[executor de avaliação](avaliacao-executor.md). Ele reproduz as mesmas conversas pela
API pública e distingue explicitamente os modos `disabled`, `shadow` e
`agent_context` nos manifestos e relatórios.

### Kev opcional por Compose

`compose.kev.yaml` é uma sobreposição opcional para o preflight Qwen 4B + Kev 4B. Ela
usa `ghcr.io/ggml-org/llama.cpp:server-cuda`, cacheia o GGUF em um volume nomeado e
constrói o backend com `config.container.kev.ini`. Esse arquivo reduz o orçamento do
Qwen para 4.096 tokens, limita a saída a 256 tokens e habilita somente `kev4b` em modo
`shadow`. Execute-o com:

```powershell
docker compose -f compose.yaml -f compose.gpu.yaml -f compose.kev.yaml `
  --profile kev up --build
```

O perfil normal `config.container.ini` fica em `disabled`; portanto, a ausência de Kev
nunca gera falhas classificatórias na execução padrão. Mesmo no perfil opcional, falha
ou indisponibilidade de Kev é persistida como auditoria e não derruba a conversa. Se os
dois processos não couberem juntos na VRAM, registre o resultado e faça o replay serial
em vez de reduzir silenciosamente o conjunto experimental.

## Experimento mínimo

1. Configure `MODE=shadow` e `ONLINE_CLASSIFIERS=local-llama8`.
2. Disponibilize o modelo escolhido no Ollama (`ollama pull llama3.1:8b` fora de containers). A variante 3.1 é usada porque declara suporte a tool calling; Llama 3.0 não é adequada ao agente atual, que sempre recebe ferramentas. No Compose, o perfil `llama8` baixa esse modelo no volume antes de habilitar o perfil.
3. Faça o preflight do Llama 8B com contexto de 4.096, as cinco ferramentas iniciais e o orçamento de RAG.
4. Colete conversas e snapshots sem usar os resultados na resposta.
5. Pare o Llama, inicie o Kev no llama.cpp e rode o replay.
6. Compare latência, cobertura, evidências inválidas, tipos, intenção, urgência e falsos negativos de urgência imediata.
7. Só então use `MODE=agent_context` em uma cópia dos mesmos casos e compare a resposta e as ferramentas escolhidas.

Uma falha de classificador gera um registro com `status=failed` e não derruba a conversa. `disabled` deve continuar sendo a condição de referência de latência e comportamento.

## Regressões de linguagem ambígua

Os casos manuais em `apps/backend/tests/fixtures/safety-regressions.v1.json` incluem
expressões figuradas (`me matou de rir`, `morri de medo`), ameaça literal atual e uma
revogação após entrada mínima (`SOCORRO` seguido de teste). Eles existem para revelar
falsos positivos de classificadores e escaladas impróprias; devem ser executados contra
cada perfil novo e não contam como teste ouro nem substituem avaliação humana.
