# Audio Transcriber v2.0.0

A Claude Code skill that transcribes meeting videos and audios to professional Markdown with speaker identification and visual context.

## Installation

### Option 1: Clone directly (recommended)

```bash
git clone https://github.com/mastertag/audio-transcriber.git ~/.claude/skills/audio-transcriber
```

### Option 2: Symlink (if you keep skills in a separate folder)

```bash
git clone https://github.com/mastertag/audio-transcriber.git ~/my-skills/audio-transcriber
ln -s ~/my-skills/audio-transcriber ~/.claude/skills/audio-transcriber
```

### Option 3: Project-specific (only for one project)

```bash
cd /path/to/your/project
git clone https://github.com/mastertag/audio-transcriber.git .claude/skills/audio-transcriber
```

After installing, verify it appears in Claude Code by typing `/` and looking for `audio-transcriber`.

Python dependencies (mlx-whisper, speechbrain, ffmpeg, etc.) are **installed automatically** on first run. If you prefer to install them upfront:

```bash
bash ~/.claude/skills/audio-transcriber/scripts/install-requirements.sh
```

## Why does this project exist?

We often receive meeting recordings from other people — a video file from Google Meet, Zoom, Teams, or even a phone recording. Without having attended the call or used real-time transcription plugins, we're left without tools to extract the meeting content in a useful way for task development or documentation.

This skill solves exactly that problem: you pass the video/audio file and it automatically generates the complete transcription with identified speakers, meeting minutes with decisions and action items, and — for videos — captures frames at moments where someone is demonstrating something on screen.

## Features

- **Local transcription** via MLX Whisper (Apple Silicon GPU) — 100% offline processing
- **Diarization** via SpeechBrain ECAPA-TDNN — identifies who is speaking without HuggingFace token
- **YouTube** — extracts transcripts instantly via MCP or downloads audio with yt-dlp
- **Visual context** — detects moments where speakers reference visual elements (screens, clicks, demos, slides) and extracts video frames for analysis
- **Automatic minutes** — generates summary with topics, decisions and action items via Claude
- **Interactive identification** — asks the user who each speaker is after diarization

## How it works (steps)

### 1. Model selection (interactive menu)
The skill presents a menu to choose the transcription model:
- **small** (recommended) — ~460 MB, very good quality
- **base** — ~140 MB, faster
- **medium** — ~1.5 GB, excellent (requires 16GB+ RAM)
- **tiny** — ~75 MB, basic and fast

### 2. Transcription
MLX Whisper transcribes the audio using the Apple Silicon GPU. For a ~58 min video, it takes ~5 min.

### 3. Diarization (speaker identification)
SpeechBrain extracts voice embeddings in 3-second windows and clusters by similarity. Identifies who is speaking in each segment. For ~58 min, it takes ~1.5 min.

### 4. Speaker identification
The skill interactively asks who each detected SPEAKER is, showing representative excerpts to help with identification.

### 5. Visual context detection (videos only)
Analyzes the transcription to find moments where speakers reference something visual:
- **Screen references**: "here", "this part", "on this button"
- **Demonstrations**: "I clicked here", "I'll open", "drag it here"
- **Observation prompts**: "look", "see?", "did you see?"
- **Reactions**: "wow!", "whoa", "oops"
- **Screen changes**: "it appeared", "it loaded", "it bugged"
- **Navigation**: "go to", "access", "open"

The skill proactively suggests frame extraction to the user, showing how many moments it detected and examples.

### 6. Frame extraction and analysis
When the user confirms, FFmpeg extracts frames at relevant timestamps. Claude analyzes each image (multimodal) and generates visual context descriptions. Frames are saved in a local folder for review.

### 7. Markdown generation
The final transcription includes:
- Metadata (duration, language, model, speakers)
- Participants identified via video
- Transcription with timestamps and speakers
- Clickable `👁️` visual markers that open the corresponding image
- Inline images rendered in VS Code Markdown preview
- `[before]` / `[after]` links for action frames

### 8. Automatic minutes
Claude automatically generates minutes with context, topics, decisions and action items.

## Output structure

```
~/Downloads/
├── video-original.mp4
├── transcript-20260312-172245.md        # Transcription with inline images
├── ata-20260312-172245.md               # Minutes/summary
├── visual-cues-20260312-172245.json     # Visual moment metadata
└── frames-video-original/               # Extracted frames
    ├── frame-05-34-before.jpg
    ├── frame-05-34-action.jpg
    ├── frame-05-34-after.jpg
    └── ...
```

## Markdown format (VS Code friendly)

Moments with visual context appear like this in the markdown:

```markdown
**[05:34]** [👁️](frames-video/frame-05-34-action.jpg) It didn't load.

> 📸 **Visual context:** Figma — Landing Page with logos. Element didn't load.
>
> ![frame-05:34](frames-video/frame-05-34-action.jpg)
> [before](frames-video/frame-05-34-before.jpg) | [after](frames-video/frame-05-34-after.jpg)
```

