# Fontes e referências

Última revisão desta lista: 7 de outubro de 2026.

## Desafio e contexto

- [Desafio 42 — CPSI/MPRS](https://cpsi.lab.mprs.mp.br/challenges/42/)

## Legislação e instrumentos oficiais

- [Lei nº 11.340/2006 — Lei Maria da Penha](https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm). O art. 7º descreve as formas física, psicológica, sexual, patrimonial e moral.
- [Lei nº 14.188/2021](https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14188.htm). Inclui o tipo penal de violência psicológica contra a mulher e institui o programa Sinal Vermelho.
- [FONAR — página do CNJ](https://www.cnj.jus.br/programas-e-acoes/violencia-contra-a-mulher/formulario-nacional-de-avaliacao-de-risco-fonar/). Descreve finalidade, aplicação e sigilo.
- [Resolução Conjunta CNJ/CNMP nº 5/2020](https://atos.cnj.jus.br/atos/detalhar/3218). Institui o FONAR no Judiciário e Ministério Público.
- [Portaria Conjunta CNJ/CNMP nº 6/2025](https://atos.cnj.jus.br/atos/detalhar/6242). Atualiza o modelo do formulário e reforça tratamento de dados e confidencialidade.
- [Ligue 180 — Ministério das Mulheres](https://www.gov.br/mulheres/pt-br/ligue180). Orientação, informações sobre serviços e denúncias; a página indica 190 para emergências.

## Modelos generativos

- [Qwen 3.5 4B no Ollama](https://ollama.com/library/qwen3.5:4b). Modelo local usado como classificador JSON e atualizador de memória no baseline.

## Modelos System One e decisões tipadas

- [Suporte a decision models no llama.cpp](https://huggingface.co/blog/ggml-org/decision-models-in-llamacpp). Documenta `/v1/systemone`, `choice`, `score` e `noul`.
- [Kev-4B GGUF](https://huggingface.co/ggml-org/Kev-4B-GGUF). Comparador principal no baseline.
- [Julia-1](https://huggingface.co/SupersonicLabs/Julia-1). Encoder multilíngue de 144,3M parâmetros, com contexto de runtime de até 8.192 tokens e avaliação publicada em português europeu.
- [Julia-1 GGUF](https://huggingface.co/ggml-org/Julia-1-GGUF). Conversão para llama.cpp.
- [OpenJev-4B](https://huggingface.co/shenjunhao/OpenJev-4B). Modelo de decisão de 4B com resultados publicados de acurácia e Brier e runtime próprio.
- [OpenJev 27B GGUF](https://huggingface.co/ggml-org/OpenJev-GGUF). Modelo diferente do OpenJev-4B; grande demais para o hardware alvo.
- [lev GGUF](https://huggingface.co/ggml-org/lev-GGUF). Modelo de 4B compatível com `/v1/systemone`.
- [Jebadiah-4B v2](https://huggingface.co/frontier-infra/jebadiah-4b-v2). Modelo de 4B treinado em inglês, com limite de treino informado de 2.048 tokens.
- [Jebadiah-4B v2 GGUF](https://huggingface.co/frontier-infra/jebadiah-4b-v2-GGUF). Quantizações para execução local.
- [OneJev-4B](https://huggingface.co/OmniJev/OneJev-4B). Modelo multimodal de decisões, voltado também a trajetórias de agentes.
- [NeoHorse-Jev-4B GGUF](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B-GGUF). Q4_K_M com runtime próprio; estado textual limitado a 384 tokens.
- [Kev-9B](https://huggingface.co/jaredpalmer/kev-9b). Candidato de escala posterior, com contexto validado até 8.192 tokens pelo autor.

## Datasets e métodos de construção de dados

- [SMM4H 2022 — Task 7](https://healthlanguageprocessing.org/smm4h-2022/). Classificação binária de autorrelato de violência por parceiro íntimo em tweets em inglês: 4.523 exemplos de treino, 534 de validação e 1.291 de teste, com aproximadamente 11% positivos.
- [Natural language model for automatic identification of IPV reports](https://pmc.ncbi.nlm.nih.gov/articles/PMC10065459/). Descreve a coleta e anotação de 6.348 tweets em inglês e os critérios para considerar um relato autorreferido.
- [Severity-Aware Women Safety Survey Dataset](https://aperta.ulakbim.gov.tr/records/286831). Respostas anonimizadas de pesquisa, com indicadores estruturados de ameaça, medo, escalada e contexto de segurança.
- [Africa GBV/IPV](https://huggingface.co/datasets/electricsheepafrica/gender-based-violence-ipv). Dataset tabular e textual em inglês; requer auditoria da geração, da representatividade e da adequação cultural antes do uso.
- [Learned Hands Domestic Violence](https://huggingface.co/datasets/mteb/LearnedHandsDomesticViolenceLegalBenchClassification). Pequeno conjunto em inglês para identificar questões jurídicas relacionadas a violência doméstica.
- [Domestic Violence Information Support](https://huggingface.co/datasets/Spiderman01/Domestic_violence_info_support_fromposts). 273 posts com 14 tipos de necessidade de informação; exige revisão de proveniência e licença antes do uso.
- [CRADLE Bench](https://github.com/emorynlp/CradleBench). Inclui violência doméstica entre rótulos de crise; desenvolvimento e teste foram anotados por profissionais clínicos, enquanto o treino usa consenso de múltiplas LLMs.
- [NariRaksha](https://huggingface.co/datasets/vikhram-labs/NariRaksha-1K). Cenários sintéticos de segurança de mulheres associados ao contexto indiano; útil para estudar estrutura, não para transferir diretamente legislação ou distribuição para o Brasil.
- [Classificação de necessidades de sobreviventes de violência doméstica](https://www.jmir.org/2025/1/e65397/). Estudo com posts de comunidades online e aumento de dados por LLM para classificação de necessidades informacionais.

## Classificadores supervisionados candidatos

- [BERTimbau base](https://huggingface.co/neuralmind/bert-base-portuguese-cased). Encoder BERT pré-treinado para português.
- [XLM-R base](https://huggingface.co/FacebookAI/xlm-roberta-base). Encoder multilíngue para testar transferência entre dados em inglês e português.

## Fontes a acrescentar antes do RAG

- versões oficiais e consolidadas das legislações usadas;
- materiais institucionais do MPRS e rede do Rio Grande do Sul;
- diretório oficial de serviços com data de atualização;
- políticas internas de atendimento e transbordo;
- documentos revisados por especialistas sobre acolhimento e comunicação;
- fontes específicas sobre violência vicária e escopo jurídico aplicável.

## Regra de uso

Uma fonte nesta lista não entra automaticamente no índice RAG. Antes da ingestão, verificar autoria, vigência, jurisdição, finalidade, licença de uso, estrutura do documento e data de atualização. Benchmarks divulgados por autores de modelos são evidência inicial, não validação para este domínio.
