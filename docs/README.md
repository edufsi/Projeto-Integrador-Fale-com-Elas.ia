# Documentação da arquitetura

Este diretório reúne a arquitetura proposta para um assistente conversacional de acolhimento e orientação a mulheres em situação possivelmente violenta. O sistema é um projeto acadêmico e ainda não foi validado para atendimento real.

## Documentos

- [Arquitetura em alto nível](arquitetura.md): objetivos, fluxo completo, limites de segurança e decisões de projeto.
- [Arquitetura do MVP agentivo](arquitetura-mvp-agentivo.md): implementação atual, catálogo MCP, memória, fontes, transbordo e degradação.
- [Arquitetura agêntica](arquitetura-agentica.md): agente LLM com ferramentas, papel de System One, execução local e comparação com as propostas do repositório.
- [Business Model Canvas](business-model-canvas.md): proposta de valor, segmentos, parceiros, recursos, custos e sustentabilidade.
- [Módulo de memória](memoria.md): memória híbrida, atualização, correções, orçamento de contexto e privacidade.
- [Módulo de classificação](classificacao.md): contrato de rótulos, modelos candidatos, calibração e transbordo.
- [Dados para classificação](dados-classificacao.md): datasets existentes, geração sintética, validação e divisão experimental.
- [Módulo de resposta e RAG](resposta-rag.md): recuperação de fontes, geração fundamentada e respostas de emergência.
- [Avaliação e evolução](avaliacao.md): baseline atual, métricas, etapas experimentais e critérios de avanço.
- [Guia de rotulagem v1](avaliacao/guia-rotulagem-v1.md): ontologia operacional, memória, evidência, ação e rubricas do novo teste ouro.
- [Benchmark sintético exploratório](avaliacao/benchmark-exploratorio.md): conjunto de 60 mensagens com revisão única e consultas por intenção, tipo e ação.
- [Fontes e referências](fontes.md): legislação, instrumentos oficiais, serviços e modelos pesquisados.

## Estado atual

O código ativo está em `apps/backend/` e no submódulo `services/legal-mcp/`. O baseline de memória e classificação, o gerador sintético e a construção do corpus de avaliação foram retirados da árvore executável; seus dados e resultados permanecem em `data/archive/`. Os relatos continuam artificiais e não representam validação para atendimento real.

## Vocabulário

- **Indício:** sinal extraído do relato. Não equivale a conclusão jurídica, clínica ou policial.
- **Memória de trabalho:** representação compacta entregue aos modelos.
- **Histórico bruto:** mensagens completas, mantidas fora do contexto dos modelos sob política própria de retenção.
- **Transbordo:** encaminhamento do atendimento para uma pessoa capacitada.
- **RAG:** recuperação de documentos antes da geração da resposta.
- **System One:** modelo que pontua alternativas fornecidas, sem gerar livremente a resposta.
