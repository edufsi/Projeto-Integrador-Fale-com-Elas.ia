# Chatbot de voz em português — documentação

Este documento reúne a arquitetura, as alternativas de modelos, a implementação básica e o plano de avaliação do chatbot de voz desenvolvido neste projeto.

## 1. Objetivo

A aplicação recebe áudio pelo microfone, transforma a fala em texto, envia o texto para um LLM e converte a resposta do LLM novamente para áudio:

```text
Microfone
   ↓
STT — Speech-to-Text
   ↓
LLM local ou remoto
   ↓
TTS — Text-to-Speech
   ↓
WAV reproduzido no navegador
```

STT e TTS são problemas independentes. É possível trocar o reconhecedor de fala sem trocar a voz sintética, ou trocar o TTS sem alterar o LLM.

## 2. Implementações existentes

Há duas aplicações simples no workspace:

- `voice_chatbot`: implementação inicial usando `faster-whisper`.
- `voice_chatbot_ptbr`: implementação voltada aos modelos brasileiros de Whisper via `transformers`, incluindo `freds0/distil-whisper-large-v3-ptbr` e `RodrigoFardin/whisper-small-pt-br`.

As duas usam o Ollama para o LLM e o Kokoro para TTS. A interface web é baseada em `MediaRecorder`: o navegador grava WebM/Opus, envia o arquivo ao backend e recebe a transcrição, a resposta textual e o áudio sintetizado.

## 3. Componentes da solução

### 3.1 STT: Whisper

O Whisper é multilíngue e inclui português. A aplicação força o idioma e a tarefa quando usa a API do Transformers:

```python
language="pt"
task="transcribe"
```

Isso ajuda a evitar que uma fala em português seja interpretada como tradução para inglês. O Whisper original foi publicado pela OpenAI; `faster-whisper` é uma implementação baseada em CTranslate2, geralmente mais eficiente para inferência local.

Referências:

