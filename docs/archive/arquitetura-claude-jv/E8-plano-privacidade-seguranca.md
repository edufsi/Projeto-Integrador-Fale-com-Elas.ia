# E8 — Privacidade, segurança e conformidade

← [plano.md](plano.md) · Arquitetura: [agente.md](agente.md) §12

## 1. Objetivo
Proteger a usuária de vazamentos técnicos e de descoberta pelo agressor; cumprir a LGPD e os requisitos de segurança do desafio.

## 2. Módulos-chave

| Módulo | Responsabilidade |
|---|---|
| **Mapa de dados** | O que é coletado, onde fica, por quanto tempo, base legal |
| **RIPD** | Relatório de impacto à proteção de dados (dados sensíveis, art. 11 LGPD) |
| **Política de retenção** | Sessão persistida por cookie com prazo limitado (proposta: 7 dias renováveis, teto de 30); opção "não lembrar neste aparelho" com TTL curto; expurgo verificável no vencimento e no `DELETE` |
| **Consentimento** | Texto curto, granular; consentimento específico para qualquer compartilhamento |
| **Mascaramento de PII** | Nome, CPF, endereço, telefone mascarados antes de logs |
| **Auditoria WORM** | Registro append-only de decisões (sem conteúdo) |
| **Gestão de acessos** | RBAC, Entra ID, princípio do menor privilégio, MFA para admins |
| **Criptografia** | TLS ≥ 1.2 em trânsito; em repouso; segredos em cofre |
| **Segurança do LLM** | Contrato sem treino/retenção; proteção contra *prompt injection*; filtragem de saída |
| **SBOM e dependências** | SPDX/CycloneDX; varredura de vulnerabilidades |
| **Resposta a incidentes** | Plano de notificação (ANPD/titulares) e contenção |

## 3. Tarefas

1. Mapa de dados e classificação (o que é dado sensível, o que nunca é guardado).
2. Modelo de ameaças (STRIDE) com foco em **adversário próximo**: agressor com acesso físico ao aparelho.
3. Definir prazos de guarda da sessão (cookie e servidor) no RIPD; implementar; teste de expurgo (nada resta após `DELETE` nem após o vencimento).
4. Cifrar o histórico da conversa em repouso; sessões fora dos backups.
5. Logging seguro: teste automatizado que falha se corpo de mensagem ou valor do cookie aparecem em logs.
6. Redigir consentimento e termos em linguagem simples (incluindo o prazo de guarda da conversa); revisar com jurídico.
7. Redigir RIPD e definir papéis (controlador/operador) — dependência do MPRS.
8. Configurar RBAC + Entra ID para painéis; MFA.
9. Revisão do contrato/configuração do provedor de LLM e STT (retenção zero, sem treino, região).
10. Rotina de SBOM e `dependency scan` na CI.
11. Testes de segurança: SAST/DAST básicos, revisão de OWASP Top 10 e OWASP para LLM, testes do cookie (atributos, CSRF, revogação).
12. Plano de incidentes.

## 4. Checklist "adversário próximo"
- Nada do chat em histórico, cache, favoritos, autofill, notificações, capturas de "recentes".
- No aparelho, só as notas de fachada e **um cookie de sessão** com nome neutro, `HttpOnly`, em domínio neutro.
- A conversa salva só aparece depois do gatilho; "apagar conversa" e toque longo na saída removem tudo.
- Testar a "revista do celular" com a sessão persistida: o que alguém vê em configurações do navegador, histórico e app aberto?
- Ícone, nome e manifest neutros.
- Sem links/URLs reveladores; sem e-mails/SMS/push relacionados.
- Aviso honesto: "nenhum app é 100% invisível".

## 5. Critérios de pronto
- RIPD redigido; retenção implementada e testada.
- Sem PII em logs comprovado por teste.
- SBOM gerado na CI; vulnerabilidades críticas zeradas.
- Modelo de ameaças revisado com pelo menos uma pessoa externa.

## 6. Riscos
- Prometer sigilo que não existe → texto honesto sobre limites.
- Sessão persistida exposta a quem pegar o aparelho → prazo curto, gatilho/PIN para retomar, apagar fácil, consentimento que explica o risco.
- Provedor de nuvem retém dado → cláusulas contratuais ou modelo hospedado.
- Conflito entre sigilo e dever de proteger (risco iminente) → decisão jurídica registrada (D6).
