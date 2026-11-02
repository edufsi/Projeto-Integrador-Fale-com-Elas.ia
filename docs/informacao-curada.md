# Informação curada no agente

O RAG jurídico é reservado para dúvidas específicas e fontes recuperáveis. Informações
essenciais de uso recorrente ficam em recursos locais, curados e versionados, para reduzir
latência e dependência de recuperação em modelos pequenos.

## Ferramentas disponíveis

| Ferramenta | Uso | Limite |
|---|---|---|
| `information_get_general_help_resources` | Canais nacionais e explicação geral da rede | não localiza instituição nem confirma horário/local disponível |
| `information_get_violence_type_overview` | explicação educativa dos tipos adotados | não conclui que violência ou crime ocorreu em um caso |

Os arquivos ficam em `apps/backend/src/notas_ia/information/resources/`. Cada recurso
contém ID, versão, data de revisão, escopo, conteúdo e URLs de fontes oficiais. Uma revisão
editorial atualiza o arquivo e sua versão; a ferramenta e o agente não precisam mudar.

O template de transbordo imediato continua sendo a fonte controlada para 190 e Ligue 180
quando há possível perigo atual. Assim, o agente não precisa buscar nem redigir livremente
essas orientações críticas.

## Busca futura por instituição próxima

Essa capacidade ainda não é uma ferramenta do catálogo. Antes de implementá-la, será
necessário registrar consentimento explícito e revogável para a localização, consultar uma
base institucional de serviços, limitar precisão/retenção e informar que a resposta é uma
indicação de proximidade, não garantia de atendimento. A localização não deve ser enviada
automaticamente ao modelo, ao RAG ou ao log.