In VS Code:
- The `👁️` is a clickable link that opens the image
- The image appears inline in the Markdown preview
- The `before`/`after` links let you see the transition

## Requirements

All dependencies are **installed automatically** on first run. You don't need to install anything manually — the skill detects what's missing and installs it.

Under the hood, it uses:
- `mlx-whisper` — transcription engine (Apple Silicon GPU)
- `speechbrain`, `scikit-learn`, `soundfile` — speaker diarization
- `ffmpeg` — format conversion + frame extraction
- `yt-dlp` — YouTube audio download (fallback when no captions)

Optional (for instant YouTube transcription via captions):
```bash
claude mcp add youtube-transcript -- npx -y @sinco-lab/mcp-youtube-transcript
```

## Benchmarks (Apple M2, 8GB RAM)

Test video: ~58 min meeting (297 MB, 720p)

| Step | Time |
|------|------|
| Transcription (MLX Whisper small) | ~5 min |
| Diarization (SpeechBrain) | ~1.5 min |
| Frame extraction (FFmpeg) | ~10 sec |
| Visual analysis (Claude) | ~1 min |
| **Total** | **~8 min** |

## Usage

In Claude Code:

```
> transcribe this video: meeting.mp4
> /audio-transcriber meeting.mp4
```

Also accepts:
- YouTube links
- Audio files (MP3, WAV, M4A, OGG, FLAC)
- `--model tiny` for faster transcription

## Input sources

| Source | Method | Speed |
|--------|--------|-------|
| YouTube URL | MCP youtube-transcript | Instant |
| YouTube (no captions) | yt-dlp + MLX Whisper | Moderate |
| Local file (audio) | MLX Whisper + SpeechBrain | Fast |
| Local file (video) | MLX Whisper + SpeechBrain + Visual Cues | Fast |

## License

MIT

---

# Audio Transcriber v2.0.0 — Português

Skill para Claude Code que transcreve vídeos e áudios de reuniões para Markdown profissional com identificação de locutores e contexto visual.

## Instalação

### Opção 1: Clone direto (recomendado)

```bash
git clone https://github.com/mastertag/audio-transcriber.git ~/.claude/skills/audio-transcriber
```

### Opção 2: Symlink (se você mantém skills em pasta separada)

```bash
git clone https://github.com/mastertag/audio-transcriber.git ~/my-skills/audio-transcriber
ln -s ~/my-skills/audio-transcriber ~/.claude/skills/audio-transcriber
```

### Opção 3: Específico de um projeto

```bash
cd /caminho/do/seu/projeto
git clone https://github.com/mastertag/audio-transcriber.git .claude/skills/audio-transcriber
```

Após instalar, verifique que aparece no Claude Code digitando `/` e procurando por `audio-transcriber`.

As dependências Python (mlx-whisper, speechbrain, ffmpeg, etc.) são **instaladas automaticamente** na primeira execução. Se preferir instalar antes:

```bash
bash ~/.claude/skills/audio-transcriber/scripts/install-requirements.sh
```

## Por que esse projeto existe?

Muitas vezes recebemos gravações de reuniões feitas por outras pessoas — um arquivo de vídeo do Google Meet, Zoom, Teams, ou até uma gravação de celular. Sem ter participado da call ou sem ter usado plugins de transcrição em tempo real, ficamos sem ferramentas para extrair o conteúdo dessa reunião de forma útil para desenvolvimento de tarefas ou documentação.

Este skill resolve exatamente esse problema: você passa o arquivo de vídeo/áudio e ele gera automaticamente a transcrição completa com locutores identificados, ata de reunião com decisões e action items, e — para vídeos — captura frames nos momentos onde alguém está demonstrando algo na tela.

## Funcionalidades

- **Transcrição local** via MLX Whisper (Apple Silicon GPU) — processamento 100% offline
- **Diarização** via SpeechBrain ECAPA-TDNN — identifica quem está falando sem token do HuggingFace
- **YouTube** — extrai transcrições instantaneamente via MCP ou baixa áudio com yt-dlp
- **Contexto visual** — detecta momentos onde locutores referenciam elementos visuais (telas, cliques, demos, slides) e extrai frames do vídeo para análise
- **Ata automática** — gera resumo com tópicos, decisões e action items via Claude
- **Identificação interativa** — pergunta ao usuário quem é cada locutor após a diarização

## Como funciona (etapas)

### 1. Escolha do modelo (menu interativo)
O skill apresenta um menu para escolher o modelo de transcrição:
- **small** (recomendado) — ~460 MB, qualidade muito boa
- **base** — ~140 MB, mais rápido
- **medium** — ~1.5 GB, excelente (requer 16GB+ RAM)
- **tiny** — ~75 MB, básico e rápido

### 2. Transcrição
MLX Whisper transcreve o áudio usando a GPU do Apple Silicon. Para um vídeo de ~58 min, leva ~5 min.

