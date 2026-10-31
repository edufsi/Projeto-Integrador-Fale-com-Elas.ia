# Notas.ia — Plano de Ação (arquivo base)

> Arquitetura do agente: [agente.md](agente.md). Este arquivo organiza a **execução**; cada etapa tem seu plano detalhado.
> Primeira vez aqui? Comece pela [visão geral](visao-geral.md), um tour amigável por todos os módulos.
> Duas entregas acadêmicas: **Projeto Integrador (PI)** = projeto inteiro; **PLN** = recorte do RAG jurídico ([E4-plano-rag.md](E4-plano-rag.md)).

## 1. Etapas e planos detalhados

| Cód. | Etapa | Plano | Dono provável | Entra no PLN? |
|---|---|---|---|---|
| E0 | Fundamentos: fontes, especialistas, decisões abertas | [E0-plano-fundamentos.md](E0-plano-fundamentos.md) | Você + orientador | — |
| E1 | Backend, API e sessão | [E1-plano-backend-api.md](E1-plano-backend-api.md) | Você | — |
| E2 | Conversa: orquestrador, intenção, persona, guardrails | [E2-plano-conversa.md](E2-plano-conversa.md) | Você | — |
| E3 | Motor de risco (Violentômetro / FONAR / IAVP) | [E3-plano-risco.md](E3-plano-risco.md) | Você + especialista | — |
| E4 | Base de conhecimento jurídica (RAG) | [E4-plano-rag.md](E4-plano-rag.md) | Você | **Sim (núcleo)** |
| E5 | Rede de apoio e geolocalização | [E5-plano-rede-geo.md](E5-plano-rede-geo.md) | Você | — |
| E6 | Voz e canais (STT) | [E6-plano-voz.md](E6-plano-voz.md) | Você | Opcional |
| E7 | Interface (app de notas camuflado) | [E7-plano-interface.md](E7-plano-interface.md) | Você | — |
| E8 | Privacidade, segurança e conformidade | [E8-plano-privacidade-seguranca.md](E8-plano-privacidade-seguranca.md) | Você | — |
| E9 | Avaliação e qualidade | [E9-plano-avaliacao.md](E9-plano-avaliacao.md) | Você | Parcial |
| E10 | Infra, CI/CD e operação | [E10-plano-infra.md](E10-plano-infra.md) | Você | — |

## 2. Dependências entre etapas

```
E0 ─┬─► E3 (itens e pesos oficiais)
    ├─► E4 (corpus e revisão jurídica)
    └─► E5 (base de serviços)

E1 ─► E2 ─► E7        E2 depende de E3, E4, E5 (como ferramentas)
E3, E4, E5 ─► E2      E6 ─► E1/E2 (entrada de áudio)
E8 percorre todas     E9 percorre todas (suítes de teste nascem junto)
E10 começa cedo (repo, CI) e fecha no fim
```

**Caminho crítico:** E0 → E3/E4 → E2 → E7 → E9. Sem itens oficiais do FONAR e corpus jurídico curado, o resto fica sem conteúdo.

## 3. Fases (sem datas; ajustar ao calendário das disciplinas)

| Fase | Objetivo | Etapas | Critério de saída |
|---|---|---|---|
| **F0 Fundação** | Fontes, decisões, repositório e esqueleto | E0, E1 (esqueleto), E10 (repo/CI) | Decisões críticas fechadas; `POST /v1/session` responde em container |
| **F1 Núcleo seguro** | Emergência + risco funcionando sem LLM | E3, E2 (pré-filtro), E9 (vinhetas) | Suíte de vinhetas de emergência passa; score reproduzível |
| **F2 Conhecimento** | RAG com citações e abstenção | E4, E9 (gabarito RAG) | Recall@k e fidelidade medidos no dataset próprio |
| **F3 Conversa completa** | Fluxos, persona, guardrails, rede | E2, E5 | Conversa ponta a ponta em texto, no terminal/API |
| **F4 Interface** | App camuflado + chat + saída rápida | E7, E8 (ganchos) | Fluxo completo no navegador/celular |
| **F5 Voz** | Áudio e canais | E6 | WER medido |
| **F6 Endurecimento** | Red-team, LGPD, SBOM, carga, piloto | E8, E9, E10 | Relatório de avaliação final |

**Marco PLN:** F2 concentra o trabalho de PLN; o relatório dele sai ao fim da F2 e alimenta o PI.

## 4. Módulos-chave transversais

| Módulo | Onde vive | Usado por |
|---|---|---|
| Configurações versionadas (itens, pesos, templates) | `/config` | E2, E3, E5 |
| Corpus jurídico versionado | `/knowledge` | E4, E2 |
| Base de serviços versionada | `/data/servicos` | E5 |
| Contrato de API (OpenAPI) | `/api` | E1, E7, E6 |
| Suítes de teste (vinhetas, gabaritos) | `/eval` | E9, todas |
| Registro de versões (regras, corpus, modelo, prompt) | metadados de toda resposta | E8, E9 |

## 5. Estrutura de repositório sugerida

```
notas-ia/
├─ agente.md, plano.md, E0…E10-plano-*.md
├─ api/            # FastAPI, contratos OpenAPI
├─ core/           # orquestrador, intenção, guardrails
├─ risk/           # motor de risco + config
├─ rag/            # ingestão, índices, recuperação, rerank
├─ network/        # serviços e geo
├─ speech/         # STT
├─ web/            # interface (PWA)
├─ config/         # YAML versionado
├─ knowledge/      # corpus curado
├─ eval/           # gabaritos, notebooks, relatórios
├─ infra/          # Docker, IaC, CI
└─ docs/
```

## 6. Riscos de projeto e mitigação

| Risco | Mitigação |
|---|---|
| Escopo grande para um prazo acadêmico | Fatiar por fases; F1–F4 é a MVP; voz e piloto são "se der" |
| Falta de acesso a especialistas/itens oficiais | Iniciar E0 já; usar textos públicos; marcar claramente o que é provisório |
| Conteúdo sensível sem validação | Nada vai para uso real sem revisão; entrega acadêmica é **protótipo**, não serviço em produção |
| Dependência de API de LLM (custo/indisponibilidade) | Camada de abstração + modelo alternativo; cache em desenvolvimento |
| Perda de foco entre PI e PLN | Interface clara entre os dois (ver [E4-plano-rag.md](E4-plano-rag.md) §2) |

## 7. Definição de pronto (global)

- Todas as respostas trazem versão de regras, corpus, modelo e prompt.
- Zero afirmação jurídica sem citação ou abstenção explícita.
- Emergência: 100% de recall nas vinhetas críticas.
- Sessão apagável por completo em uma chamada.
- SBOM gerado e imagem Docker reproduzível.

## 8. Pontos em aberto herdados (ver [E0-plano-fundamentos.md](E0-plano-fundamentos.md))

IAVP incluso? Versão do Violentômetro? Especialistas revisores? LLM em nuvem vs. hospedado? O que é o 153? Escopo geográfico? Prazo de guarda da sessão por cookie? Idiomas?
