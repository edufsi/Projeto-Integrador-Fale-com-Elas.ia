# E7 — Interface: app de notas camuflado

← [plano.md](plano.md) · Ganchos exigidos: [agente.md](agente.md) §12, §14

## 1. Objetivo
Um app de notas **funcional e convincente** que esconde o acesso ao agente, com saída rápida e mínimo rastro no aparelho.

## 2. Módulos-chave

| Módulo | Responsabilidade |
|---|---|
| **Notas (fachada)** | Criar/editar/listar notas de verdade (lista de compras, receitas etc.); precisa parecer e funcionar como app de notas real |
| **Gatilho de acesso** | Forma discreta de abrir o chat: ex. sequência de toque, PIN em nota específica, título mágico. Não pode aparecer na UI |
| **Chat** | Conversa com o agente, texto e áudio; balões sóbrios, sem identidade "de violência" |
| **Retomada da conversa** | Depois do gatilho, chama `GET /v1/session`; se o cookie for válido, a conversa continua de onde parou |
| **Saída rápida** | Botão/gesto sempre visível. **Toque:** esconde o chat e volta às notas na hora, mantendo a sessão (o cookie continua). **Toque longo:** sai **e** apaga tudo (`DELETE /v1/session`) |
| **Apagar conversa** | Opção explícita dentro do chat: apaga a sessão no servidor e expira o cookie |
| **Violentômetro visual** | Renderiza o nível vindo de `GET /v1/session/risk` de forma educativa e não alarmista |
| **Ações rápidas** | Botões para 180/190/153*, abrir mapa/serviço, compartilhar nada |
| **Consentimento e termos** | Texto curto e claro, no primeiro uso do chat. Informa que a conversa fica guardada por até N dias e oferece "não lembrar neste aparelho" |
| **Limpeza local** | Ao sair: tira o chat da memória e da tela e limpa cache do chat. O cookie (`HttpOnly`) só é removido pelo servidor, via `DELETE` |
| **Acessibilidade** | Contraste, leitor de tela, tamanhos de fonte, linguagem simples |
| **Cliente de API** | Gerado do OpenAPI ([E1-plano-backend-api.md](E1-plano-backend-api.md)) |

\* confirmar 153 com MPRS.

## 3. Decisões técnicas

| Tema | Proposta |
|---|---|
| Plataforma | **PWA** (web) na MVP: um código, sem loja de apps, instalável e com ícone/nome neutros |
| Stack | TypeScript + React (ou Svelte) + Vite |
| Armazenamento local | Notas ficam no aparelho (IndexedDB). Do chat, o aparelho guarda **só o cookie de sessão** (nome neutro, `HttpOnly`); o histórico fica no servidor e só é carregado na tela depois do gatilho |
| Domínio | Endereço do site neutro (nada sobre violência ou IA), porque aparece nas configurações do navegador junto do cookie |
| Nome/ícone | Neutros (ex.: "Notas"), sem menção a violência ou à IA na tela inicial/manifest/título de aba |
| Notificações | **Sem** notificações do chat |
| Histórico do navegador | Chat sem URLs reveladoras; usar rota genérica e substituição de histórico |

## 4. Tarefas

1. Protótipo de baixa fidelidade (fluxo notas → gatilho → consentimento → chat → saída).
2. Testar o gatilho com pessoas reais: fácil para ela, invisível para outros.
3. Construir o app de notas funcional (CRUD, busca, pastas simples).
4. Componente de chat + estados de carregamento, erro e reconexão.
5. Saída rápida (toque = esconder; toque longo = esconder e apagar) e opção "apagar conversa".
6. Retomada: ao passar pelo gatilho, buscar `GET /v1/session` e redesenhar o histórico; tratar sessão expirada ("começar nova conversa").
7. Tela de consentimento com prazo de guarda e a opção "não lembrar neste aparelho".
8. Violentômetro visual (aprovado por especialista quanto a tom e cores).
9. Gravação de áudio (E6) com feedback discreto.
10. Modo "tela emprestada": abrir o chat não deixa entradas visíveis em "recentes".
11. Testes de usabilidade e acessibilidade (WCAG), incluindo baixa conectividade e celulares simples.
12. Revisão de privacidade (checklist em [E8-plano-privacidade-seguranca.md](E8-plano-privacidade-seguranca.md)).

## 5. Critérios de pronto
- Do chat às notas em menos de 1 segundo; fora o cookie de sessão, nada do chat resta no aparelho.
- Fechar e reabrir o navegador → depois do gatilho, a conversa continua.
- Toque longo na saída ou "apagar conversa" → reabrir mostra conversa nova.
- Um observador casual não identifica o app como algo além de notas.
- Funciona offline como app de notas; o chat avisa quando não há conexão.
- Teste com usuárias representativas (ou proxy) sem quebra de camuflagem.

## 6. Riscos
- **Descoberta pelo agressor** (maior risco do projeto) → camuflagem completa, testes de "revista do celular".
- **Com a persistência, quem descobrir o gatilho vê a conversa anterior** → gatilho difícil de adivinhar; considerar PIN próprio para retomar; deixar "apagar conversa" fácil de achar; prazo de guarda curto.
- **O desafio pede limpeza de dados na saída rápida (R10)**, e o toque simples agora mantém a sessão → o toque longo cumpre o requisito; confirmar com o MPRS se isso basta.
- Gatilho difícil demais ou fácil demais → iterar com testes de uso.
- Limitações de PWA em iOS/Android → validar cedo; considerar app nativo depois.
- Camuflagem que parece "boa" mas não protege → não prometer sigilo absoluto na UI; ser honesta sobre limites.
