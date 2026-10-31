# Backend agentivo do Notas.IA

FastAPI experimental que mantém conversas em SQLite e executa um agente limitado com
duas ferramentas:

- `legal_search_legal_sources`, fornecida pelo serviço MCP jurídico;
- `operations_request_human_handoff`, fornecida por FastMCP em memória.

Todas as ferramentas disponíveis são apresentadas à LLM em cada turno. O backend valida
nomes e argumentos, limita rodadas e chamadas, mantém fontes fora da memória factual e
usa respostas controladas para transbordo simulado.

## Instalação e execução

O caminho recomendado é executar o conjunto pelo `compose.yaml` da raiz. A imagem deste
serviço usa `config.container.ini`, no qual os hosts internos são `ollama` e `legal-mcp`.

Execução isolada, sem containers:

```powershell
python -m pip install -e ".[dev]"
Copy-Item config.example.ini config.ini
python -m notas_ia api --config config.ini
```

Com o servidor ativo, a documentação OpenAPI fica em `http://127.0.0.1:8000/docs`.
Também existe um cliente simples de terminal:

```powershell
python -m notas_ia chat --url http://127.0.0.1:8000
```

O perfil escolhido precisa declarar `SUPPORTS_TOOLS = true`. URLs e segredos são
configuração do servidor; chaves devem existir apenas na variável indicada por
`API_KEY_ENV`.

## Testes

```powershell
python -m pytest -q
```

Os testes usam LLMs e transportes falsos. Nenhum modelo real ou acesso externo é
necessário.
