# Módulo de classificação

## 1. Objetivo

O módulo identifica indícios presentes no relato para apoiar recuperação, escolha de resposta e revisão humana. Ele não determina autoria, materialidade, diagnóstico ou enquadramento jurídico definitivo.

## 2. Saída comum

```json
{
  "tipos": {
    "fisica": false,
    "psicologica": true,
    "sexual": false,
    "patrimonial": false,
    "moral": false,
    "vicaria": false
  },
  "intencao": "informacao",
  "urgencia": "prioritaria"
}
```

### Tipos independentes

- física;
- psicológica;
- sexual;
- patrimonial;
- moral;
- vicária.

Mais de um tipo pode ser verdadeiro. Os cinco primeiros correspondem às formas previstas no art. 7º da Lei Maria da Penha. A violência vicária é mantida como categoria analítica adicional do projeto e deve ser descrita com precisão nas fontes recuperadas.

### Intenção principal

- `relato`;
- `informacao`;
- `ajuda_urgente`;
- `atendimento_humano`;
- `outro`.

A intenção se refere à mensagem atual. Uma conversa pode conter violência anterior e, no turno atual, um pedido de informação.

### Urgência

- `imediata`: perigo atual ou iminente explicitamente sustentado;
- `prioritaria`: risco relevante sem perigo atual claramente estabelecido;
- `sem_urgencia_detectada`: nenhum sinal de urgência no material disponível;
- `indeterminada`: evidência insuficiente, ambígua ou contraditória.

`sem_urgencia_detectada` não significa que a situação é segura.

## 3. Estado comum

Todos os modelos recebem a mesma entrada congelada por condição: memória anterior, até duas mensagens recentes e mensagem atual. O limite alvo é 1.536 tokens, ajustado somente pelo preflight comum.

Comparações que usam tokenizadores ou truncamentos diferentes devem ser identificadas. O turno nunca pode ser cortado silenciosamente para favorecer um modelo.

## 4. Modelos candidatos

| Modelo | Papel sugerido | Pontos favoráveis | Limitações principais |
|---|---|---|---|
| Qwen 3.5 4B Q4 | LLM classificadora | português razoável, JSON estruturado, mesmo modelo da memória | geração mais lenta e probabilidades pouco comparáveis |
| Kev-4B Q4 | System One principal | `/v1/systemone`, GGUF, perguntas tipadas em uma passagem | treinamento declarado em inglês |
| Julia-1 | baseline compacto multilíngue | 144M, CPU, evidência publicada em pt-PT, contexto amplo | domínio sensível não avaliado; até 20 opções |
| OpenJev-4B | candidato experimental de qualidade | arquitetura própria e bons resultados publicados de acurácia/Brier | runtime próprio, pesos BF16 apertados para 8 GB, sem evidência em pt-BR |
| lev-4B Q4 | comparador simples | GGUF e mesma API do llama.cpp | inglês e pouca evidência de domínio |
| Jebadiah-4B v2 | comparador experimental | GGUF; treino até 2.048 tokens | 4B sem avaliação principal publicada; inglês |
| OneJev-4B | comparador multimodal | GGUF disponível e treino com trajetórias de agentes | dados em inglês e foco distante do domínio |
| NeoHorse-Jev-4B Q4 | cobertura parcial | modelo aberto com decisões tipadas | estado textual limitado a 384 tokens |
| classificador supervisionado | baseline tradicional futuro | rápido, pequeno e ajustável ao domínio | exige dataset anotado e boa separação de teste |

Links e detalhes estão em [Fontes e referências](fontes.md).

O plano para obter dados em português e treinar classificadores supervisionados está em [Dados para classificação](dados-classificacao.md).

## 5. Perguntas System One

As seis formas de violência são perguntas `noul` independentes. Intenção e urgência são perguntas `choice`. Descrições das opções devem ser completas, pois esses modelos comparam semanticamente os critérios.

Exemplo:

```json
{
  "urgencia": {
    "type": "choice",
    "instructions": "Qual é a urgência observável considerando tempo e risco?",
    "criteria": {
      "imediata": "Há perigo atual ou iminente relatado.",
      "prioritaria": "Há risco relevante sem perigo atual ou iminente estabelecido.",
      "sem_urgencia_detectada": "Não há sinal de urgência no relato disponível.",
      "indeterminada": "As informações são insuficientes ou contraditórias."
    }
  }
}
```

Perguntas são versionadas como parte do experimento. Ajustes feitos no conjunto de desenvolvimento não podem continuar depois de aberto o teste fechado.

## 6. Probabilidades e calibração

Uma probabilidade produzida pelo modelo não deve ser interpretada diretamente como probabilidade de violência real. Primeiro é necessário medir calibração no domínio.

Procedimento proposto:

1. manter as probabilidades brutas;
2. medir Brier score e curvas de confiabilidade;
3. ajustar limiares somente no conjunto de desenvolvimento;
4. avaliar os limiares congelados no teste;
5. definir zona de incerteza para transbordo;
6. repetir por modelo e por rótulo.

Para urgência imediata, recall e número absoluto de falsos negativos têm precedência sobre acurácia global.

## 7. Combinação e transbordo

No primeiro experimento, os modelos são comparados, não combinados. Uma etapa posterior pode usar política como:

- qualquer classificador confiável indicando urgência imediata aciona revisão;
- divergência forte entre modelos aciona revisão;
- baixa confiança em intenção ou urgência aciona revisão;
- falha de um backend não é convertida em rótulo negativo;
- regras explícitas sobre sinais críticos funcionam como rede adicional, após validação profissional.

A política deve ser pequena, versionada e testável. Um ensemble opaco dificultaria atribuir erros à memória, ao classificador ou à regra de decisão.

## 8. Métricas

- precisão e recall por tipo;
- macro e micro F1;
- erro de intenção e matriz de confusão;
- acurácia e matriz de confusão de urgência;
- falsos negativos de urgência imediata;
- Brier score e erro de calibração;
- cobertura e taxa de falha;
- latência mediana e percentil 95;
- pico de VRAM e uso de RAM;
- estabilidade entre variações do mesmo roteiro;
- degradação causada por memória produzida pelo modelo.

Resultados do NeoHorse devem sempre mostrar cobertura, porque avaliar apenas entradas curtas cria um subconjunto diferente.

## 9. Recomendação atual

A rodada principal deve comparar Qwen 3.5 4B, Kev-4B e Julia-1. OpenJev-4B entra como candidato experimental quando houver uma configuração confiável para 8 GB. NeoHorse permanece como análise secundária. lev e Jebadiah podem ser adicionados com baixo custo depois que o protocolo estiver congelado.

Para classificadores treinados, começar com TF-IDF mais regressão logística como piso simples e BERTimbau como baseline neural em português. Um encoder multilíngue, como XLM-R, ajuda a testar transferência dos datasets em inglês. Treinar cabeças separadas ou multitarefa para tipos, intenção e urgência deve ser uma escolha experimental, não uma diferença implícita entre modelos.
