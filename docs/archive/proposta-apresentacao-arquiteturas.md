# Proposta para apresentação das arquiteturas

## Objetivo da apresentação

Apresentar a arquitetura do assistente em um nível abstrato, sem assumir que uma implementação específica já foi escolhida. A ideia é mostrar que memória, classificação, recuperação de conhecimento e geração de resposta são blocos substituíveis, que podem ser avaliados separadamente.

O projeto pode começar com uma solução mínima e incorporar novos módulos apenas quando os experimentos demonstrarem ganho de qualidade, segurança ou auditabilidade.

## Fluxo abstrato

Uma representação inicial possível seria:

```text
Prompt → Memória → Classificadores / RAG → Elaboração da resposta → Resposta
```

Para deixar mais clara a responsabilidade de cada módulo, propõe-se a seguinte formulação:

```text
Mensagem atual + memória anterior
                │
                ▼
       Compreensão e decisão
                │
                ▼
     Recuperação de conhecimento
                │
                ▼
      Elaboração da resposta
                │
                ▼
 Resposta + atualização da memória
```

Essa formulação evita colocar classificação e RAG como se fossem a mesma operação:

- **Compreensão e decisão:** identifica intenção, possíveis tipos de violência, urgência, lacunas de informação e próxima ação.
- **Recuperação de conhecimento:** busca informações jurídicas, definições e serviços em fontes verificadas.
- **Elaboração da resposta:** transforma o estado da conversa e os resultados dos módulos em uma resposta acolhedora.

Classificação e recuperação podem ser opcionais. Nem toda mensagem precisa passar por todos os módulos.

## Baseline conversacional mínimo

O primeiro baseline pode ser deliberadamente simples:

```text
Mensagem + memória recente
          │
          ▼
       Uma LLM
          │
          ▼
       Resposta
```

A mesma chamada recebe as instruções, a memória e a mensagem atual. A LLM interpreta a situação e responde diretamente, sem RAG, classificador externo ou sistema de agentes.

### Vantagens

- implementação rápida;
- baixa complexidade de integração;
- referência inicial de latência e qualidade;
- permite observar o que uma LLM local consegue fazer sozinha;
- facilita medir o ganho real dos módulos adicionados posteriormente.

### Limitações

- menor controle sobre decisões;
- dificuldade para explicar por que uma rota foi escolhida;
- ausência de fontes verificadas para afirmações jurídicas;
- risco de respostas inconsistentes;
- classificação e resposta podem falhar juntas, pois dependem do mesmo modelo.

Esse desenho deve ser apresentado como **baseline experimental**, e não como sistema pronto para uso real.

## Opções para a memória

O módulo de memória também pode evoluir gradualmente:

```text
Sem memória
    ↓
Últimas mensagens
    ↓
Resumo da conversa
    ↓
Resumo + fatos estruturados
```

### Alternativas

| Opção | Vantagem | Limitação |
| --- | --- | --- |
| Sem memória | Implementação mínima | Perde informações entre turnos |
| Últimas mensagens | Simples e preserva o texto original | Contexto cresce e fatos antigos desaparecem |
| Resumo | Reduz o contexto | Pode omitir ou distorcer fatos críticos |
| Resumo + fatos estruturados | Preserva evidências e correções | Exige atualização e validação da memória |

O projeto já experimentou o uso de formulários completos no contexto. Essa abordagem aumentou excessivamente o tamanho da entrada e prejudicou o desempenho. A memória híbrida busca um equilíbrio entre preservar informações e respeitar os limites dos modelos locais.

## Opções para compreensão e decisão

Essa é a principal área de comparação experimental.

| Opção | Funcionamento | Principal vantagem | Principal limitação |
| --- | --- | --- | --- |
| Sem classificação explícita | A LLM interpreta e responde diretamente | Simplicidade | Pouca auditabilidade |
| LLM classificadora | A LLM devolve intenção, urgência e tipos em JSON | Não exige dataset de treino | Pode variar e errar o contrato |
| System One | Kev, OpenJev ou equivalente pontua perguntas tipadas | Decisões probabilísticas em uma passagem | Desempenho em português ainda precisa ser validado |
| Classificador tradicional | BERTimbau, SVM ou outro modelo treinado | Métricas e limiares controláveis | Exige dataset representativo |
| Arquitetura híbrida | Combina LLM, System One, regras ou classificador | Permite segunda opinião | Aumenta custo e complexidade |
| Agente com ferramentas | A LLM escolhe a próxima ação e as ferramentas | Fluxo flexível | Depende mais da capacidade da LLM |

Os resultados de classificação continuam sendo indícios para organizar o fluxo. Eles não representam conclusão jurídica, policial ou clínica.

## Opções para recuperação de conhecimento

O RAG responde à pergunta:

> De onde vêm as informações jurídicas, as definições e os serviços recomendados?

### Alternativas

| Opção | Funcionamento |
| --- | --- |
| Sem RAG | A LLM usa somente o conhecimento armazenado no modelo |
| Busca lexical | BM25 recupera documentos com base nos termos da consulta |
| Busca densa | FAISS recupera documentos por similaridade semântica |
| Busca híbrida | Combina BM25 e FAISS |
| RAG como ferramenta | Um agente consulta a base somente quando identifica necessidade |