### 3. Diarização (identificação de locutores)
SpeechBrain extrai embeddings de voz em janelas de 3 segundos e agrupa por similaridade. Identifica quem está falando em cada segmento. Para ~58 min, leva ~1.5 min.

### 4. Identificação dos locutores
O skill pergunta interativamente quem é cada SPEAKER detectado, mostrando trechos representativos para ajudar na identificação.

### 5. Detecção de contexto visual (apenas vídeos)
Analisa a transcrição para encontrar momentos onde os locutores referenciam algo visual:
- **Referências a tela**: "aqui", "essa parte", "nesse botão"
- **Demonstrações**: "cliquei aqui", "vou abrir", "arrasta pra cá"
- **Convites a observar**: "olha", "tá vendo?", "viu?"
- **Reações/espanto**: "nossa!", "vixe", "opa"
- **Mudanças na tela**: "apareceu", "carregou", "bugou"
- **Navegação**: "entra em", "vai em", "acessa"

O skill sugere proativamente ao usuário a extração de frames, mostrando quantos momentos detectou e exemplos.

### 6. Extração e análise de frames
Quando o usuário confirma, o FFmpeg extrai frames nos timestamps relevantes. Claude analisa cada imagem (multimodal) e gera descrições do contexto visual. Os frames são salvos numa pasta local para conferência.

### 7. Geração do Markdown
A transcrição final inclui:
- Metadados (duração, idioma, modelo, locutores)
- Participantes identificados via vídeo
- Transcrição com timestamps e locutores
- Marcadores visuais `👁️` clicáveis que abrem a imagem correspondente
- Imagens inline renderizadas no preview do VS Code
- Links `[antes]` / `[depois]` para frames de ação

### 8. Ata automática
Claude gera automaticamente uma ata com contexto, tópicos, decisões e action items.

## Estrutura de saída

```
~/Downloads/
├── video-original.mp4
├── transcript-20260312-172245.md        # Transcrição com imagens inline
├── ata-20260312-172245.md               # Ata/resumo
├── visual-cues-20260312-172245.json     # Metadados dos momentos visuais
└── frames-video-original/               # Frames extraídos
    ├── frame-05-34-before.jpg
    ├── frame-05-34-action.jpg
    ├── frame-05-34-after.jpg
    └── ...
```

## Formato do Markdown (VS Code friendly)

Os momentos com contexto visual aparecem assim no markdown:

```markdown
**[05:34]** [👁️](frames-video/frame-05-34-action.jpg) Não carregou.

> 📸 **Contexto visual:** Figma — Landing Page com logos. Elemento não carregou.
>
> ![frame-05:34](frames-video/frame-05-34-action.jpg)
> [antes](frames-video/frame-05-34-before.jpg) | [depois](frames-video/frame-05-34-after.jpg)
```

No VS Code:
- O `👁️` é um link clicável que abre a imagem
- A imagem aparece inline no preview do Markdown
- Os links `antes`/`depois` permitem ver a transição

## Requisitos

Todas as dependências são **instaladas automaticamente** na primeira execução. Você não precisa instalar nada manualmente — o skill detecta o que está faltando e instala.

Por baixo dos panos, usa:
- `mlx-whisper` — engine de transcrição (Apple Silicon GPU)
- `speechbrain`, `scikit-learn`, `soundfile` — diarização de locutores
- `ffmpeg` — conversão de formatos + extração de frames
- `yt-dlp` — download de áudio do YouTube (fallback quando não houver legendas)

Opcional (para transcrição instantânea do YouTube via legendas):
```bash
claude mcp add youtube-transcript -- npx -y @sinco-lab/mcp-youtube-transcript
```

## Benchmarks (Apple M2, 8GB RAM)

Vídeo de teste: ~58 min de reunião (297 MB, 720p)

| Etapa | Tempo |
|-------|-------|
| Transcrição (MLX Whisper small) | ~5 min |
| Diarização (SpeechBrain) | ~1.5 min |
| Extração de frames (FFmpeg) | ~10 seg |
| Análise visual (Claude) | ~1 min |
| **Total** | **~8 min** |

## Uso

No Claude Code:

```
> transcreva esse vídeo: reuniao.mp4
> /audio-transcriber reuniao.mp4
```

Também aceita:
- Links do YouTube
- Arquivos de áudio (MP3, WAV, M4A, OGG, FLAC)
- `--model tiny` para transcrição mais rápida

## Fontes de entrada

| Fonte | Método | Velocidade |
|-------|--------|-----------|
| YouTube URL | MCP youtube-transcript | Instantâneo |
| YouTube (sem legenda) | yt-dlp + MLX Whisper | Moderado |
| Arquivo local (áudio) | MLX Whisper + SpeechBrain | Rápido |
| Arquivo local (vídeo) | MLX Whisper + SpeechBrain + Visual Cues | Rápido |

## Licença

MIT
