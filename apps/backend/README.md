# Backend agentivo do Notas.IA

FastAPI experimental que mantém conversas em SQLite e executa um agente limitado com
cinco ferramentas:

- `legal_search_legal_sources`, fornecida pelo serviço MCP jurídico;
- `operations_offer_human_handoff` e `operations_escalate_immediate`, fornecidas por
  FastMCP em memória.
- `information_get_general_help_resources` e `information_get_violence_type_overview`,
  recursos locais curados e versionados.

Todas as ferramentas disponíveis são apresentadas à LLM em cada turno. O backend valida
nomes e argumentos, limita rodadas e chamadas, mantém fontes fora da memória factual e
usa respostas controladas para transbordo simulado.

A classificação é opcional e começa desativada. Nos modos `shadow` e `agent_context`,
inferências ficam separadas da memória factual; consulte o [guia de integração](../../docs/classificacao-integracao.md).
Para reproduzir rodadas HTTP contra os corpora e comparar os modos, consulte o
[executor de avaliação](../../docs/avaliacao-executor.md).

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

Durante teste, acrescente `--trace` para visualizar o traço auditável do turno:

```powershell
python -m notas_ia chat --url http://127.0.0.1:8000 --trace
```

Ele mostra o contexto usado, ferramentas disponíveis e executadas, fontes, transbordo,
serviços degradados e classificações validadas. Também informa o tempo de ida e volta do
turno, e os tokens e a latência reportados separadamente pela LLM do agente e por cada
classificador. Tipos positivos também mostram a confiança bruta retornada pelo perfil.
`não informado` significa que aquele provedor não devolveu a métrica; não é convertido em
zero. Não mostra cadeia de pensamento livre, prompts internos nem
argumentos brutos de ferramentas, pois estes podem conter dados da usuária e não
constituem uma explicação confiável do modelo.

Para executar um comparador sobre snapshots já produzidos, sem carregar dois modelos ao
mesmo tempo na GPU:

```powershell
python -m notas_ia classify-replay --config config.ini --source-profile local-llama8 --target-profile kev4b
```

O perfil escolhido precisa declarar `SUPPORTS_TOOLS = true`. URLs e segredos são
configuração do servidor; chaves devem existir apenas na variável indicada por
`API_KEY_ENV`.

### Kev / System One no Compose

O Compose padrão não carrega Kev nem classificação. Para o experimento local Qwen 4B +
Kev 4B, acrescente `-f compose.kev.yaml --profile kev` aos comandos da raiz. Essa
sobreposição inicia a imagem CUDA oficial do llama.cpp, baixa o GGUF no volume
`kev-models`, aguarda `GET /health` e constrói o backend com
`config.container.kev.ini`. Nesse perfil, o classificador aponta internamente para
`http://kev:8080/v1/systemone`, em modo `shadow`.

O serviço também publica `http://127.0.0.1:8080` apenas para diagnóstico. Uma resposta
404 para `/v1/systemone` normalmente indica uma imagem/versão anterior ao suporte a
System One, e não um erro da ontologia. Para usar um Kev iniciado fora do Compose ou em
outra máquina, mantenha `config.container.ini` como referência e troque somente
`[CLASSIFIER.kev4b].API_URL`; a interface do classificador permanece HTTP.

## Testes

```powershell
python -m pytest -q
```

Os testes usam LLMs e transportes falsos. Nenhum modelo real ou acesso externo é
necessário.