O RAG não precisa executar em toda mensagem. Um relato pode exigir acolhimento e uma pergunta de segurança. Uma pergunta sobre medida protetiva exige recuperação de fontes jurídicas.

Para uma primeira implementação, SQLite para documentos e metadados, BM25 para busca lexical e FAISS para busca densa formam uma alternativa simples. Um serviço como Qdrant pode ser considerado quando o volume, os filtros ou as atualizações simultâneas justificarem sua adoção.

## Opções para elaboração da resposta

A geração da resposta também pode evoluir por etapas:

```text
LLM livre
    ↓
LLM com persona e instruções
    ↓
LLM com resultados da classificação
    ↓
LLM fundamentada pelos documentos do RAG
    ↓
Templates críticos + LLM para o restante
```

Templates são especialmente relevantes para mensagens de emergência, telefones, avisos e orientações que não podem variar livremente. A LLM pode ser usada para o acolhimento e para adaptar a linguagem ao contexto.

## Arquiteturas que podem ser comparadas

### Arquitetura A — Baseline mínimo

```text
Mensagem + memória → LLM → resposta
```

É a referência mais simples e rápida de implementar.

### Arquitetura B — LLM estruturada

```text
Mensagem + memória
        ↓
LLM identifica rótulos e fatos
        ↓
LLM elabora a resposta
```

Pode usar uma chamada com saída estruturada e resposta, ou duas chamadas separadas.

### Arquitetura C — Pipeline modular

```text
Mensagem + memória
        ↓
Classificadores
        ↓
RAG quando necessário
        ↓
LLM elabora a resposta
```

É mais auditável, mas exige mais componentes e integração.

### Arquitetura D — Agente com ferramentas

```text
Mensagem + memória
        ↓
LLM decide o que precisa
        ↓
Ferramentas: risco, RAG, serviços e transbordo
        ↓
LLM elabora a resposta
```

Uma única LLM com estado, ferramentas e um laço de execução já constitui um agente. Não é necessário começar com vários agentes especializados.

### Arquitetura E — Agente híbrido

```text
LLM agente
   +
System One como verificador
   +
regras determinísticas para casos críticos
```

O modelo System One pode começar em modo sombra, registrando divergências sem controlar a resposta. Sua influência sobre a política só deve ser habilitada depois de avaliação em um conjunto revisado.

## Comparação resumida

| Arquitetura | Complexidade | Dados próprios | Auditabilidade | Flexibilidade |
| --- | --- | --- | --- | --- |
| Baseline mínimo | Baixa | Não | Baixa | Média |
| LLM estruturada | Baixa a média | Não | Média | Média |
| Pipeline modular | Alta | Possivelmente | Alta | Média |
| Agente com ferramentas | Média a alta | Não para iniciar | Média | Alta |
| Agente híbrido | Alta | Teste revisado | Alta | Alta |

## Estratégia experimental

A arquitetura não precisa ser escolhida integralmente antes dos experimentos. Uma evolução possível é:

1. Implementar uma LLM com memória recente e resposta direta.
2. Solicitar classificação estruturada à mesma LLM.
3. Adicionar RAG somente para perguntas que exigem conhecimento externo.
4. Comparar a classificação da LLM com System One.
5. Testar o uso de ferramentas e planejamento agêntico.
6. Treinar classificadores próprios apenas se houver dados e uma lacuna demonstrada.

Cada módulo deve ser mantido somente quando demonstrar ganho mensurável em relação à versão anterior.

### Métricas possíveis

- falsos negativos de urgência imediata;
- precisão e recall por tipo de violência;
- acerto de intenção;
- preservação de fatos críticos na memória;
- seleção correta de ferramentas;
- fidelidade da resposta aos documentos recuperados;
- taxa de respostas sem fonte quando uma fonte era necessária;
- latência, uso de tokens e memória da GPU;
- taxa de transbordo adequado;
- avaliação humana de clareza e acolhimento.

## Sequência sugerida para os slides

### Slide 1 — Problema

Acolher, compreender relatos e oferecer informação segura usando hardware limitado e modelos abertos.

### Slide 2 — Fluxo abstrato

Memória, compreensão, recuperação de conhecimento e elaboração da resposta.

### Slide 3 — Baseline mínimo

Uma LLM com memória, sem RAG e sem classificadores externos.

### Slide 4 — Opções de compreensão

LLM, System One, classificadores tradicionais, híbridos e agente.

### Slide 5 — Opções de conhecimento

Sem RAG, BM25, FAISS, busca híbrida e RAG como ferramenta.

### Slide 6 — Arquiteturas possíveis

Comparação entre baseline, LLM estruturada, pipeline modular e agente híbrido.

### Slide 7 — Estratégia experimental

Começar simples e adicionar módulos somente quando produzirem ganho mensurável.

### Slide 8 — Próximos passos

Revisar o corpus, testar o baseline conversacional, avaliar RAG e comparar alternativas de classificação.

## Mensagem central

> O sistema é composto por blocos substituíveis. O experimento começa com uma LLM e memória. Classificadores, System One, RAG e ferramentas são adicionados e mantidos apenas quando produzem ganhos mensuráveis.

Essa apresentação permite discutir as propostas do grupo como alternativas experimentais, sem exigir uma decisão prematura sobre a arquitetura final.
