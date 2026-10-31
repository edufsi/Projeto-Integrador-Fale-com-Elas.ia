# E3 — Motor de risco (Violentômetro / FONAR / IAVP)

← [plano.md](plano.md) · Arquitetura: [agente.md](agente.md) §6

## 1. Objetivo
Transformar respostas confirmadas em **nível de risco reproduzível e auditável**, com pisos por gatilho crítico. É código determinístico; o LLM não pontua.

## 2. Módulos-chave

| Módulo | Responsabilidade |
|---|---|
| **Banco de itens** (`config/itens.yaml`) | Cada item: `id`, fonte, texto oficial, reformulação empática aprovada, tipo de resposta, peso, dimensão, `gatilho_critico` |
| **Selecionador de perguntas** | Próxima pergunta por relevância; pula respondidas; sensíveis depois do vínculo; para em gatilho crítico |
| **Registro de respostas** | `sim / não / não sei / prefiro não responder`, com origem (direta ou inferida-confirmada) |
| **Motor de pontuação** | Soma ponderada + pisos por gatilho + confiança → `{score, nivel, confianca, fatores_criticos, dimensoes}` |
| **Mapeador de dimensões** | Física, psicológica, sexual, patrimonial, moral (Art. 7º Lei 11.340) e dimensões do IAVP |
| **Reavaliador** | Recalcula a cada nova informação; guarda histórico para detectar escalada |
| **Apresentador** | Traduz o resultado para linguagem cidadã + degrau do Violentômetro (nunca número frio) |
| **Versionamento** | `versao_regras` em toda saída |

## 3. Tarefas

1. **Transcrever** itens do FONAR (texto oficial), Violentômetro e IAVP (se D1 = sim) para o YAML, com `fonte` e trecho original.
2. Escrever reformulações empáticas (rascunho) → **revisão por especialista**.
3. Propor **estrutura** de pesos/faixas e enviar ao revisor para definição dos valores (não decidir sozinha).
4. Implementar o motor puro (sem dependência de LLM) com testes unitários.
5. Implementar pisos: gatilho crítico define nível mínimo.
6. Confiança: muitos "não sei" ⇒ estimativa + encaminhamento conservador (nível acima).
7. Selecionador adaptativo e integração com o extrator (E2).
8. Vinhetas gabaritadas (com o revisor): casos com nível esperado.
9. Métricas: sensibilidade em ALTO/CRÍTICO, matriz de confusão, análise de falsos negativos.
10. Endpoint `GET /v1/session/risk` e formato para a interface desenhar o Violentômetro.

## 4. Regras de projeto
- **Nunca** subestimar: preferir falso positivo a falso negativo.
- Itens e pesos **provisórios** ficam rotulados `provisorio: true` até validação.
- Escore é apoio à decisão, nunca diagnóstico ou sentença; isso aparece na UI e nos termos.
- Mudança de regra = nova versão + rodar toda a suíte de vinhetas.

## 5. Critérios de pronto
- Mesma entrada ⇒ mesma saída (teste de determinismo).
- 100% das vinhetas com gatilho crítico devolvem nível ≥ mínimo esperado.
- Todo item tem fonte rastreável.

## 6. Riscos
- Pesos sem validação → rotular como "protótipo"; não usar em produção real.
- Instrumento oficial protegido/inacessível → registrar limitação e usar versão pública.
- Perguntas demais → medir tempo/abandono no piloto e reduzir.
