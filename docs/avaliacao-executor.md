# Executor de avaliação do agente

O executor chama a API já em execução. Ele não baixa modelos, não inicia containers e
não altera a configuração do backend. Cada rodada grava transcrições sintéticas e
metadados em `data/private/evaluations/`, diretório ignorado pelo Git.

## Corpus e status

| Suite | Conteúdo | Status | Uso no relatório |
| --- | --- | --- | --- |
| `exploratory` | itens de `benchmark_exploratorio.json` | `single_reviewed` | métrica exploratória principal |
| `gold_draft` | conversas de `gold_conversations.draft.json` | `draft_pending_calibration` | métrica separada, não teste ouro |
| `safety` | regressões de metáfora, ameaça e revogação | `code_regression` | regressão de segurança |
| `emergency` | cenários de `emergency.draft.json` | `draft_pending_specialist_review` | métrica separada; aguarda revisão especializada |

O executor nunca mistura esses estados de revisão numa média única. Ele lê todos os
itens existentes nos arquivos, sem impor uma cardinalidade fixa. Uma suíte só é marcada
como `blocked_incomplete` se seu arquivo não possuir nenhum turno executável; nesse caso,
ela aparece no relatório sem impedir as demais suítes.

## Presets

| Preset | Agente | Classificação | Como o prompt é afetado |
| --- | --- | --- | --- |
| `qwen-only` | Qwen 4B | desativada | nenhuma inferência |
| `qwen-qwen-shadow` | Qwen 4B | Qwen 4B em sombra | não muda o prompt |
| `qwen-qwen-context` | Qwen 4B | Qwen 4B | hipótese compacta após a persona |
| `qwen-kev-shadow` | Qwen 4B | Kev 4B em sombra | não muda o prompt |
| `qwen-kev-context` | Qwen 4B | Kev 4B | hipótese compacta após a persona |
| `llama8-only` | Llama 8B | desativada | nenhuma inferência |
| `llama8-qwen-shadow` | Llama 8B | Qwen 4B em sombra | não muda o prompt |
| `llama8-llama8-shadow` | Llama 8B | Llama 8B em sombra | não muda o prompt |
| `llama8-kev-shadow` | Llama 8B | Kev 4B em sombra | não muda o prompt |

Em `agent_context`, a hipótese é uma mensagem de sistema auxiliar colocada depois da
persona e antes de resumo/histórico. Ela contém somente tipos com indício, intenção,
urgência, confiança, evidência literal validada e nota breve. Ela não é um fato da
usuária, não inclui resposta bruta/raciocínio do classificador e não pode disparar
ferramentas ou transbordo sozinha. Em `shadow`, a classificação é persistida para
auditoria, mas o prompt do agente é idêntico a `disabled`.

## Execução

Valide os dados antes da primeira rodada:

```powershell
docker compose run --build --rm cli evaluate validate-datasets --suites all
```

Para uma rodada curta inicial, use apenas benchmark e regressões:

```powershell
docker compose run --build --rm cli evaluate run `
  --url http://backend:8000 --preset qwen-only --suites exploratory,safety
```

Para os outros presets, reinicie explicitamente o backend com a sobreposição adequada:

```powershell
# Qwen como classificador em sombra
docker compose -f compose.yaml -f compose.gpu.yaml -f compose.qwen-shadow.yaml `
  up --build -d --force-recreate backend

# Qwen como hipótese de contexto
docker compose -f compose.yaml -f compose.gpu.yaml -f compose.qwen-context.yaml `
  up --build -d --force-recreate backend

# Kev em sombra
docker compose -f compose.yaml -f compose.gpu.yaml -f compose.kev.yaml `
  --profile kev up --build -d

# Kev como hipótese de contexto
docker compose -f compose.yaml -f compose.gpu.yaml -f compose.kev.yaml `
  -f compose.kev-context.yaml --profile kev up --build -d --force-recreate backend

