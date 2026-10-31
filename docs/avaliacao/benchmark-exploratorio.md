# Benchmark sintético exploratório

Este conjunto contém 60 mensagens revisadas por uma pessoa. Ele serve para experimentos empíricos, comparação de modelos e desenvolvimento da futura API de conversação. Não deve ser apresentado como teste ouro ou como estimativa de desempenho em atendimento real.

## Campos consultáveis

- `intencao`: objetivo principal da mensagem atual;
- `tipos_com_indicio`: seis booleanos para indícios positivos sustentados pelo contexto;
- `tipos_presentes`: lista compacta dos tipos positivos;
- `tipos_mencionados`: tipos positivos ou discutidos como assunto, mesmo quando negados ou apenas conceituais;
- `urgencia`: estado de risco conhecido;
- `acao_esperada`: próximo comportamento operacional principal.

`tipos_com_indicio` é o alvo de classificação. `tipos_mencionados` pode orientar recuperação de conhecimento, mas não deve ser interpretado como ocorrência de violência.

## Estado arquivado

O construtor experimental foi removido da árvore executável após a consolidação do MVP.
As saídas revisadas foram preservadas em `data/archive/evaluation-corpus/`:

- `benchmark_exploratorio.json`: formato completo;
- `benchmark_exploratorio.csv`: tabela para inspeção;
- `benchmark_exploratorio_report.json`: concordância, distribuições e resoluções.

As anotações originais permanecem intactas. Seis divergências centrais foram resolvidas explicitamente em `single_review_resolutions.json`, com justificativa por campo.

O JSON completo continua consultável por `intencao`, `tipos_presentes`,
`tipos_mencionados`, `acao_esperada` e `urgencia`. Um novo executor de benchmark deverá
consumi-lo como dado, sem depender do antigo módulo `evaluation_corpus`.

## Resultado da revisão

- intenção: 100% de concordância com a proposta;
- urgência: 100%;
- vetor de tipos: 95%;
- ação: 95%;
- conjunto principal completo: 90%.

Das 15 diferenças de evidência, 13 tiveram cobertura equivalente por outro trecho ou por extensão diferente. Evidência é preservada para auditoria, mas não faz parte do alvo mínimo deste benchmark.
