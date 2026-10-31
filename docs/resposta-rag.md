# Módulo de resposta e RAG

## 1. Objetivo

O módulo transforma intenção, urgência, memória factual e mensagem atual em uma resposta acolhedora, útil e verificável. Ele deve recuperar material antes de formular afirmações sobre direitos, procedimentos e serviços.

RAG não corrige uma classificação errada por si só. A consulta precisa incluir o texto atual e fatos relevantes, sem depender exclusivamente dos rótulos inferidos.

## 2. Coleções de conhecimento

Separar o índice em coleções com políticas próprias:

1. **Legislação:** texto legal oficial e suas versões.
2. **Definições e guias:** CNJ, CNMP, Ministério das Mulheres, MPRS e outras instituições competentes.
3. **Serviços nacionais:** Ligue 180, emergências e canais oficiais.
4. **Rede local:** endereço, município, abrangência, horário, acessibilidade e forma de contato.
5. **Protocolos internos:** mensagens aprovadas, regras de transbordo e limites do sistema.

FONAR pode informar a pesquisa e a revisão profissional, mas não deve ser convertido em questionário automático no MVP. O CNJ o descreve como instrumento de avaliação de risco aplicado preferencialmente pela Polícia Civil ou, quando isso não for possível, pelo Ministério Público ou Judiciário, com exigência de sigilo.

## 3. Metadados obrigatórios

Cada trecho indexado deve carregar:

```json
{
  "documento": "Lei 11.340/2006",
  "orgao": "Presidência da República",
  "url": "https://...",
  "jurisdicao": "Brasil",
  "localidade": null,
  "tipo": "legislacao",
  "publicado_em": "2006-08-07",
  "verificado_em": "2026-10-07",
  "vigente_de": "2006-09-22",
  "vigente_ate": null,
  "secao": "Art. 7º",
  "hash": "..."
}
```

Serviços locais também precisam de latitude/longitude opcional, área atendida, telefone, canal, horário e data da última confirmação. Registro vencido não deve ser recomendado como atual.

## 4. Ingestão

1. buscar somente fontes autorizadas;
2. preservar documento original e hash;
3. extrair estrutura, título, seção e datas;
4. dividir por unidade semântica, sem misturar órgãos ou versões;
5. indexar texto e metadados;
6. revisar amostra da extração;
7. revalidar periodicamente links e vigência;
8. retirar do índice documentos substituídos, mantendo histórico auditável.

Conteúdo recuperado é dado, não instrução de sistema. Páginas e documentos devem ser tratados como potencialmente malformados e nunca podem alterar o comportamento do agente.

## 5. Recuperação

### Consulta

A consulta é construída com:

- mensagem atual integral;
- intenção e urgência;
- fatos ativos relevantes;
- localidade, somente quando informada ou consentida;
- tipo de informação pedido.

Classificações de violência ajudam a expandir termos, mas o texto original continua presente.

### Estratégia recomendada

Para o MVP:

- BM25 ou SQLite FTS5 para termos jurídicos, nomes e telefones;
- embeddings multilíngues para variação semântica;
- união dos candidatos por reciprocal rank fusion;
- filtros por jurisdição, localidade, vigência e tipo de fonte;
- reranqueador pequeno opcional;
- seleção final de poucos trechos com diversidade de fonte.

### Primeira implementação: SQLite FTS5 e FAISS

A primeira implementação deve manter as funções separadas e observáveis:

- SQLite armazena documentos, trechos, fontes, versões e metadados;
- FTS5 fornece busca lexical com BM25 para termos exatos, artigos, nomes e telefones;
- FAISS mantém o índice de vetores densos para busca semântica;
- filtros SQL restringem vigência, jurisdição, localidade e tipo de fonte;
- RRF, implementado na aplicação, combina os rankings lexical e denso;
- um reranqueador opcional atua somente sobre o conjunto reduzido de candidatos.

Essa composição permite medir isoladamente BM25, busca densa, busca híbrida, filtros e reranqueamento. Também evita manter outro serviço no primeiro protótipo.

SQLite e FAISS precisam permanecer sincronizados. Cada trecho deve ter um identificador estável compartilhado, e uma atualização só deve ser publicada depois de banco e índice terem sido produzidos com a mesma versão do corpus. Para bases pequenas, reconstruir o índice FAISS de modo atômico é mais simples que tentar atualizá-lo em lugar.

O módulo de resposta não deve conhecer o backend. Ele depende de uma interface como:

```python
class Retriever:
    def index(self, documents): ...
    def search(self, query, filters, limit): ...
```

