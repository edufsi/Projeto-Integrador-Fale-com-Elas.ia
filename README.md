# Notas.IA

Protótipo acadêmico de assistente conversacional com memória local, pesquisa de fontes
jurídicas e transbordo humano simulado.

```text
cliente → FastAPI / AgentRuntime → LLM com tool calling
                     ├──────────→ MCP jurídico (HTTP)
                     └──────────→ transbordo FastMCP (em memória)
```

O backend também pode executar classificação experimental em modo sombra ou como hipótese
auxiliar explicitamente marcada; ela não modifica a memória nem aciona transbordo automático.
Veja [a integração de classificação](docs/classificacao-integracao.md).

O projeto não foi validado para atendimento real. O transbordo não conecta uma pessoa e
a recuperação de fontes não constitui orientação jurídica.

## Estrutura

- `apps/backend/`: API, agente, provedores de LLM, memória e SQLite;
- `services/legal-mcp/`: submódulo com ingestão, índices, avaliação e servidor MCP;
- `data/reference/`: materiais de referência preservados;
- `data/archive/`: corpora e resultados experimentais anteriores;
- `docs/`: decisões de arquitetura e avaliação;
- `deliverables/`: apresentações.

## Execução recomendada com Docker

Pré-requisitos no Windows:

- Docker Desktop com backend WSL2;
- drivers NVIDIA atualizados para usar a RTX 4060;
- submódulo inicializado.

```powershell
git submodule update --init --recursive
docker compose -f compose.yaml -f compose.gpu.yaml up --build
```

Na primeira execução, o Compose constrói os dois serviços Python, gera os índices BM25 e
denso `e5-small`, baixa `qwen3.5:4b` para o volume do Ollama e faz uma inferência curta de aquecimento.
O backend só inicia depois desse aquecimento, evitando que a primeira mensagem da CLI
receba um erro transitório durante a carga do modelo. Os próximos inícios reutilizam os
volumes.

Para executar sem GPU:

```powershell
docker compose up --build
```

O arquivo de GPU é opcional. Se o Docker Desktop ou o runtime NVIDIA reiniciar durante
a inferência, confirme primeiro que a pilha em CPU funciona e diagnostique a integração
WSL2/NVIDIA separadamente. Para fixar uma versão do Ollama em vez de usar `latest`,
defina em um arquivo `.env` local um tag do Ollama que tenha sido validado com o modelo:

```dotenv
OLLAMA_VERSION=<tag-validado>
```

Para abrir a CLI em um container, com o conjunto já iniciado:

```powershell
docker compose run --rm cli
```

Endereços publicados somente em loopback:

- FastAPI e Swagger: `http://127.0.0.1:8000/docs`;
- saúde do backend: `http://127.0.0.1:8000/health/ready`;
- MCP jurídico: `http://127.0.0.1:8001/mcp`;
- saúde jurídica: `http://127.0.0.1:8001/health/ready`.

O Ollama do Compose não publica `11434` no host; apenas o backend o acessa pela rede
interna. Isso permite manter simultaneamente uma instalação independente do Ollama no
WSL sem disputar a mesma porta.

Comandos operacionais:

```powershell
docker compose ps
docker compose logs -f backend legal-mcp ollama
docker compose down
```

`docker compose down` preserva os modelos, o índice e o SQLite. Evite `down -v`, que
remove os volumes de modelos e índice. O SQLite usa `data/private/` no host.

## Avaliação integrada

O backend possui um executor HTTP que reproduz os corpus sintéticos contra a pilha real,
registra classificações, ferramentas, RAG, transcrições, tokens e latência. Ele compara
os modos `disabled`, `shadow` e `agent_context` sem deixar a classificação em sombra
alterar o prompt do agente. As rodadas completas são privadas; consulte o
[guia do executor](docs/avaliacao-executor.md) para presets, Docker, corpus draft e
interpretação das métricas.

### Experimento local Qwen 4B + Kev 4B

O Kev é um modelo System One servido pelo `llama.cpp`, e não é compatível com Ollama.
Para não ocupar GPU na execução normal, ele está em uma sobreposição Compose opcional.
O comando abaixo baixa a imagem CUDA oficial do llama.cpp, baixa o GGUF `Kev-4B` para o
volume `kev-models`, inicia o endpoint `/v1/systemone` e recria o backend com
classificação em modo sombra:

```powershell
docker compose -f compose.yaml -f compose.gpu.yaml -f compose.kev.yaml `
  --profile kev up --build
```

O primeiro início pode levar alguns minutos. O serviço Kev fica exposto somente em
`127.0.0.1:8080`; o backend o alcança internamente em `http://kev:8080/v1/systemone`.
O backend aguarda `GET /health` do Kev antes de subir. Para acompanhar a carga:

```powershell
docker compose -f compose.yaml -f compose.gpu.yaml -f compose.kev.yaml logs -f kev
```

O experimento usa Qwen com 4.096 tokens de contexto, resposta de até 256 tokens e
`OLLAMA_KEEP_ALIVE=0`, para reduzir a pressão da RTX 4060 de 8 GB. Ainda assim, os dois
modelos podem não caber juntos na VRAM. Confira `nvidia-smi` e, se houver falha de carga,
use o replay do Kev em vez da classificação online. A pilha padrão continua sem Kev e com
classificação desativada.

Para testar e ver classificação, ferramentas e métricas separadas por etapa:

```powershell
docker compose -f compose.yaml -f compose.gpu.yaml -f compose.kev.yaml `
  --profile kev run --build --rm cli chat --url http://backend:8000 --trace
```

Para fixar a imagem do llama.cpp no lugar do tag móvel `server-cuda`, acrescente ao `.env`
local `LLAMA_CPP_IMAGE=<tag-ou-digest-validado>`. Não use o perfil `kev` em uma máquina
sem GPU NVIDIA configurada no Docker Desktop.

## Execução sem containers

Ao clonar:

```powershell
git clone --recurse-submodules <url-do-repositorio>
python -m pip install -e "services/legal-mcp[dev]"
python -m pip install -e "apps/backend[dev]"
python -m legal_rag index --strategy bm25
Copy-Item apps/backend/config.example.ini apps/backend/config.ini
```

Se o repositório já estiver clonado, use `git submodule update --init --recursive`.

## Execução local

Terminal 1:

```powershell
python -m legal_rag serve --host 127.0.0.1 --port 8001
```

Terminal 2:

```powershell
python -m notas_ia api --config apps/backend/config.ini
```

O Ollama deve estar ativo no mesmo ambiente de rede ou ter uma URL acessível configurada. A FastAPI fica em
`http://127.0.0.1:8000` e o MCP jurídico em `http://127.0.0.1:8001/mcp`.

## Testes

```powershell
python -m pytest -q apps/backend/tests
python -m pytest -q services/legal-mcp/tests services/legal-mcp/test_rag.py
```

Veja [a arquitetura do MVP](docs/arquitetura-mvp-agentivo.md) e os READMEs específicos
do backend e do serviço jurídico para configuração e limitações.
