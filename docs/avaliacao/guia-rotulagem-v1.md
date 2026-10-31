# Guia de rotulagem v1

## Finalidade e unidade de análise

Este guia define o gabarito experimental do assistente. Os rótulos representam indícios presentes no texto e não constituem conclusão jurídica, diagnóstico ou aplicação oficial de instrumentos como FONAR e IAVP.

A unidade principal é um **turno da usuária com o histórico visível anterior**. Tipos e urgência são cumulativos enquanto os fatos permanecem válidos. A intenção descreve o objetivo da mensagem atual. A ação descreve o próximo comportamento esperado do sistema.

## Tipos de violência

Cada tipo é um booleano independente. Marque apenas quando existir um fato textual compatível; dúvida genérica ou falta de contexto não conta como evidência positiva.

O campo de tipo significa **indício textual positivo ou possibilidade sustentada pelos fatos disponíveis**. A mera menção ao nome de um tipo, uma pergunta conceitual ou uma negação explícita não torna o tipo positivo. Para preservar o assunto discutido sem criar um falso positivo, o benchmark exploratório mantém também `tipos_mencionados`, separado de `tipos_com_indicio`.

| Tipo | Marcar quando houver indício de | Não marcar apenas por |
|---|---|---|
| `fisica` | agressão ao corpo ou à saúde corporal, restrição física, estrangulamento | medo, discussão, objeto quebrado sem contato corporal |
| `psicologica` | ameaça, controle, isolamento, perseguição, humilhação ou coerção emocional | discordância isolada ou sentimento sem conduta descrita |
| `sexual` | ato sexual ou reprodutivo imposto, sem consentimento ou mediante coerção | pergunta geral sobre consentimento |
| `patrimonial` | retenção, subtração ou destruição de bens, documentos, renda ou recursos | divisão financeira livremente combinada |
| `moral` | calúnia, difamação ou injúria, inclusive exposição ofensiva | crítica de trabalho sem ofensa à honra descrita |
| `vicaria` | uso de filhos ou familiares para causar dano à mulher | conflito de guarda sem ato dirigido a atingi-la |

Um fato pode sustentar mais de um tipo. Não acrescente automaticamente `psicologica` a todo caso: é preciso haver ameaça, controle, humilhação, medo imposto ou conduta emocionalmente coercitiva descrita.

## Intenção principal da mensagem atual

| Rótulo | Regra operacional |
|---|---|
| `relato` | a mensagem principalmente conta ou esclarece uma experiência |
| `informacao` | pede definição, canal, procedimento ou orientação geral |
| `ajuda_urgente` | pede socorro ou ação imediata diante de perigo atual ou iminente |
| `atendimento_humano` | pede explicitamente contato com uma pessoa atendente |
| `outro` | ruído, teste, conteúdo fora do escopo ou objetivo ainda não identificável |

Pedidos explícitos prevalecem sobre a forma gramatical. “Quero falar com uma atendente e contar o que houve” é `atendimento_humano`. “Ele está aqui, preciso de ajuda agora” é `ajuda_urgente`.

## Urgência

| Rótulo | Regra operacional |
|---|---|
| `imediata` | perigo atual ou iminente, agressor presente, impedimento de sair, ameaça prestes a ocorrer ou pessoa vulnerável atualmente exposta |
| `prioritaria` | risco relevante ou violência recente/recorrente sem perigo atual informado |
| `sem_urgencia_detectada` | há informação suficiente para concluir que não foi relatado perigo atual ou relevante no contexto disponível |
| `indeterminada` | faltam tempo, proximidade, segurança atual ou sentido suficiente para decidir |

“Sem urgência detectada” não significa “caso sem importância”. Relato antigo, já encerrado e com segurança atual explicitada pode receber esse rótulo. Uma entrada mínima como “socorro” tem intenção urgente, mas urgência `indeterminada` até haver contexto de perigo.

## Ação operacional

