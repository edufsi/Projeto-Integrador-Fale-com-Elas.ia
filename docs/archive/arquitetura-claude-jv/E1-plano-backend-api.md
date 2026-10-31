# E1 — Backend, API e sessão

← [plano.md](plano.md) · Arquitetura: [agente.md](agente.md) §3, §14

## 1. Objetivo
Uma API REST **independente de canal**, stateless, com sessão anônima **persistida por cookie** (a conversa continua na próxima vez que ela abrir a página) e metadados de versão em toda resposta. É o "esqueleto" onde os demais módulos se encaixam.

## 2. Módulos-chave

| Módulo | Responsabilidade | Tecnologia |
|---|---|---|
| API Gateway / rotas | Endpoints, validação, rate limit, CORS | FastAPI + Pydantic |
| Contrato OpenAPI | Fonte da verdade para interface e testes | OpenAPI 3 (gerado + revisado) |
| Store de sessão | Estado e histórico da conversa, com o mesmo prazo do cookie; conteúdo cifrado em repouso | Redis com persistência (AOF) ou Postgres |
| Autenticação da usuária | Sessão anônima identificada por **cookie** com token opaco (ver §3) | Middleware próprio |
| Autenticação administrativa | Painéis e base de serviços | Entra ID/OIDC + RBAC |
| Proteção CSRF | Impede outro site de agir com o cookie dela | SameSite=Strict + checagem de `Origin` + cabeçalho próprio |
| Middleware de privacidade | Mascara PII antes de logar; nunca loga conteúdo | Middleware próprio |
| Registro de versões | Injeta `regras`, `corpus`, `modelo`, `prompt` na resposta | Config central |
| Auditoria WORM | Log de decisão append-only (sem conteúdo) | Armazenamento append-only |
| Adaptador de canais | Traduz app/web/WhatsApp para o formato interno | Adaptadores por canal |

## 3. Sessão da usuária por cookie

Sem login e sem conta: o cookie só liga o navegador dela a uma conversa anônima no servidor.

| Item | Especificação |
|---|---|
| Valor | Token **opaco** aleatório (≥ 128 bits). O servidor guarda só o **hash**; não é JWT, para poder ser revogado na hora |
| Nome | Neutro, sem relação com o tema (ex.: `nt_sync`) |
| Atributos | `HttpOnly` (JavaScript não lê), `Secure` (só HTTPS), `SameSite=Strict`, `Path=/v1` |
| Validade | `Max-Age` configurável. Proposta: **7 dias, renovados a cada uso, com teto absoluto de 30 dias**. Valores finais definidos no RIPD (E8) |
| Rotação | Novo token ao retomar a sessão e periodicamente; o antigo é invalidado |
| Sem persistência | Se ela marcar "não lembrar neste aparelho" no consentimento, vira cookie de sessão (sem `Max-Age`) e o servidor usa TTL curto (ex.: 30 min) |
| Encerramento | `DELETE /v1/session` apaga os dados no servidor **e** responde com `Set-Cookie` expirado |
| Expiração | Servidor expurga a sessão quando o prazo vence, mesmo que o cookie continue no aparelho |

Como o token vai no cookie, ele **não aparece em URLs** (nem no histórico do navegador). Por isso as rotas usam `/v1/session` (a sessão "atual"), sem id no caminho.

## 4. Endpoints (MVP)

```
POST   /v1/session              cria sessão anônima → Set-Cookie
GET    /v1/session              retoma: histórico + estado do fluxo + nível de risco (se o cookie for válido)
POST   /v1/session/messages     texto (áudio na E6) → resposta estruturada
GET    /v1/session/risk         nível atual (para o Violentômetro visual)
DELETE /v1/session              apaga tudo no servidor + expira o cookie
GET    /v1/network              serviços próximos (E5)
GET    /v1/health  /v1/version  operação e versões
```

Resposta padrão: `{ reply, intent, risk, actions[], citations[], abstained, versions }`.

## 5. Tarefas

1. Repositório, formatação/lint, CI mínimo (ver [E10-plano-infra.md](E10-plano-infra.md)).
2. Esqueleto FastAPI + OpenAPI; `POST`, `GET` e `DELETE /v1/session` funcionando.
3. Emissão e validação do cookie (§3): geração do token, hash no servidor, atributos, renovação e rotação.
4. Store de sessão com prazo igual ao do cookie, persistência entre reinícios e conteúdo da conversa **cifrado em repouso**.
5. Expurgo automático no vencimento e no `DELETE` (inclui backups: sessões não entram em backup).
6. Proteção CSRF: `SameSite=Strict`, checagem de `Origin` e exigência de cabeçalho próprio nas rotas que alteram estado.
7. Modelo de dados da sessão: histórico, respostas do questionário, estado do fluxo, nível de risco. **Sem PII persistida** (mascaramento antes de gravar).
8. Middleware: request-id, mascaramento, logs estruturados sem corpo e **sem o valor do cookie**.
9. Endpoint `messages` chamando o orquestrador (stub → E2).
10. RBAC + Entra ID para rotas administrativas.
11. Testes de contrato (schemathesis ou similar) e testes de segurança do cookie (atributos, revogação, CSRF).

## 6. Decisões de projeto
- **Stateless**: qualquer instância atende qualquer sessão (escala horizontal); o estado fica no store.
- **Sem contas de usuária** na MVP: o cookie identifica a conversa, não a pessoa.
- **Persistência por cookie** é decisão do projeto (D5 em [E0-plano-fundamentos.md](E0-plano-fundamentos.md)); os cuidados com o aparelho estão em [E7-plano-interface.md](E7-plano-interface.md) e [E8-plano-privacidade-seguranca.md](E8-plano-privacidade-seguranca.md).
- **Idempotência** em `messages` (id do cliente) para reenvios em rede ruim.

## 7. Critérios de pronto
- Criar sessão → conversar → fechar o navegador → reabrir → `GET /v1/session` devolve a conversa.
- `DELETE /v1/session` → nada resta no store e o cookie fica expirado no navegador.
- Sessão vencida é expurgada no servidor mesmo sem `DELETE`.
- Cookie com `HttpOnly`, `Secure` e `SameSite=Strict` verificado por teste; requisição de outra origem é recusada.
- Logs sem conteúdo de mensagem e sem valor do cookie (verificado por teste).

## 8. Riscos
- **Conversa reaparece para quem pegar o aparelho** → retomada só depois do gatilho do app de notas e cookie com nome/domínio neutros (ver E7 e E8).
- Roubo do cookie → `HttpOnly`, `Secure`, rotação, revogação imediata, prazo limitado.
- Vazamento em logs/erros → teste automatizado que falha se corpo ou cookie aparecerem em log.
- Latência do LLM → streaming de resposta e timeouts com resposta de contingência.
