# E0 — Fundamentos: fontes, especialistas e decisões

← [plano.md](plano.md) · Contexto: [agente.md](agente.md) §17–18

## 1. Objetivo
Fechar o que **bloqueia** as demais etapas: materiais oficiais, pessoas que validam o conteúdo sensível e decisões de arquitetura.

## 2. Módulos-chave

| Módulo | O que é | Saída |
|---|---|---|
| Inventário de fontes | Coleta e registro dos documentos oficiais (FONAR, Violentômetro, IAVP, leis, cartilhas) | `docs/fontes.md` com URL, data de acesso, versão |
| Rede de revisores | Especialistas que validam pesos, tom, plano de segurança e texto jurídico | Lista com papel, disponibilidade e escopo |
| Registro de decisões (ADR) | Uma página por decisão arquitetural | `docs/adr/NNN-*.md` |
| Glossário e linguagem | Termos jurídicos → linguagem cidadã | `docs/glossario.md` |
| Contato institucional | Ponte com MPRS/CPSI (mentores do desafio) | Canal e perguntas pendentes |

## 3. Tarefas

1. Baixar/registrar o texto oficial do **FONAR** e a Lei 14.149/2021.
2. Localizar o **Violentômetro** e escolher a versão (adaptação brasileira/RS); registrar a decisão.
3. Obter documentação do **IAVP** (via MPRS ou literatura); se inacessível, registrar limitação.
4. Levantar a **lista de leis** do corpus (agente.md §7.1) e conferir cada uma no texto oficial.
5. Identificar **revisores**: assistente social/psicóloga (tom, plano de segurança), advogada/jurista (corpus), especialista em violência de gênero (pesos de risco). Fontes possíveis: mentores do CPSI, professores, núcleos de estudo da universidade, Defensoria.
6. Escrever ADRs para as decisões abaixo.
7. Enviar ao MPRS/professores as perguntas pendentes (153, compartilhamento em risco iminente, acesso a dados).

## 4. Decisões a fechar (uma ADR cada)

| # | Decisão | Opções | Impacto |
|---|---|---|---|
| D1 | Incluir IAVP | Sim / não / adiar | Banco de itens (E3) |
| D2 | Versão do Violentômetro | A definir | E3, E7 |
| D3 | LLM | API em nuvem c/ retenção zero · modelo aberto hospedado | LGPD, custo, E2/E4 |
| D4 | Escopo geográfico | RS todo · município-piloto | E5 |
| D5 | Histórico da usuária | **Decidido:** sessão persistida por cookie (sem conta), com prazo limitado e opção "não lembrar neste aparelho". Falta definir o prazo exato (RIPD) | E1, E7, E8 |
| D6 | Compartilhamento com a rede em risco iminente | Só orienta · aciona com consentimento · outra | E2, E8 (decisão jurídica) |
| D7 | Idiomas | pt-BR apenas · + Libras/outros depois | E6, E7 |
| D8 | Canais | Web/PWA na MVP · WhatsApp depois | E6, E7 |

## 5. Critérios de pronto
- Fontes registradas com data de acesso.
- Pelo menos um revisor por área (tom, jurídico, risco) confirmado — ou risco registrado.
- D1–D6 decididas ou com "padrão provisório" documentado.

## 6. Riscos
- Materiais oficiais não acessíveis → usar versões públicas e rotular como provisório.
- Sem revisor → o projeto é entregue como **protótipo acadêmico** e o conteúdo sensível marcado "não validado".

## 7. Prioridade
Começar **agora**; é o que destrava E3, E4 e E5.