| Ação | Quando usar |
|---|---|
| `redirecionar_ao_escopo` | entrada claramente alheia ao serviço, sem contexto anterior relevante |
| `responder_informacao_geral` | pergunta geral respondível sem triagem de caso atual |
| `acolher_sem_escalar` | relato sem urgência ou mensagem inicial que permite continuidade segura |
| `perguntar_risco_e_oferecer_humano` | risco ou sentido insuficiente; perguntar segurança atual e oferecer pessoa atendente |
| `oferecer_atendimento_humano` | pedido explícito de pessoa ou caso em que o canal humano deve ser oferecido |
| `continuar_triagem_prioritaria` | risco relevante sem perigo imediato; acolher e coletar apenas o necessário |
| `preservar_memoria_e_redirecionar` | ruído ou desvio após relato relevante; manter o contexto anterior |
| `transbordar_imediatamente` | perigo atual/iminente; iniciar fluxo humano/emergencial conforme protocolo |

Em caso de sobreposição, aplique esta precedência:

1. perigo atual ou iminente → `transbordar_imediatamente`;
2. pedido explícito de pessoa atendente → `oferecer_atendimento_humano`;
3. segurança atual ainda insuficiente para decidir → `perguntar_risco_e_oferecer_humano`;
4. risco prioritário já identificado → `continuar_triagem_prioritaria`;
5. caso sem escalonamento → ação informativa, acolhimento ou redirecionamento correspondente.

Uma resposta de triagem prioritária pode oferecer atendimento humano. A ação registra o objetivo operacional principal do turno.

A ação é avaliada separadamente da urgência. Uma usuária pode pedir atendimento humano sem relatar perigo; nesse caso, a intenção é `atendimento_humano`, a urgência pode ser `sem_urgencia_detectada` e a ação é `oferecer_atendimento_humano`.

## Evidência literal

- A evidência deve ser um trecho contínuo e literal da mensagem do turno que introduziu ou corrigiu o fato.
- Pontuação e caixa podem variar na validação, mas não se deve parafrasear.
- Para um rótulo cumulativo, preserve a referência ao turno original; não invente uma nova evidência no turno atual.
- Uma mensagem pode ter mais de um trecho de evidência.
- Intenção e conteúdo fora do escopo podem ter lista de evidências vazia.
- Duas listas de evidência podem ser equivalentes mesmo sem igualdade exata. Na auditoria, avalie se os trechos são literais, válidos e cobrem os fatos necessários; diferenças de extensão ou a escolha de outro trecho válido não são automaticamente erros.

## Memória, tempo, correção e revogação

A memória factual ouro contém somente fatos já revelados. Cada fato registra afirmação curta, trecho literal, turno de origem, situação temporal e criticidade. O resumo ouro sintetiza os mesmos fatos sem adicionar causas, identidades, diagnósticos ou conclusões jurídicas.

Quando a usuária corrige um fato, registre a nova evidência e o identificador do fato revogado. A revogação remove o fato das classificações cumulativas, mas o histórico da correção permanece auditável. Negação só revoga quando se refere claramente ao fato anterior; “não quero falar disso” não nega o acontecimento.

## Fatos, inferências e conteúdo proibido

**Fatos observados:** aparecem expressamente no texto ou em contexto anterior ainda válido.

**Inferências aceitáveis:** apenas as necessárias para aplicar a ontologia, como reconhecer que “não me deixa sair do quarto” descreve restrição física e risco atual.

**Informações proibidas:** nomes, endereços, diagnósticos, motivação do agressor, situação jurídica, canais locais específicos, segurança atual ou fatos futuros que não tenham sido informados.

## RAG e resposta

Os tópicos RAG são necessidades de conhecimento, não IDs de chunks. Recuperar apenas o necessário ao turno. `nenhum_documento_necessario` vale para ruído, acolhimento curto e fluxo imediato que não dependa de explicação documental.

A rubrica de resposta contém obrigações observáveis e proibições. Não existe texto único de referência. Em todo caso, a resposta deve evitar culpabilização, promessas, conclusão jurídica categórica e fatos inventados. Em urgência imediata, concisão e transbordo têm precedência sobre explicações longas.

## Procedimento de rotulagem

1. Leia somente o histórico visível e a mensagem atual.
2. Identifique correções e fatos ainda válidos.
3. Marque os seis tipos independentemente.
4. Rotule a intenção da mensagem atual.
5. Rotule a urgência do estado conhecido.
6. Escolha uma ação operacional.
7. Copie os trechos literais que sustentam a decisão.
8. Informe confiança (`alta`, `media`, `baixa`) e use comentário apenas para dúvida real.

Casos de violência sexual, vicária e urgência imediata sempre passam por revisão quando houver divergência. O arquivo de decisões de fronteira acompanha este guia e é normativo para a calibração.