# Llama 8B como agente; o perfil baixa o modelo no volume Ollama
docker compose -f compose.yaml -f compose.gpu.yaml --profile llama8 up --build -d

# Llama 8B como agente e Qwen 4B como classificador em sombra
docker compose -f compose.yaml -f compose.gpu.yaml -f compose.llama8-qwen-shadow.yaml `
  --profile llama8 up --build -d --force-recreate

# Llama 8B como agente e classificador, em chamadas sequenciais ao mesmo Ollama
docker compose -f compose.yaml -f compose.gpu.yaml -f compose.llama8-llama8-shadow.yaml `
  --profile llama8 up --build -d --force-recreate

# Llama 8B como agente e Kev como classificador em sombra
docker compose -f compose.yaml -f compose.gpu.yaml -f compose.kev.yaml `
  --profile llama8 --profile kev up --build -d --force-recreate
```

Depois de cada reinício, execute `evaluate run` com o preset correspondente. O executor
consulta `/health/ready`, `/version`, `/v1/model-profiles` e
`/v1/classifier-profiles`; se modo, modelo ou classificador não correspondem ao preset,
ele falha antes de gravar resultados. Use `--resume` somente para retomar uma rodada
interrompida no mesmo diretório.

Use os **mesmos arquivos `-f`** também no comando `run`. `docker compose run` cria o
cliente CLI; se ele for chamado só com `compose.yaml`, o Compose pode reaproveitar ou
iniciar dependências a partir da configuração-base (`disabled`). Exemplo completo para
Qwen em sombra:

```powershell
docker compose -f compose.yaml -f compose.gpu.yaml -f compose.qwen-shadow.yaml `
  up --build -d --force-recreate backend

docker compose -f compose.yaml -f compose.gpu.yaml -f compose.qwen-shadow.yaml `
  run --build --rm cli evaluate run `
  --url http://backend:8000 --preset qwen-qwen-shadow `
  --suites exploratory,safety,gold_draft,emergency
```

Antes de executar uma rodada longa, confirme o processo que está respondendo:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/v1/classifier-profiles
```

O resultado esperado contém `mode: shadow` e `online_classifiers: ["local-qwen4"]`.
Nos logs do backend deve aparecer `runtime_configuration classification_mode=shadow`.

## Artefatos e interpretação

Cada diretório de rodada contém:

- `manifest.json`: hashes, saúde do backend, preset, contrato de contexto, versões de
  prompt e modelos efetivamente reportados pelos provedores;
- `records.jsonl`: uma entrada por turno, com transcrição e resposta integral;
- `report.json` e `report.md`: métricas por estado de revisão;
- `audit.json` e `audit.html`: pacote humano editável e visualização local.

`evaluate compare` produz tanto o JSON estruturado quanto um Markdown tabular ao lado
dele. A tabela preserva os status de revisão; ela não agrega `single_reviewed`,
`draft_pending_calibration` e `code_regression` numa única média.

O relatório mede F1 por tipo, micro/macro F1, intenção, urgência, falsos negativos de
urgência imediata, ferramentas, templates, fontes, tamanho de resposta, tokens e
latência. Ações conversacionais como acolher ou formular a pergunta ideal permanecem
como auditoria humana; somente transbordo, oferta humana e uso observável de ferramenta
são pontuados automaticamente.

Compare rodadas apenas do mesmo corpus:

```powershell
docker compose run --build --rm cli evaluate compare --runs `
  /data/private/evaluations/<run-qwen> /data/private/evaluations/<run-kev>
```

Depois de registrar alterações no campo `auditoria_humana` de `audit.json`, gere de
novo a visualização estática sem repetir chamadas ao modelo:

```powershell
docker compose run --build --rm cli evaluate audit `
  --run /data/private/evaluations/<run-id>
```

O relatório não demonstra aptidão para atendimento real. Os casos são sintéticos e o
ouro draft permanece pendente de calibração humana.
