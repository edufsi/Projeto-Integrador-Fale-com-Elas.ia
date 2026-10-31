# Avaliação e evolução

## 1. Perguntas de pesquisa

1. Quanto a memória melhora classificação em conversas com revelação tardia?
2. Quanto erro é introduzido pela memória gerada em comparação com fatos de referência?
3. Modelos System One apresentam melhor latência, calibração ou estabilidade que uma LLM generativa local?
4. Um encoder multilíngue pequeno, como Julia-1, é competitivo em português?
5. O ganho de um modelo maior justifica custo e complexidade no hardware disponível?
6. O RAG recupera fontes e serviços corretos sem depender de uma classificação perfeita?

## 2. Baseline histórico

O código desse baseline foi removido da árvore ativa durante a consolidação do MVP
agentivo. O corpus e os resultados foram preservados em `data/archive/baseline-corpus.json`
e `data/archive/baseline-results/`. O experimento continha:

- 24 roteiros artificiais com três variações cada;
- conversas de três turnos;
- seis roteiros base para desenvolvimento e 18 para teste;
- condições sem memória, memória de referência e memória Qwen;
- adaptadores para Qwen 3.5 4B, Kev-4B e NeoHorse;
- preflight de contexto;
- congelamento das entradas;
- métricas de classificação, memória, latência e VRAM.

O corpus inclui revelação tardia, múltiplos tipos, ambiguidades, negações, correções e mudança de urgência. Ele precisa de revisão humana antes de produzir resultados interpretáveis.

## 3. Protocolo experimental

### Preparação

1. revisar relatos e rótulos;
2. congelar divisão por roteiro base;
3. versionar corpus e prompts;
4. executar preflight de 1.536 tokens por modelo;
5. fixar quantização, runtime, versão e limiar;
6. ajustar somente no desenvolvimento;
7. abrir teste uma única vez para a análise principal.

### Execução

Os modelos são carregados sequencialmente. Entradas ficam congeladas em disco e são verificadas por hash. Cada resultado registra erro, tokens, latência e configuração.

Uma ordem possível:

1. Qwen e atualização de memória;
2. Kev;
3. Julia-1;
4. candidatos exploratórios;
5. consolidação de relatório.

Para evitar viés por aquecimento ou carga, fazer uma chamada de warm-up não pontuada e repetir medições de desempenho em ordem balanceada.

## 4. Métricas prioritárias

### Segurança

- falsos negativos de urgência imediata;
- recall de urgência imediata;
- perda de fatos críticos;
- falhas que viraram rótulo negativo;
- respostas que omitiram o fluxo de emergência.

### Classificação

- precisão, recall e F1 por tipo;
- macro F1;
- acurácia e confusão de intenção;
- acurácia e confusão de urgência;
- Brier score e calibração;
- consistência entre variações.

### Memória

- precisão e recall de fatos;
- preservação de evidência e origem;
- correções aplicadas;
- contradições ainda ativas;
- taxa de excesso do orçamento.

### Sistema

- cobertura;
- latência mediana e p95;
- tokens processados;
- pico de VRAM e RAM;
- tamanho em disco;
- falhas por backend.

### RAG e resposta

- recall@k;
- precisão por localidade;
- fidelidade e cobertura de citações;
- contatos inventados ou vencidos;
- clareza, acolhimento e utilidade;
- preferência de resposta por avaliadoras qualificadas.

## 5. Análise de erros

Cada erro deve ser atribuído à etapa predominante:

- informação ausente no relato;
- perda ou invenção da memória;
- montagem/truncamento do estado;
- erro do classificador;
- limiar inadequado;
- política de decisão;
- recuperação incorreta;
- geração não fundamentada;
- fonte desatualizada.

Sem essa decomposição, uma métrica final de resposta não informa onde melhorar o sistema.

## 6. Experimentos seguintes

### Experimento A — ampliar classificadores

Adicionar Julia-1 à rodada principal. Depois, testar OpenJev-4B, lev e Jebadiah sobre as entradas congeladas. NeoHorse mantém relatório separado de cobertura.

Em paralelo, comparar um piso TF-IDF com regressão logística, um encoder em português como BERTimbau e um encoder multilíngue como XLM-R. A estratégia de construção dos dados está descrita em [Dados para classificação](dados-classificacao.md).

### Experimento B — tamanhos de memória

Comparar, no desenvolvimento, limites como 256, 512 e 700 tokens. Medir o ponto em que contexto extra deixa de ajudar ou prejudica a classificação.

### Experimento C — ablação da memória

Remover separadamente resumo, fatos, evidências e mensagens recentes para identificar qual componente oferece ganho.

### Experimento D — recuperação sem geração

Criar perguntas artificiais com documentos e serviços esperados. Avaliar BM25, embeddings e recuperação híbrida antes de usar uma LLM de resposta.

### Experimento E — resposta fundamentada

Comparar template determinístico, Qwen local com RAG e revisão humana. Avaliar citações e utilidade sem uso com público real.

## 7. Critérios antes de avançar

Os valores devem ser definidos com pessoas especialistas; a arquitetura estabelece apenas o processo. Antes de integrar cada etapa, exigir:

- nenhuma falha silenciosa de tamanho;
- reprodução determinística das entradas;
- corpus revisado;
- erros críticos inspecionados individualmente;
- fontes oficiais versionadas;
- teste de ausência de informação;
- documentação das limitações por idioma e domínio.

Antes de qualquer piloto com pessoas reais, acrescentar revisão ética, jurídica, de proteção de dados, segurança, acessibilidade e operação de transbordo humano.

## 8. Ameaças à validade

- relatos sintéticos não reproduzem integralmente linguagem, hesitação e contexto de casos reais;
- variações automáticas podem ser fáceis demais ou semanticamente equivalentes de forma artificial;
- rótulos jurídicos exigem interpretação especializada;
- modelos treinados em inglês podem usar pistas lexicais frágeis em português;
- comparação com cobertura parcial favorece subconjuntos curtos;
- quantizações diferentes confundem efeito do modelo e da precisão;
- prompts ajustados repetidamente podem vazar características do teste;
- probabilidades podem parecer calibradas no conjunto pequeno por acaso.
