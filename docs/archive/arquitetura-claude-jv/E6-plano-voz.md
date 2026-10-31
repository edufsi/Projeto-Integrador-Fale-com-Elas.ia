# E6 — Voz e canais

← [plano.md](plano.md) · Arquitetura: [agente.md](agente.md) §10

## 1. Objetivo
Aceitar áudio (STT com **WER ≤ 10%**) e desacoplar o núcleo do canal, permitindo adicionar WhatsApp depois.

## 2. Módulos-chave

| Módulo | Responsabilidade |
|---|---|
| **Captura/upload de áudio** | Formatos comuns, limite de duração, compressão (no cliente, E7) |
| **STT** | Áudio → texto pt-BR (serviço em nuvem ou Whisper hospedado) |
| **Normalizador** | Pontuação, números, gírias regionais |
| **Confiança e confirmação** | Baixa confiança em palavras de risco ⇒ o agente confirma antes de assumir |
| **Descarte** | Áudio apagado logo após transcrição |
| **Adaptadores de canal** | Web/PWA (MVP); WhatsApp (depois) → formato interno |
| **Síntese de voz (opcional)** | Resposta falada para acessibilidade |

## 3. Tarefas

1. Comparar 2–3 opções de STT em amostra pt-BR (sotaque gaúcho, ruído, idade, voz baixa/sussurrada).
2. Montar conjunto de teste com transcrição de referência e medir **WER**; registrar por perfil.
3. Endpoint `messages` aceitando áudio; pipeline STT → texto → E2.
4. Política de confiança e confirmação em trechos críticos.
5. Apagar áudio e transcrição temporária conforme política ([E8-plano-privacidade-seguranca.md](E8-plano-privacidade-seguranca.md)).
6. Adaptador para WhatsApp: estudar API oficial, limites de privacidade (histórico no aparelho); decidir se entra.
7. (Opcional) TTS.

## 4. Critérios de pronto
- WER ≤ 10% no conjunto de teste, com relatório por perfil.
- Nenhum áudio persistido após a resposta.
- Mensagem de áudio e de texto produzem o mesmo tratamento de emergência.

## 5. Riscos
- WER alto em voz baixa/ruído → confirmar transcrição; oferecer digitar.
- Provedor STT em nuvem = dado sensível em terceiro → contrato sem retenção/treino, ou modelo hospedado.
- WhatsApp compromete sigilo (histórico visível) → tratar como fase posterior e com avisos claros.
