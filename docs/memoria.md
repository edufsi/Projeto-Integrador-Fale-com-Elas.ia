# Módulo de memória

## 1. Problema

Repassar toda a conversa e formulários completos aumenta custo, ocupa contexto e prejudica modelos locais. Usar somente um resumo é frágil: detalhes críticos podem desaparecer, negações podem ser incorporadas incorretamente e o texto deixa de mostrar de onde veio cada informação.

A solução proposta combina uma narrativa curta com fatos estruturados e mantém o histórico bruto fora do contexto dos modelos.

## 2. Três camadas

### Histórico bruto

Sequência imutável das mensagens originais, usada para auditoria autorizada, reconstrução e avaliação. Não é reenviada integralmente a cada turno.

### Memória de trabalho

Entregue aos modelos. Possui:

- resumo narrativo curto;
- até 12 fatos ativos;
- no máximo 700 tokens;
- referências ao turno e evidência literal.

### Registro de deltas

Guarda cada proposta e resultado da atualização: fatos adicionados, fatos revogados, validações rejeitadas, modelo e latência. Isso permite reproduzir como a memória chegou ao estado atual.

## 3. Estrutura de um fato

```json
{
  "id": "t3f2",
  "afirmacao": "O ex-companheiro informou que a esperaria na saída.",
  "tempo": "futuro",
  "turno": 3,
  "trecho": "ele disse que vai me esperar na saída hoje",
  "critico": true,
  "estado": "ativo"
}
```

`afirmacao` é uma paráfrase curta. `trecho` precisa ser uma substring literal da mensagem de origem. O fato não deve incorporar uma classificação jurídica.

## 4. Atualização por delta

A LLM recebe memória anterior, até duas mensagens recentes e mensagem atual. Ela propõe:

```json
{
  "resumo": "...",
  "revogar_ids": ["t1f1"],
  "novos_fatos": [
    {
      "afirmacao": "...",
      "trecho": "...",
      "tempo": "atual",
      "critico": true
    }
  ]
}
```

O código aplica o delta somente após validar:

- existência literal do trecho na mensagem atual;
- enumeração temporal válida;
- existência do identificador revogado;
- ausência de duplicação;
- limite de fatos e tokens.

Quando ocorre correção explícita, o fato anterior é revogado, não apagado do registro de deltas. A memória ativa deixa de mostrá-lo. O resumo deve ser reconstruído para não preservar a afirmação corrigida.

## 5. Temporalidade e contradição

Valores temporais iniciais:

- `passado`;
- `atual`;
- `futuro`;
- `nao_informado`.

Uma versão posterior pode incluir intervalo, recorrência e validade, desde que isso seja extraído explicitamente. Expressões como “ontem”, “agora” e “na próxima semana” devem ser preservadas na evidência; converter para uma data absoluta exige registrar a data de referência.

Negação não é ausência. “Ele não está aqui agora” pode corrigir perigo atual sem revogar uma agressão anterior. Revogação só ocorre quando a mensagem contradiz explicitamente o fato correspondente.

## 6. Fatos críticos

O marcador crítico indica que a perda do fato pode prejudicar a triagem. Exemplos para avaliação inicial:

- ameaça explícita;
- arma;
- estrangulamento ou sufocamento;
- violência sexual;
- perseguição e presença atual;
- perigo contra filhos ou rede de apoio;
- impossibilidade de sair ou pedir ajuda;
- ideação suicida relatada.

Essa lista é uma heurística de engenharia e precisa de revisão profissional. Fatos críticos podem ultrapassar o limite de 12; nesse caso, o sistema registra erro de capacidade e não remove silenciosamente nenhum deles.

## 7. Empacotamento para modelos

O estado comum contém memória anterior, até duas mensagens recentes e mensagem atual, com alvo máximo de 1.536 tokens.

Ordem de redução:

1. remover a mensagem recente mais antiga;
2. encurtar o resumo;
3. remover fatos não críticos mais antigos;
4. se ainda exceder, registrar o turno como não avaliável.

A mensagem atual e fatos críticos nunca são cortados silenciosamente.

## 8. Memórias usadas na avaliação

Cada classificador é testado em três condições:

- **sem memória:** somente mensagens recentes e atual;
- **memória de referência:** fatos anotados manualmente no corpus;
- **memória Qwen:** memória produzida pelo atualizador local.

Isso separa erro do classificador de erro acumulado pelo módulo de memória.

## 9. Métricas

- fatos críticos preservados;
- fatos inventados;
- evidências inválidas;
- correções aplicadas corretamente;
- correções que removeram informação válida;
- fatos duplicados;
- memória acima do orçamento;
- latência por atualização;
- estabilidade do resumo entre turnos;
- impacto da memória nas métricas de classificação.

Comparação literal de evidências é auditável, mas não mede equivalência semântica. A análise final deve inspecionar os casos individualmente.

## 10. Melhorias futuras

- extrator menor especializado em fatos e relações;
- detecção determinística de datas relativas;
- memória episódica recuperada por relevância;
- grafo de entidades com identidades incertas;
- consolidação periódica supervisionada;
- políticas diferentes de retenção para pesquisa e atendimento.

