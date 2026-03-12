# Audio Transcriber v2.0.0

Skill para Claude Code que transcreve vídeos e áudios de reuniões para Markdown profissional com identificação de locutores e contexto visual.

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

```bash
# Engine de transcrição (Apple Silicon)
pip install mlx-whisper

# Diarização
pip install speechbrain scikit-learn soundfile

# Conversão de formatos + extração de frames
brew install ffmpeg

# YouTube (opcional — transcrição via legendas)
claude mcp add youtube-transcript -- npx -y @sinco-lab/mcp-youtube-transcript

# YouTube fallback (opcional — quando não houver legendas)
pip install yt-dlp
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
