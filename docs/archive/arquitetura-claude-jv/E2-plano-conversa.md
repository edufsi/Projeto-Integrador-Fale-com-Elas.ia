# E2 — Conversa: orquestrador, intenção, persona e guardrails

← [plano.md](plano.md) · Arquitetura: [agente.md](agente.md) §4, §5, §9

## 1. Objetivo
Conduzir a conversa de forma empática e segura, chamando risco, RAG e rede como **ferramentas**, e barrando qualquer saída que viole as regras.

## 2. Módulos-chave

| Módulo | Responsabilidade |
|---|---|
| **Pré-filtro de segurança** | Roda em **toda** mensagem, antes do LLM: detecta emergência/autolesão por regras + classificador leve |
| **Protocolo de emergência** | Resposta curta com ações (190/180/153*); marca sessão `CRÍTICO`; suspende questionário |
| **Detector de intenção** | `emergencia · relato · duvida · orientacao_geral · ambigua`, com reclassificação a cada turno |
| **Máquina de estados** | Fluxos: acolhimento → triagem → informação → encaminhamento → encerramento; retomada de sessão |
| **Extrator de fatos** | LLM → JSON com trecho de evidência; itens marcados "inferido — confirmar" |
| **Gerador de resposta** | LLM com persona; temperatura baixa; usa templates fixos nos trechos críticos |
| **Biblioteca de templates** | Textos aprovados: emergência, plano de segurança, avisos, consentimento |
| **Guardrails de saída** | Verificação de citações, telefones só de tabela, lista "nunca faça", juiz de fidelidade |
| **Camada de ferramentas** | Interface única para risco (E3), RAG (E4), rede (E5) |
| **Abstração de LLM** | Troca de provedor/modelo sem mexer no fluxo |

\* 153: confirmar significado com o MPRS antes de exibir.

## 3. Fluxos principais

1. **Início:** consentimento curto + aviso "sou uma IA" → pergunta aberta.
2. **Relato:** acolhe → pede licença → triagem adaptativa (E3) → apresenta nível → oferece caminhos.
3. **Dúvida:** RAG (E4) com citação → resumo simples → "quer saber mais?".
4. **Orientação geral:** rede (E5) por localização opcional.
5. **Emergência:** a qualquer momento, prioridade absoluta.
6. **Encerramento:** resumo opcional, lembrete de saída rápida, porta aberta para voltar.

## 4. Tarefas

1. Escrever a persona e a lista "nunca faça" como **testes** (cada regra vira caso automatizado).
2. Implementar o pré-filtro e a suíte de vinhetas de emergência (com [E9-plano-avaliacao.md](E9-plano-avaliacao.md)).
3. Definir esquema JSON de saída do LLM (`reply`, `citations`, `confidence`, `next_action`).
4. Máquina de estados com persistência na sessão e reentrada.
5. Detector de intenção (LLM estruturado + fallback por regras) e conjunto rotulado.
6. Extrator de fatos com confirmação obrigatória antes de pontuar.
7. Guardrails: bloqueio de números não tabelados, verificador de citações, juiz de fidelidade.
8. Templates aprovados (com revisor de tom).
9. Testes de tom com rubrica (não revitimização, sem julgamento, sem infantilizar).
10. Red-team: *prompt injection*, tentativas de conselho perigoso, tentativa de extrair dados.

## 5. Regras de projeto
- Regras críticas ficam **no código**, não só no prompt.
- Um turno = no máximo 1 pergunta (2 curtas).
- Abstenção é resposta válida.
- Todo desvio (regeneração, bloqueio) vai para o log de decisão.

## 6. Critérios de pronto
- Recall de emergência ~100% nas vinhetas.
- Nenhum telefone/endereço fora da tabela verificada em N conversas simuladas.
- Revisão de tom aprovada por especialista (ou marcada "não validada").

## 7. Riscos
- Modelo "sai do personagem" → guardrails de saída e testes de regressão a cada mudança de prompt/modelo.
- Perguntas em excesso cansam/assustam → limite por turno, permitir pular e pausar.
