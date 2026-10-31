# E5 — Rede de apoio e geolocalização

← [plano.md](plano.md) · Arquitetura: [agente.md](agente.md) §8

## 1. Objetivo
Encaminhar a usuária ao serviço certo, perto dela, com dados **verificados e datados**, sem expô-la.

## 2. Módulos-chave

| Módulo | Responsabilidade |
|---|---|
| **Base de serviços** | DEAMs, delegacias, CRAS, CREAS, Defensoria, Juizados/Varas de violência doméstica, casas-abrigo, Patrulha Maria da Penha, saúde |
| **Esquema de dados** | Nome, tipo, endereço, coordenadas, telefone, horário, atende sem agendamento, `verificado_em`, fonte |
| **Localizador** | Entrada: CEP / cidade-bairro / geolocalização (consentida); busca por proximidade |
| **Roteador por risco** | Nível de risco → tipos de serviço prioritários (tabela do agente.md §8) |
| **Mapa município → promotoria** | Atribuição territorial (requisito do desafio); API para o MPRS |
| **Verificador de atualidade** | Marca dados vencidos; sempre oferece 180 como alternativa |
| **Plano de segurança** | Conteúdo aprovado, selecionado e ordenado pelo agente |
| **Apresentador** | Endereço/telefone/rota exibidos no chat, sem gerar rastro fora dele |

## 3. Tarefas

1. Definir escopo geográfico (D4) e fontes por município: sites do MPRS, SSP-RS, Defensoria, prefeituras, SUAS.
2. Coletar dados do escopo; validar por telefone/site oficial; registrar `verificado_em`.
3. Modelagem em Postgres/PostGIS; script de carga versionado.
4. Geocodificação (endereço → coordenadas) e busca por raio.
5. Roteador por risco (regras em YAML).
6. Endpoint `GET /v1/network` e ferramenta para o orquestrador.
7. Regra de segurança: nada de "enviar por SMS/e-mail/notificação" que fique visível no aparelho.
8. Plano de segurança: redação com o revisor; seletor no código.
9. Rotina de revisão periódica dos dados e alerta de vencimento.

## 4. Critérios de pronto
- Para o município-piloto: cobertura completa das categorias, todas com `verificado_em`.
- Busca por CEP/cidade devolve serviço correto em casos de teste.
- Nenhum serviço apresentado sem data de verificação e sem fallback 180.

## 5. Riscos
- Dados desatualizados são perigosos (ela vai a um lugar fechado) → datar, avisar, fallback.
- Geolocalização sensível → opcional, não persistida, consentimento explícito.
- Cobertura desigual no interior → dizer com transparência e priorizar canais remotos (180).