- [Whisper](https://github.com/openai/whisper)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [whisper.cpp](https://github.com/ggml-org/whisper.cpp)

### 3.2 LLM

O backend conversa com o Ollama através de HTTP. O modelo usado nos testes foi:

```text
llama3.1:8b
```

Ele pode ser substituído por outro modelo compatível com Ollama, por exemplo `qwen2.5:7b`, alterando `OLLAMA_MODEL` no arquivo `.env`.

O LLM não faz reconhecimento de áudio: ele recebe a transcrição produzida pelo STT e gera a resposta textual.

### 3.3 TTS: Kokoro-82M

O Kokoro-82M é um modelo TTS pequeno, de aproximadamente 82 milhões de parâmetros. Na aplicação foi usado com:

```python
KPipeline(lang_code="p")
```

e a voz:

```text
pf_dora
```

As vozes brasileiras disponíveis incluem também `pm_alex` e `pm_santa`, dependendo da versão instalada. A saída é gerada em WAV, normalmente a 24 kHz, e enviada ao navegador como áudio.

O Kokoro é adequado para uma aplicação local leve, mas não é uma voz gaúcha. Ele produz português brasileiro relativamente neutro e não foi treinado especificamente para reproduzir léxico, prosódia ou sotaque do Rio Grande do Sul.

Referências: [repositório do Kokoro](https://github.com/hexgrad/kokoro) e [modelo Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M).

## 4. Variações de STT testadas

### 4.1 `faster-whisper small` ou `medium`

Foi a primeira alternativa considerada por ser simples e eficiente:

```text
faster-whisper
├── small  — mais leve e rápido
└── medium — mais pesado, potencialmente mais preciso
```

Configuração típica para CPU:

```text
WHISPER_MODEL=small
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
```

Vantagens:

- fácil de instalar e usar;
- boa velocidade em CPU com quantização `int8`;
- suporta português diretamente;
- pode ser usado sem baixar os modelos maiores do Transformers.

Limitações:

- não é especializado em português brasileiro;
- sotaques e regionalismos podem ser reconhecidos de forma inconsistente;
- `medium` exige mais memória e tende a aumentar a latência.

#### Problema de compatibilidade com PyAV

O `faster-whisper` utilizado pela aplicação chamava `av.open` com o argumento `metadata_errors`. Versões recentes do PyAV removeram esse argumento, produzindo:

```text
TypeError: open() got an unexpected keyword argument 'metadata_errors'
```

A solução adotada foi restringir a dependência:

```text
av>=11,<19
```

Também foi adicionado um diagnóstico explícito para avisar quando uma versão incompatível do PyAV é encontrada.

### 4.2 `freds0/distil-whisper-large-v3-ptbr`

Este foi o modelo que apresentou o melhor resultado prático nos testes realizados. É uma versão destilada baseada na família Whisper Large, ajustada para português brasileiro.

Características relevantes:

- aproximadamente 0,8 bilhão de parâmetros;
- checkpoint de cerca de 3 GB baixado na primeira execução;
- usado via `transformers`, e não diretamente via `faster-whisper`;
- exige mais memória que `small`, mas a destilação mantém a inferência suficientemente rápida;
- o usuário observou boa velocidade e melhor qualidade geral que as versões menores.

O model card reporta WER de aproximadamente 8,22% em sua avaliação própria. Esse número não deve ser comparado diretamente com outros modelos sem usar o mesmo conjunto de dados, a mesma normalização e o mesmo protocolo.

Referência: [freds0/distil-whisper-large-v3-ptbr](https://huggingface.co/freds0/distil-whisper-large-v3-ptbr).

#### Erro de `max_new_tokens`

O primeiro código usava `max_new_tokens=448`. Como o Whisper aceita no máximo 448 posições no decoder e já havia tokens de início, o total ultrapassava o limite:

```text
The combined length ... exceeds the max_target_positions of the Whisper model: 448
```

A correção foi usar um valor menor, atualmente `440`, e substituir configurações antigas por:

```python
language="pt"
task="transcribe"
```

Isso também evita depender de `forced_decoder_ids`, que aparece como configuração depreciada nas versões atuais do Transformers.

### 4.3 `RodrigoFardin/whisper-small-pt-br`

Este é um fine-tuning do Whisper Small para português brasileiro. É uma alternativa mais leve para comparar custo, velocidade e qualidade.

Para testá-lo na aplicação `voice_chatbot_ptbr`, basta alterar o `.env`:

```dotenv
ASR_MODEL=RodrigoFardin/whisper-small-pt-br
```

O model card reporta WER de aproximadamente 17,38% em sua avaliação própria. Ele não é diretamente comparável ao modelo `freds0`, porque os conjuntos de dados, o particionamento e a normalização podem ser diferentes.

Referência: [RodrigoFardin/whisper-small-pt-br](https://huggingface.co/RodrigoFardin/whisper-small-pt-br).

### 4.4 `EliezerCarvalho/WhisperLv3-PT`

Foi considerada como alternativa futura. É uma versão de maior porte voltada a variedades do português, com dados de português brasileiro, europeu, africano e asiático. O treinamento reportado é muito maior que o dos modelos pequenos, e a execução local exige mais memória.

Referência: [EliezerCarvalho/WhisperLv3-PT](https://huggingface.co/EliezerCarvalho/WhisperLv3-PT).

### 4.5 Vosk

O Vosk é uma alternativa muito leve, com modelos pequenos e execução offline. Pode ser interessante para máquinas fracas ou aplicações embarcadas, mas em geral tende a oferecer menor qualidade que as variantes modernas do Whisper, especialmente em fala espontânea e com regionalismos. Não foi escolhido para a versão atual.

## 5. Por que “bah” pode falhar?

Mesmo um bom modelo geral pode omitir ou substituir expressões como `bah` porque:

- é uma palavra curta e com pouca informação acústica;
- pode ser interpretada como hesitação, ruído ou interjeição descartável;
- modelos gerais não foram treinados especificamente para o vocabulário gaúcho;
- dados de fala lida, como parte do Common Voice, não representam bem conversa espontânea;
- o contexto acústico, o microfone e a pronúncia influenciam muito.

É possível dar um pequeno viés de vocabulário com `initial_prompt`, mas isso deve ser usado com cuidado: pode fazer o modelo inserir palavras esperadas que não foram faladas.

Para avaliar o caso real, o ideal é incluir frases com:

```text
bah, tchê, guri, gurizada, tri, sinaleira, bergamota, barbaridade
```

e não medir somente a média geral de WER.

## 6. TTS regionalizado ou gaúcho

Não foi encontrada uma versão pública, leve e pronta do Kokoro especificamente regionalizada para o sotaque gaúcho. Há três possibilidades diferentes:

### 6.1 Usar o Kokoro neutro

É a opção atual: barata, local e simples. A resposta fica em português brasileiro, mas não necessariamente soa gaúcha.

### 6.2 Clonar uma voz gaúcha

Modelos como XTTS-v2 podem sintetizar texto usando uma gravação de referência. Isso tende a preservar timbre e parte da prosódia de uma pessoa real, desde que a gravação tenha consentimento e boa qualidade.

- [XTTS-v2](https://docs.coqui.ai/en/latest/models/xtts.html)

Também existe o projeto comunitário [F5-TTS PT-BR](https://github.com/Cataldir/f5-tts-pt-br), com modelo ajustado para português brasileiro e suporte a referência de voz. Ele é mais pesado que Kokoro e as licenças dos pesos devem ser verificadas antes de uso comercial.

Clonar uma voz não garante automaticamente um sotaque gaúcho perfeito: timbre, prosódia e pronúncia são dimensões diferentes. Para controlar o sotaque, a referência deve conter fala natural do locutor e o texto de entrada pode precisar usar vocabulário regional.

### 6.3 Treinar ou adaptar uma voz com dados regionais

O [SOTAQUE](https://sotaque.ia.br/) reúne vozes brasileiras com informação regional, inclusive categorias relacionadas ao Sul. É mais útil como fonte de dados e pesquisa do que como um modelo TTS pronto para instalar.

Para qualquer uso com voz de terceiros, é necessário verificar licença, consentimento, privacidade e autorização para clonagem.

## 7. Execução local

### 7.1 Aplicação inicial com `faster-whisper`

No PowerShell:

```powershell
cd C:\caminho\para\voice_chatbot
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
ollama pull llama3.1:8b
ollama serve
```

Em outro terminal, com o ambiente virtual ativado:

```powershell
cd C:\caminho\para\voice_chatbot
.\.venv\Scripts\Activate.ps1
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Acesse [http://127.0.0.1:8000](http://127.0.0.1:8000).

Durante os testes, foi preferível iniciar sem `--reload`, pois o modo de recarga pode observar muitos arquivos do ambiente virtual e parecer parado. A primeira execução também pode demorar por causa do download e do carregamento dos modelos.

### 7.2 Aplicação com modelos PT-BR via Transformers

```powershell
cd C:\caminho\para\voice_chatbot_ptbr
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app:app --host 127.0.0.1 --port 8001
```

Acesse [http://127.0.0.1:8001](http://127.0.0.1:8001).

O primeiro carregamento de `freds0/distil-whisper-large-v3-ptbr` baixa aproximadamente 3 GB e pode levar alguns minutos. Depois, o modelo fica em cache.

O `.env` principal contém:

```dotenv
ASR_MODEL=freds0/distil-whisper-large-v3-ptbr
ASR_DEVICE=auto
OLLAMA_URL=http://127.0.0.1:11434/api/chat
OLLAMA_MODEL=llama3.1:8b
KOKORO_LANG=p
KOKORO_VOICE=pf_dora
KOKORO_SPEED=1.0
SYSTEM_PROMPT=Você é um assistente útil. Responda em português brasileiro, de forma natural e concisa.
```

Para trocar para o modelo Small:

```dotenv
ASR_MODEL=RodrigoFardin/whisper-small-pt-br
```

O backend reporta os tempos de STT, LLM, TTS e o tempo total. Isso permite separar se a lentidão percebida vem do reconhecimento, da geração de texto ou da síntese de voz.

## 8. Fluxo técnico da aplicação

1. O navegador solicita permissão para usar o microfone.
2. `MediaRecorder` grava o áudio em WebM/Opus.
3. O frontend envia o arquivo em `multipart/form-data` para `/api/chat/voice`.
4. O backend decodifica o áudio com PyAV e converte para mono, 16 kHz.
5. O STT gera a transcrição em português.
6. A transcrição é enviada ao Ollama.
7. A resposta textual é enviada ao Kokoro.
8. O WAV é codificado em Base64 na resposta JSON.
9. O navegador exibe a transcrição, a resposta e reproduz o áudio.

O histórico atual é mantido no frontend e enviado a cada requisição. Para uma aplicação real, seria necessário adicionar autenticação, limites de tamanho, tratamento de concorrência, persistência e controle de privacidade.

## 9. Benchmark de STT

### 9.1 Métricas

O benchmark incluído em `voice_chatbot_ptbr/benchmark.py` calcula:

- **WER — Word Error Rate**: erros de substituição, deleção e inserção divididos pelo número de palavras da referência.
- **CER — Character Error Rate**: mesma ideia, mas por caractere.
- **tempo de processamento**: tempo gasto para transcrever cada arquivo.
- **duração do áudio**: duração real do exemplo.
- **RTF — Real-Time Factor**: tempo de processamento dividido pela duração do áudio.

Interpretação:

```text
WER/CER menor = melhor reconhecimento
RTF < 1         = mais rápido que tempo real
```

WER é a métrica principal para transcrição, mas CER pode ser útil para nomes, palavras curtas e diferenças de pontuação. Para regionalismos, convém acrescentar uma métrica de acerto de palavras-chave.

### 9.2 Formato do manifesto

O arquivo CSV deve ter pelo menos:

```csv
audio,text
audio/bah_01.wav,Bah tchê, vamos embora.
audio/guri_01.wav,O guri chegou cedo.
```

### 9.3 Comandos

```powershell
cd C:\caminho\para\voice_chatbot_ptbr
.\.venv\Scripts\Activate.ps1
python benchmark.py manifest.csv --limit 20
python benchmark.py manifest.csv --output benchmark_results\freds0.jsonl
```

Depois, altere `ASR_MODEL`, reinicie o processo Python e rode exatamente o mesmo manifesto:

```powershell
python benchmark.py manifest.csv --output benchmark_results\rodrigo.jsonl
```

Para uma comparação válida, mantenha iguais o hardware, o manifesto, a normalização, o idioma, a tarefa e os parâmetros de decodificação. É útil separar resultados por duração, ruído, espontaneidade e região do falante.

## 10. Datasets e avaliação em português

### Common Voice

É útil para uma primeira comparação, mas costuma conter fala lida e frases curtas. Serve bem para medir desempenho básico, mas não representa completamente conversa espontânea nem sotaques regionais.

### CORAA

O CORAA possui aproximadamente 290 horas de fala em português brasileiro, incluindo fala espontânea e preparada. É uma opção mais representativa para avaliação geral.

Referência: [CORAA](https://huggingface.co/papers/2110.15731).

### NURC-SP

O NURC-SP contém fala espontânea e dados sociolinguísticos de São Paulo. É valioso para testar conversação natural, mas não é um conjunto gaúcho.

Referência: [NURC-SP Audio Corpus](https://github.com/nilc-nlp/nurc-sp-audio-corpus).

### MuPe-Diversidades / MuPe-RS

O MuPe é a melhor opção imediata para o objetivo regional. Ele disponibiliza amostras públicas de diferentes estados e inclui material do Rio Grande do Sul, com metadados de falantes. O subconjunto MuPe-RS é pequeno para treinamento, mas adequado para um teste direcionado.

Referência: [MuPe-Diversidades](https://github.com/nilc-nlp/MuPe-Diversidades/).

### VARSUL

O VARSUL é muito relevante para variação linguística no Sul e inclui cidades do Rio Grande do Sul, como Porto Alegre, Flores da Cunha, Panambi e São Borja. Porém, o acesso ao áudio é restrito e a página bloqueia o download direto. O caminho adequado é contato institucional e solicitação de acesso.

Referência: [VARSUL](https://www.varsul.org.br/).

### BDS Pampa

A BDS Pampa é outra fonte interessante para fala da fronteira e da campanha gaúcha, com áudio e transcrições ortográficas. O acesso pode exigir contato ou procedimentos acadêmicos.

Referência: [artigo sobre a BDS Pampa](https://revistas.gel.org.br/rg/article/view/2107).

### Spoltech

O Spoltech tem falantes de várias regiões e participação de instituições do Sul, mas não é um dataset exclusivamente gaúcho. O acesso pode ser restrito ou pago.

Referência: [LDC Spoltech](https://catalog.ldc.upenn.edu/LDC2006S16).

## 11. Protocolo recomendado para MuPe-RS

1. Separar os áudios por falante, evitando que a mesma pessoa apareça no conjunto de comparação e em qualquer ajuste posterior.
2. Usar as transcrições de referência exatamente como fornecidas, criando uma versão normalizada separada.
3. Rodar `freds0/distil-whisper-large-v3-ptbr` e `RodrigoFardin/whisper-small-pt-br` com o mesmo manifesto.
4. Registrar WER, CER, RTF, duração e erros por arquivo.
5. Criar uma análise específica das palavras regionais.
6. Inspecionar manualmente exemplos em que o modelo apaga interjeições, troca vogais, junta palavras ou altera nomes próprios.

O MuPe-RS provavelmente será pequeno demais para concluir que um modelo é universalmente melhor, mas é suficiente para responder qual modelo se comporta melhor no cenário regional do projeto.

## 12. Estado atual e recomendação

Para o estado atual do protótipo:

- **STT principal:** `freds0/distil-whisper-large-v3-ptbr`, porque foi o melhor compromisso observado entre qualidade e velocidade.
- **STT de comparação leve:** `RodrigoFardin/whisper-small-pt-br`.
- **Baseline simples:** `faster-whisper small` ou `medium`.
- **LLM:** `llama3.1:8b` via Ollama, substituível por outro modelo local.
- **TTS:** Kokoro-82M com `pf_dora`, por ser leve e fácil de executar localmente.
- **Avaliação regional:** começar pelo MuPe-RS e complementar posteriormente com VARSUL, BDS Pampa ou gravações próprias consentidas.

O principal ponto em aberto não é mais a arquitetura básica, mas a avaliação regional e a escolha de uma voz TTS que tenha sotaque gaúcho convincente. Para isso, a solução mais prática tende a ser uma voz de referência gaúcha, obtida com consentimento, usando um modelo de clonagem compatível com português brasileiro.
