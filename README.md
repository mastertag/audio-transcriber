# audio-transcriber

A Claude Code skill that transcribes audio, video, and YouTube content to professional Markdown with automatic speaker diarization and meeting minutes generation.

**100% local. Zero API calls. Zero cost. Total privacy.**

Everything runs on your machine — no external APIs, no tokens, no cloud services, no internet required (except for YouTube). Your audio never leaves your Mac.

## Why This Skill?

| | **This skill** | Typical alternatives |
|---|---|---|
| **Cost** | Free forever | Pay-per-minute API fees |
| **Privacy** | Audio never leaves your machine | Audio uploaded to cloud |
| **Speed** | ~10x real-time (Apple Silicon GPU) | Varies, often slower on CPU |
| **API keys** | None required | OpenAI, HuggingFace, etc. |
| **Internet** | Not needed (except YouTube) | Required for cloud APIs |
| **Diarization** | Built-in, no token needed | Often requires paid APIs |

## Features

- **Zero API, zero cost** — MLX Whisper runs entirely on Apple Silicon GPU, no cloud needed
- **YouTube support** — instant transcription via captions (MCP) or audio download (yt-dlp)
- **Apple Silicon optimized** — MLX framework leverages GPU/Neural Engine for 10x real-time speed
- **Speaker diarization** — SpeechBrain ECAPA-TDNN identifies speakers without any API keys or tokens
- **Interactive speaker naming** — after diarization, asks you to name each speaker
- **Automatic meeting minutes** — generates summaries with topics, decisions, and action items
- **Multiple engines** — MLX Whisper (default), WhisperX, Faster-Whisper, OpenAI Whisper
- **Model selection** — tiny/base/small/medium/large with automatic recommendation based on RAM
- **Clean output** — temp files go to `/tmp/`, only final `.md` files stay in your directory

## Quick Install

```bash
npx skills add mastertag/audio-transcriber
```

## Requirements

```bash
# Main engine (Apple Silicon — runs on GPU, no API needed)
pip install mlx-whisper

# Speaker diarization (lightweight, no HuggingFace token needed)
pip install speechbrain scikit-learn soundfile

# Format conversion
brew install ffmpeg

# YouTube support (optional)
claude mcp add youtube-transcript -- npx -y @sinco-lab/mcp-youtube-transcript
pip install yt-dlp
```

## Usage

Just ask Claude Code:

- "Transcribe this audio" + attach file
- "Transcribe this YouTube video: https://youtube.com/watch?v=..."
- "Generate meeting minutes from this recording"
- "Who speaks in this audio?"

## Benchmarks (Apple M2, 8GB RAM)

Test: ~85 min meeting recording

| Pipeline | Time | Speed | Quality |
|----------|------|-------|---------|
| WhisperX + pyannote | ~91 min | 0.9x | Poor |
| MLX Whisper base + SpeechBrain | ~9 min | 9.4x | Good |
| **MLX Whisper small + SpeechBrain** | **~9.5 min** | **8.9x** | **Very good** |

> 58 min of audio transcribed + diarized in 5.6 min on an M2 MacBook with just 8GB RAM.

## How It Works

```
Input (file or YouTube URL)
  |
  +-- YouTube? --> MCP youtube-transcript (instant, no download)
  |                   \-- No captions? --> yt-dlp audio download
  |
  +-- MLX Whisper transcription (Apple Silicon GPU, 100% local)
  |
  +-- SpeechBrain diarization (speaker embeddings + clustering, no API)
  |
  +-- Interactive speaker naming ("SPEAKER_00 is John, SPEAKER_01 is Mary")
  |
  +-- Markdown transcript + automatic meeting minutes
  |
  +-- Cleanup (temp files in /tmp/, only .md files remain)
```

## Model Selection

| Model | Size | RAM | Quality | Best for |
|-------|------|-----|---------|----------|
| `tiny` | ~75 MB | ~500 MB | Basic | Quick drafts, low-end hardware |
| `base` | ~140 MB | ~800 MB | Good | Fast results with decent quality |
| **`small`** | **~460 MB** | **~1.5 GB** | **Very good** | **Best balance (default)** |
| `medium` | ~1.5 GB | ~3 GB | Excellent | 16GB+ RAM Macs |
| `large` | ~1.5 GB | ~4 GB | Superior | 16GB+ RAM Macs |

## License

MIT
