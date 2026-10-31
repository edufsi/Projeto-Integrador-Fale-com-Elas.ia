# E4 — Base de conhecimento jurídica (RAG) · **Recorte do trabalho de PLN**

← [plano.md](plano.md) · Arquitetura: [agente.md](agente.md) §7, §9

## 1. Objetivo
**No Projeto Integrador:** um módulo que responde dúvidas jurídicas só com base em texto oficial curado, com citação e abstenção.
**No trabalho de PLN:** estudo experimental aprofundado de **recuperação** (dense retrieval + reranqueamento) e **fidelidade da geração** sobre esse corpus.

## 2. Fronteira PI × PLN

| | Projeto Integrador | PLN |
|---|---|---|
| Entrada | Pergunta da usuária (texto) | Pergunta em linguagem leiga |
| Saída | Trechos + resposta com citações + flag de abstenção | Ranking de artigos + métricas |
| Foco | Integração, robustez, latência | Método, dataset, comparação, análise de erros |
| Interface | `rag.search(query, k)` e `rag.answer(query)` | Notebooks/experimentos em `eval/rag/` |
| Entrega | Módulo funcional | Relatório/artigo com resultados |

Contrato entre os dois: `search(query, k) → [{chunk_id, norma, artigo, texto, score, vigencia}]`.

## 3. Módulos-chave

| Módulo | Responsabilidade |
|---|---|
| **Ingestão** | Baixar textos oficiais, normalizar, versionar |
| **Chunking** | Divisão por artigo/inciso/parágrafo, mantendo hierarquia e contexto (caput) |
| **Metadados** | Norma, artigo, vigência, tema, URL oficial, data de verificação, revisor |
| **Notas em linguagem simples** | Explicações revisadas, vinculadas ao artigo de origem |
| **Índice híbrido** | BM25 + vetorial (pgvector/OpenSearch) |
| **Recuperador denso** | Embeddings (BGE-M3, multilingual-e5, BERTimbau ajustado) |
| **Reranqueador** | Cross-encoder para reordenar top-k |
| **Reescrita de consulta** | Linguagem coloquial → termos jurídicos (avaliada como experimento) |
| **Limiar de suficiência** | Decide entre responder e **abster** |
| **Gerador com citação** | LLM restrito aos trechos recuperados |
| **Verificador de fidelidade** | Cada afirmação apoiada por trecho? |
| **Curadoria contínua** | Revisão periódica e alerta de mudança legislativa |

## 4. Plano de trabalho

**Parte A — Corpus**
1. Lista de normas (agente.md §7.1) conferida contra texto oficial.
2. Pipeline de ingestão + chunking; versão do corpus com hash.
3. Revisão jurídica das notas em linguagem simples.

**Parte B — Dataset anotado (ground truth, exigência do PLN)**
4. Definir esquema: `{id, pergunta, artigos_relevantes[], relevancia (graduada), tipo_pergunta, anotador}`.
5. Redigir 150–300 perguntas em linguagem leiga cobrindo: tipos de violência, medidas protetivas, denúncia, guarda/filhos, trabalho, moradia, provas, fluxos da delegacia e da Justiça.
6. Incluir **perguntas sem resposta na base** (para medir abstenção) e perguntas adversas (mal formuladas, gírias, ambíguas).
7. Dupla anotação numa amostra + concordância (Cohen's κ); adjudicar divergências; revisão de jurista.
8. Divisão treino/validação/teste (**teste congelado**).
9. Complemento com dataset público em português para validar o método em escala (a confirmar).

**Parte C — Experimentos**
10. Linha de base: BM25.
11. Dense retrieval zero-shot (BGE-M3, multilingual-e5, BERTimbau-based).
12. Híbrido (fusão BM25 + denso).
13. Reranqueamento com cross-encoder.
14. **Fine-tuning** de embeddings com pares do treino (e negativos difíceis).
15. Ablações: tamanho/estratégia de chunk, reescrita de consulta, k, adição das notas simples.
16. Geração: fidelidade às fontes, taxa de alucinação, taxa de abstenção correta.
17. Análise de erros por categoria + testes de significância.

**Parte D — Integração**
18. Empacotar o melhor pipeline como serviço interno usado pelo orquestrador ([E2-plano-conversa.md](E2-plano-conversa.md)).
19. Latência e custo por consulta.

## 5. Métricas
- Recuperação: Recall@k (1,3,5,10), MRR, nDCG@10.
- Abstenção: precisão/recall de "sem resposta na base".
- Geração: fidelidade (afirmações apoiadas / total), alucinação (HAM), citação correta.
- Custo: latência p50/p95, tokens.

## 6. Critérios de pronto
- Dataset publicado no repositório com documentação (folha de dados) e concordância medida.
- Tabela comparativa de métodos com intervalos de confiança.
- Módulo integrado com abstenção calibrada.

## 7. Riscos
- Dataset pequeno → validação cruzada e complemento público.
- Viés do anotador único → dupla anotação em amostra.
- Legislação muda → versão do corpus congelada por experimento; documentar data.
- Escopo do PLN engolir o do PI → manter o contrato `search/answer` estável.

## 8. Entregas para os professores
- Proposta de tópico de uma página (tarefa, dataset, modelos, métricas) para aprovação.
- Confirmar que dataset próprio atende ao item (iii) e que o recorte é aceito nas duas disciplinas.
