#!/usr/bin/env bash

# Audio Transcriber v2.0.0 - Requirements Installation Script
# Installs MLX Whisper + SpeechBrain + FFmpeg for Apple Silicon

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 Audio Transcriber v2.0.0 — Dependency Installation${NC}"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.9+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Python ${PYTHON_VERSION}${NC}"

# Check pip
if ! python3 -m pip --version &>/dev/null; then
    echo -e "${RED}❌ pip not found${NC}"
    exit 1
fi

echo ""

# ── MLX Whisper (transcription engine) ──────────────────────────
echo -e "${BLUE}📦 [1/4] MLX Whisper (transcrição)...${NC}"
if python3 -c "import mlx_whisper" 2>/dev/null; then
    echo -e "${GREEN}✅ mlx-whisper já instalado${NC}"
else
    echo -e "${BLUE}   Instalando mlx-whisper...${NC}"
    python3 -m pip install mlx-whisper --quiet 2>/dev/null \
        || python3 -m pip install --user --break-system-packages mlx-whisper --quiet 2>/dev/null \
        || { echo -e "${RED}❌ Falha ao instalar mlx-whisper${NC}"; exit 1; }
    echo -e "${GREEN}✅ mlx-whisper instalado${NC}"
fi

# ── SpeechBrain + deps (diarization) ───────────────────────────
echo ""
echo -e "${BLUE}📦 [2/4] SpeechBrain + scikit-learn + soundfile (diarização)...${NC}"
if python3 -c "from speechbrain.inference.speaker import EncoderClassifier" 2>/dev/null; then
    echo -e "${GREEN}✅ speechbrain já instalado${NC}"
else
    echo -e "${BLUE}   Instalando speechbrain scikit-learn soundfile...${NC}"
    python3 -m pip install speechbrain scikit-learn soundfile --quiet 2>/dev/null \
        || python3 -m pip install --user --break-system-packages speechbrain scikit-learn soundfile --quiet 2>/dev/null \
        || { echo -e "${RED}❌ Falha ao instalar speechbrain${NC}"; exit 1; }
    echo -e "${GREEN}✅ speechbrain instalado${NC}"
fi

# ── FFmpeg (format conversion + frame extraction) ──────────────
echo ""
echo -e "${BLUE}📦 [3/4] FFmpeg (conversão + frames)...${NC}"
if command -v ffmpeg &>/dev/null; then
    echo -e "${GREEN}✅ ffmpeg já instalado ($(ffmpeg -version 2>&1 | head -1 | cut -d' ' -f3))${NC}"
else
    if [[ "$OSTYPE" == "darwin"* ]] && command -v brew &>/dev/null; then
        echo -e "${BLUE}   Instalando via Homebrew...${NC}"
        brew install ffmpeg --quiet
        echo -e "${GREEN}✅ ffmpeg instalado${NC}"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo -e "${YELLOW}⚠️  ffmpeg não encontrado. Instale com:${NC}"
        echo "     sudo apt install ffmpeg   # Debian/Ubuntu"
        echo "     sudo yum install ffmpeg   # CentOS/RHEL"
    else
        echo -e "${YELLOW}⚠️  ffmpeg não encontrado. Instale manualmente.${NC}"
    fi
fi

# ── yt-dlp (YouTube fallback) ──────────────────────────────────
echo ""
echo -e "${BLUE}📦 [4/4] yt-dlp (YouTube fallback, opcional)...${NC}"
if command -v yt-dlp &>/dev/null || python3 -c "import yt_dlp" 2>/dev/null; then
    echo -e "${GREEN}✅ yt-dlp já instalado${NC}"
else
    echo -e "${BLUE}   Instalando yt-dlp...${NC}"
    python3 -m pip install yt-dlp --quiet 2>/dev/null \
        || python3 -m pip install --user --break-system-packages yt-dlp --quiet 2>/dev/null \
        || echo -e "${YELLOW}⚠️  yt-dlp não instalado (opcional — necessário apenas para YouTube sem legendas)${NC}"
    echo -e "${GREEN}✅ yt-dlp instalado${NC}"
fi

# ── Verify ──────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}🔍 Verificando instalação...${NC}"

ERRORS=0

python3 -c "import mlx_whisper" 2>/dev/null \
    && echo -e "${GREEN}✅ mlx-whisper OK${NC}" \
    || { echo -e "${RED}❌ mlx-whisper FALHOU${NC}"; ERRORS=$((ERRORS+1)); }

python3 -c "from speechbrain.inference.speaker import EncoderClassifier" 2>/dev/null \
    && echo -e "${GREEN}✅ speechbrain OK${NC}" \
    || { echo -e "${RED}❌ speechbrain FALHOU${NC}"; ERRORS=$((ERRORS+1)); }

command -v ffmpeg &>/dev/null \
    && echo -e "${GREEN}✅ ffmpeg OK${NC}" \
    || { echo -e "${YELLOW}⚠️  ffmpeg não disponível (necessário para vídeo)${NC}"; }

if [[ $ERRORS -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ Instalação completa! Tudo pronto.${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "🚀 Use no Claude Code:"
    echo "   > transcreva este vídeo: reuniao.mp4"
    echo "   > /audio-transcriber reuniao.mp4"
else
    echo ""
    echo -e "${RED}❌ $ERRORS dependência(s) falharam. Verifique os erros acima.${NC}"
    exit 1
fi