A implementação inicial será `SqliteFaissRetriever`. Uma futura `QdrantRetriever` deverá retornar o mesmo formato de resultados, incluindo trecho, metadados, escores por recuperador e versão do índice.

### Quando avaliar Qdrant

Qdrant passa a fazer sentido quando houver muitos filtros, maior volume, atualizações frequentes, consultas simultâneas ou necessidade de operar a recuperação como serviço. Ele já oferece:

- índices vetoriais e persistência;
- vetores densos, esparsos e múltiplos vetores por trecho;
- payload JSON e índices para filtros;
- busca híbrida e fusão RRF ou DBSF;
- inserção, atualização e exclusão por API;
- quantização, armazenamento em disco, snapshots, shards e réplicas.

Ele não elimina ingestão, chunking, geração de embeddings, versionamento das fontes nem validação da resposta. O núcleo do Qdrant é o mecanismo de armazenamento e recuperação.

A migração deve ser tratada como experimento: executar o mesmo conjunto de consultas em `SqliteFaissRetriever` e `QdrantRetriever`, comparando recall@k, nDCG, latência, memória e complexidade operacional. Para a base pequena e estática do MVP, SQLite FTS5 mais FAISS continua sendo a escolha inicial.

Modelos de embeddings a testar incluem `multilingual-e5-small/base` e `bge-m3`. O primeiro favorece custo; o segundo favorece alcance e pode ser executado em CPU em etapa separada. A escolha deve ser decidida por recall de recuperação no corpus real, não por benchmark genérico.

## 6. Política por urgência

### Imediata

Não continuar com uma entrevista longa. Apresentar mensagem curta previamente revisada, oferecer transbordo humano e indicar canais adequados ao contexto. No Brasil, a fonte federal diferencia o Ligue 180, para acolhimento, orientação e denúncias, do 190, indicado para emergência ou violência em andamento.

Se a interface não consegue efetuar contato, deve dizer claramente que está exibindo opções e não que realizou o encaminhamento.

### Prioritária

Responder ao pedido atual, oferecer contato humano e recuperar serviços e direitos pertinentes. Evitar sobrecarregar a pessoa com uma lista extensa.

### Sem urgência detectada

Responder ao pedido sem afirmar que não há risco. Permitir acesso fácil a atendimento humano e recursos de ajuda.

### Indeterminada

Fazer no máximo uma pergunta curta quando ela puder mudar materialmente a orientação, ou oferecer transbordo. Não pressionar por detalhes desnecessários.

## 7. Geração

A LLM de resposta recebe:

- mensagem atual;
- memória factual atualizada;
- decisão de urgência e intenção;
- trechos recuperados com identificadores;
- instruções de estilo e limites;
- ações realmente disponíveis no sistema.

Estrutura sugerida:

1. reconhecimento breve do pedido;
2. informação diretamente útil;
3. opções concretas, em número limitado;
4. indicação de fonte;
5. pergunta opcional para continuar ou falar com uma pessoa.

O texto não deve diagnosticar, culpar, prometer sigilo inexistente, pressionar por denúncia nem apresentar inferência como fato. Detalhes de implementação e rótulos internos não aparecem para a usuária.

## 8. Validação da resposta

Antes de exibir:

- todo identificador de citação precisa existir nos trechos recuperados;
- telefones e URLs devem vir de campos estruturados, não ser gerados livremente;
- afirmações jurídicas verificáveis precisam de suporte recuperado;
- nenhuma ação pode ser descrita como concluída sem confirmação do sistema externo;
- resposta de urgência precisa conter o bloco obrigatório aprovado;
- ausência de fonte deve gerar linguagem de incerteza ou transbordo.

Um validador simples e determinístico deve preceder qualquer avaliador baseado em LLM.

## 9. Avaliação do RAG

- recall@k de documento e trecho;
- precisão de serviços por localidade;
- percentual de fontes vigentes;
- cobertura de citações;
- fidelidade entre resposta e trechos;
- respostas com telefone ou link inventado;
- utilidade e clareza avaliadas por pessoas;
- comportamento quando não existe documento suficiente;
- resistência a instruções maliciosas dentro dos documentos.

## 10. Atualização das fontes

Legislação, canais e serviços mudam. Cada execução deve registrar a versão do índice. Uma rotina de manutenção precisa verificar links, datas e mudanças de conteúdo. Documentos antigos permanecem arquivados para reprodução de experimentos, mas não participam da recuperação corrente sem marcação histórica.
