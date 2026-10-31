# E9 — Avaliação e qualidade

← [plano.md](plano.md) · Arquitetura: [agente.md](agente.md) §11

## 1. Objetivo
Provar com números que o agente é seguro: não erra orientação, não subestima risco, não revitimiza. As suítes nascem **junto** com cada módulo.

## 2. Módulos-chave

| Módulo | Conteúdo | Etapa dona |
|---|---|---|
| **Vinhetas de emergência** | Casos sintéticos com gatilhos críticos, formas diretas e indiretas | E2 |
| **Vinhetas de risco** | Casos com nível esperado, revisados por especialista | E3 |
| **Gabarito RAG** | Pergunta → artigos relevantes (dataset do PLN) | E4 |
| **Conjunto de intenções** | Frases rotuladas nas 5 classes | E2 |
| **Conjunto de STT** | Áudios + transcrição de referência | E6 |
| **Rubrica de tom** | Escala para não revitimização, empatia, clareza | E2 |
| **Red-team** | Ataques, conselhos perigosos, injeção | E2/E8 |
| **Runner de avaliação** | Executa suítes, gera relatório por versão | E9 |
| **Dashboard de regressão** | Compara versões de modelo/prompt/regras/corpus | E9 |

## 3. Métricas e metas (iniciais, ver agente.md §11)

| Métrica | Meta |
|---|---|
| Alucinação (HAM) | ≤ 10% (interno ≤ 3% em jurídico) |
| Fidelidade às fontes | ≥ 95% |
| Recall de emergência | ~100% |
| Sensibilidade ALTO/CRÍTICO | definir com especialista |
| Intenção | ≥ 90% |
| WER | ≤ 10% |
| Abstenção correta | monitorar |
| Latência p95 | poucos segundos |

## 4. Tarefas

1. Criar o runner (`eval/`) com versionamento dos resultados.
2. Construir vinhetas e conjuntos (junto de cada etapa).
3. Definir rubrica de tom e pedir avaliação a especialistas.
4. Fixar versões (modelo, prompt, regras, corpus) e rodar avaliação a cada mudança (CI).
5. Rodar red-team estruturado (checklist de ataques) e registrar falhas/correções.
6. Revisão humana por amostragem de conversas simuladas.
7. Relatório final com limitações e o que **não** foi validado.

## 5. Critérios de pronto
- Toda mudança de prompt/modelo/regras gera relatório comparativo.
- Nenhum bloqueador aberto de emergência ou de orientação errada.
- Relatório final honesto sobre limites.

## 6. Riscos
- Avaliação "de mentira" (vinhetas fáceis) → incluir casos difíceis e adversos.
- Sem revisão especializada → registrar como limitação, não vender como validado.
