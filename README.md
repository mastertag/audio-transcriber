# audio-transcriber

A Claude Code skill that transcribes audio, video, and YouTube content to professional Markdown with automatic speaker diarization and meeting minutes generation.

## Features

- **YouTube support** — instant transcription via captions (MCP) or audio download (yt-dlp)
- **Apple Silicon optimized** — MLX Whisper uses GPU/Neural Engine for 10x real-time speed
- **Speaker diarization** — SpeechBrain ECAPA-TDNN identifies speakers without any API keys
- **Interactive speaker naming** — after diarization, asks you to name each speaker
- **Automatic meeting minutes** — generates summaries with topics, decisions, and action items
- **Multiple engines** — MLX Whisper (default), WhisperX, Faster-Whisper, OpenAI Whisper
- **Model selection** — tiny/base/small/medium/large with automatic recommendation based on RAM

## Quick Install

```bash
npx skills add mastertag/audio-transcriber
```

## Requirements

```bash
# Main engine (Apple Silicon)
pip install mlx-whisper

# Speaker diarization
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

## How It Works

```
Input (file or YouTube URL)
  |
  +-- YouTube? --> MCP youtube-transcript (instant)
  |                   \-- No captions? --> yt-dlp download
  |
  +-- MLX Whisper transcription (Apple Silicon GPU)
  |
  +-- SpeechBrain diarization (speaker embeddings + clustering)
  |
  +-- Interactive speaker naming
  |
  +-- Markdown transcript + automatic meeting minutes
  |
  +-- Cleanup (temp files in /tmp/, only .md files remain)
```

## License

MIT
