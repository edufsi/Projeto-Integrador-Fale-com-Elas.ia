# E10 — Infra, CI/CD e operação

← [plano.md](plano.md) · Arquitetura: [agente.md](agente.md) §12–13

## 1. Objetivo
Entregar o sistema em containers, escalável horizontalmente, com pipeline que roda testes, avaliações, SBOM e varreduras a cada mudança.

## 2. Módulos-chave

| Módulo | Responsabilidade |
|---|---|
| **Repositório e branches** | Git, revisão de código, proteção da main |
| **Containers** | Dockerfiles por serviço (api, rag, web) em padrão OCI |
| **Orquestração local** | docker-compose para dev (API, Redis, Postgres/pgvector, web) |
| **CI** | Lint, testes, suítes de avaliação, SBOM, scan de vulnerabilidades |
| **CD** | Deploy em ambiente de homologação e (opcional) produção |
| **Infra como código** | Terraform/Bicep (Azure alinhado a Entra ID) ou equivalente |
| **Segredos** | Cofre (Key Vault ou similar); nada em repositório |
| **Escala** | Serviços stateless, Redis compartilhado, autoscaling |
| **Observabilidade** | Métricas, traços, alertas — **sem conteúdo sensível** |
| **Backups e expurgo** | Backup de corpus/serviços; nenhum backup de sessão |

## 3. Tarefas

1. Criar repositório com estrutura de [plano.md](plano.md) §5, README e guia de contribuição.
2. `docker-compose` com todos os serviços; ambiente reproduzível em um comando.
3. CI: lint + testes unitários + contrato de API.
4. Job de avaliação (vinhetas, gabarito RAG) com relatório anexado.
5. Geração de SBOM (SPDX/CycloneDX) e varredura de dependências e imagens.
6. Escolher nuvem (créditos oferecidos no desafio: Oracle, AWS, Microsoft, Cloudera) e provisionar homologação.
7. IaC para o ambiente; segredos em cofre.
8. Observabilidade sem PII (filtros e amostragem).
9. Teste de carga e de escala horizontal.
10. Runbook: implantação, rollback, incidentes.

## 4. Critérios de pronto
- `docker compose up` sobe o sistema completo.
- CI verde bloqueia merge; SBOM publicado por build.
- Escala de 1 para N instâncias sem perda de sessões.

## 5. Riscos
- Custo de nuvem/LLM → limites de uso, cache em dev, alertas de orçamento.
- Vazamento de segredos → scan de segredos na CI, rotação.
- Complexidade de infra desproporcional ao prazo → começar em compose e uma VM; Kubernetes só se sobrar tempo.
