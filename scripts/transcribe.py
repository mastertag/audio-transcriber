#!/usr/bin/env python3
"""
Audio Transcriber v2.0.0
Transcreve áudio para texto com diarização real (identificação de locutores).
Gera atas/resumos usando LLM.
"""

import os
import sys
import json
import subprocess
import shutil
import time
from datetime import datetime
from pathlib import Path

# Rich for beautiful terminal output
try:
    from rich.console import Console
    from rich.prompt import Prompt
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Installing rich for better UI...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--user", "rich"], check=False)
    from rich.console import Console
    from rich.prompt import Prompt
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich import print as rprint

# tqdm for progress bars
try:
    from tqdm import tqdm
except ImportError:
    print("⚠️  Installing tqdm for progress bars...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--user", "tqdm"], check=False)
    from tqdm import tqdm

# Whisper engines
TRANSCRIBER = None
WHISPERX_AVAILABLE = False

try:
    import whisperx
    TRANSCRIBER = "whisperx"
    WHISPERX_AVAILABLE = True
except ImportError:
    pass

if not TRANSCRIBER:
    try:
        from faster_whisper import WhisperModel
        TRANSCRIBER = "faster-whisper"
    except ImportError:
        try:
            import whisper
            TRANSCRIBER = "whisper"
        except ImportError:
            print("❌ Nenhum engine de transcrição encontrado!")
            print("   Instale: pip install whisperx  (recomendado, com diarização)")
            print("   Ou:      pip install faster-whisper")
            sys.exit(1)

console = Console()

# Template padrão RISEN para fallback
DEFAULT_MEETING_PROMPT = """
Role: Você é um transcritor profissional especializado em documentação.

Instructions: Transforme a transcrição fornecida em um documento estruturado e profissional.

Steps:
1. Identifique o tipo de conteúdo (reunião, palestra, entrevista, etc.)
2. Extraia os principais tópicos e pontos-chave
3. Identifique participantes/speakers (se aplicável)
4. Extraia decisões tomadas e ações definidas (se reunião)
5. Organize em formato apropriado com seções claras
6. Use Markdown para formatação profissional

End Goal: Documento final bem estruturado, legível e pronto para distribuição.

Narrowing:
- Mantenha objetividade e clareza
- Preserve contexto importante
- Use formatação Markdown adequada
- Inclua timestamps relevantes quando aplicável
"""


def format_timestamp(seconds):
    """Formata segundos em HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def get_hf_token():
    """Obtém o token do HuggingFace de variáveis de ambiente ou arquivo."""
    # 1. Variável de ambiente
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if token:
        return token

    # 2. Arquivo ~/.hf_token ou ~/.hftoken
    for filename in [".hf_token", ".hftoken"]:
        hf_token_file = Path.home() / filename
        if hf_token_file.exists():
            token = hf_token_file.read_text().strip()
            if token:
                return token

    # 3. huggingface-cli login (cached token)
    try:
        from huggingface_hub import HfFolder
        token = HfFolder.get_token()
        if token:
            return token
    except Exception:
        pass

    return None


def detect_cli_tool():
    """Detecta qual CLI de LLM está disponível (claude > gh copilot)."""
    if shutil.which('claude'):
        return 'claude'
    elif shutil.which('gh'):
        result = subprocess.run(['gh', 'copilot', '--version'],
                                capture_output=True, text=True)
        if result.returncode == 0:
            return 'gh-copilot'
    return None


def invoke_prompt_engineer(raw_prompt, timeout=90):
    """Invoca prompt-engineer skill via CLI para melhorar/gerar prompts."""
    try:
        console.print("[dim]   Invocando prompt-engineer...[/dim]")
        result = subprocess.run(
            ['gh', 'copilot', 'suggest', '-t', 'shell', raw_prompt],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        else:
            console.print("[yellow]⚠️  prompt-engineer não respondeu, usando template padrão[/yellow]")
            return DEFAULT_MEETING_PROMPT
    except subprocess.TimeoutExpired:
        console.print(f"[red]⚠️  Timeout após {timeout}s, usando template padrão[/red]")
        return DEFAULT_MEETING_PROMPT
    except Exception as e:
        console.print(f"[red]⚠️  Erro ao invocar prompt-engineer: {e}[/red]")
        return DEFAULT_MEETING_PROMPT


def handle_prompt_workflow(user_prompt, transcript):
    """Gerencia fluxo completo de prompts com prompt-engineer."""
    prompt_engineer_available = os.path.exists(
        os.path.expanduser('~/.copilot/skills/prompt-engineer/SKILL.md')
    )

    if user_prompt:
        console.print("\n[cyan]📝 Prompt fornecido pelo usuário[/cyan]")
        console.print(Panel(user_prompt[:300] + ("..." if len(user_prompt) > 300 else ""),
                           title="Prompt original", border_style="dim"))
        if prompt_engineer_available:
            console.print("\n[cyan]🔧 Melhorando prompt com prompt-engineer...[/cyan]")
            improved_prompt = invoke_prompt_engineer(f"melhore este prompt:\n\n{user_prompt}")
            console.print("\n[green]✨ Versão melhorada:[/green]")
            console.print(Panel(improved_prompt[:500], title="Prompt otimizado", border_style="green"))
            confirm = Prompt.ask("\n💡 Usar versão melhorada?", choices=["s", "n"], default="s")
            return improved_prompt if confirm == "s" else user_prompt
        else:
            return user_prompt
    else:
        console.print("\n[yellow]⚠️  Nenhum prompt fornecido.[/yellow]")
        if not prompt_engineer_available:
            return DEFAULT_MEETING_PROMPT
        console.print("Posso analisar o transcript e sugerir um formato de resumo/ata?")
        generate = Prompt.ask("\n💡 Gerar prompt automaticamente?", choices=["s", "n"], default="s")
        if generate == "n":
            return None
        console.print("\n[cyan]🔍 Analisando transcript...[/cyan]")
        suggestion_meta_prompt = f"Analise este transcript e sugira formato de saída:\n{transcript[:4000]}"
        suggested_type = invoke_prompt_engineer(suggestion_meta_prompt)
        console.print(Panel(suggested_type, title="Análise", border_style="green"))
        confirm_type = Prompt.ask("\n💡 Usar este formato?", choices=["s", "n"], default="s")
        if confirm_type == "n":
            return DEFAULT_MEETING_PROMPT
        final_meta_prompt = f"Crie um prompt completo para:\n{suggested_type}"
        generated_prompt = invoke_prompt_engineer(final_meta_prompt)
        console.print(Panel(generated_prompt[:600], title="Preview", border_style="green"))
        confirm_final = Prompt.ask("\n💡 Usar este prompt?", choices=["s", "n"], default="s")
        return generated_prompt if confirm_final == "s" else DEFAULT_MEETING_PROMPT


def process_with_llm(transcript, prompt, cli_tool='claude', timeout=300):
    """Processa transcript com LLM usando prompt fornecido."""
    full_prompt = f"{prompt}\n\n---\n\nTranscrição:\n\n{transcript}"
    try:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
            progress.add_task(description=f"🤖 Processando com {cli_tool}...", total=None)
            if cli_tool == 'claude':
                result = subprocess.run(['claude', '-'], input=full_prompt,
                                        capture_output=True, text=True, timeout=timeout)
            elif cli_tool == 'gh-copilot':
                result = subprocess.run(['gh', 'copilot', 'suggest', '-t', 'shell', full_prompt],
                                        capture_output=True, text=True, timeout=timeout)
            else:
                raise ValueError(f"CLI tool desconhecido: {cli_tool}")
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            console.print(f"[red]❌ Erro ao processar com {cli_tool}[/red]")
            console.print(f"[dim]{result.stderr[:200]}[/dim]")
            return None
    except subprocess.TimeoutExpired:
        console.print(f"[red]❌ Timeout após {timeout}s[/red]")
        return None
    except Exception as e:
        console.print(f"[red]❌ Erro: {e}[/red]")
        return None


def transcribe_with_whisperx(audio_file, model="medium", language="pt", diarize=False, hf_token=None):
    """
    Transcreve áudio usando WhisperX com diarização real.

    Returns:
        dict: {language, duration, segments: [{start, end, text, speaker?}], num_speakers}
    """
    import whisperx
    import torch

    device = "cpu"
    compute_type = "int8"

    # Detectar GPU
    if torch.cuda.is_available():
        device = "cuda"
        compute_type = "float16"
        console.print("[green]✅ GPU NVIDIA detectada[/green]")
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        # MPS não é totalmente suportado pelo whisperx, usar CPU
        console.print("[yellow]ℹ️  Apple Silicon detectado — usando CPU (MPS não suportado pelo WhisperX)[/yellow]")

    console.print(f"[cyan]🎙️  Carregando modelo {model} (WhisperX)...[/cyan]")
    start_load = time.time()
    model_obj = whisperx.load_model(model, device, compute_type=compute_type, language=language)
    console.print(f"[green]✅ Modelo carregado em {time.time() - start_load:.1f}s[/green]")

    # Step 1: Transcrever
    console.print(f"[cyan]🎙️  Transcrevendo...[/cyan]")
    start_transcribe = time.time()
    audio = whisperx.load_audio(audio_file)
    result = model_obj.transcribe(audio, batch_size=16, language=language)
    console.print(f"[green]✅ Transcrição base em {time.time() - start_transcribe:.1f}s[/green]")

    # Step 2: Alinhar timestamps
    console.print(f"[cyan]🔄 Alinhando timestamps...[/cyan]")
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
    console.print(f"[green]✅ Timestamps alinhados[/green]")

    num_speakers = 0

    # Step 3: Diarização (se solicitada)
    if diarize:
        if not hf_token:
            console.print("[red]❌ Token do HuggingFace necessário para diarização![/red]")
            console.print("[yellow]   Configure: export HF_TOKEN='hf_seu_token'[/yellow]")
            console.print("[yellow]   Ou salve em: ~/.hf_token[/yellow]")
            console.print("[yellow]   Continuando sem diarização...[/yellow]")
        else:
            console.print(f"[cyan]👥 Identificando locutores (diarização)...[/cyan]")
            start_diarize = time.time()
            diarize_model = whisperx.DiarizationPipeline(use_auth_token=hf_token, device=device)
            diarize_segments = diarize_model(audio)
            result = whisperx.assign_word_speakers(diarize_segments, result)

            # Contar speakers únicos
            speakers = set()
            for seg in result["segments"]:
                if "speaker" in seg:
                    speakers.add(seg["speaker"])
            num_speakers = len(speakers)

            console.print(f"[green]✅ {num_speakers} locutores identificados em {time.time() - start_diarize:.1f}s[/green]")

    # Montar dados de saída
    segments = []
    for seg in result["segments"]:
        entry = {
            "start": round(seg["start"], 2),
            "end": round(seg["end"], 2),
            "text": seg["text"].strip()
        }
        if "speaker" in seg:
            entry["speaker"] = seg["speaker"]
        segments.append(entry)

    duration = segments[-1]["end"] if segments else 0

    return {
        "language": result.get("language", language),
        "duration": duration,
        "segments": segments,
        "num_speakers": num_speakers
    }


def transcribe_with_faster_whisper(audio_file, model="medium", language="pt"):
    """
    Transcreve áudio usando faster-whisper (sem diarização).

    Returns:
        dict: {language, duration, segments: [{start, end, text}], num_speakers: 0}
    """
    from faster_whisper import WhisperModel

    console.print(f"[cyan]🎙️  Carregando modelo {model} (faster-whisper)...[/cyan]")
    start_load = time.time()
    model_obj = WhisperModel(model, device="cpu", compute_type="int8")
    console.print(f"[green]✅ Modelo carregado em {time.time() - start_load:.1f}s[/green]")

    console.print(f"[cyan]🎙️  Transcrevendo...[/cyan]")
    start_transcribe = time.time()

    segments_gen, info = model_obj.transcribe(
        audio_file, language=language,
        beam_size=5, vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )

    segments = []
    for segment in tqdm(segments_gen, desc="Segmentos", unit="seg"):
        segments.append({
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip()
        })

    console.print(f"[green]✅ Transcrição completa em {time.time() - start_transcribe:.1f}s[/green]")
    console.print(f"[green]   Idioma: {info.language} ({info.language_probability:.0%})[/green]")

    return {
        "language": info.language,
        "duration": info.duration,
        "segments": segments,
        "num_speakers": 0
    }


def transcribe_with_whisper(audio_file, model="medium", language="pt"):
    """Transcreve áudio usando whisper original (sem diarização)."""
    import whisper

    console.print(f"[cyan]🎙️  Carregando modelo {model} (whisper)...[/cyan]")
    model_obj = whisper.load_model(model)

    console.print(f"[cyan]🎙️  Transcrevendo...[/cyan]")
    result = model_obj.transcribe(audio_file, language=language, word_timestamps=True)

    segments = []
    for seg in result["segments"]:
        segments.append({
            "start": round(seg["start"], 2),
            "end": round(seg["end"], 2),
            "text": seg["text"].strip()
        })

    return {
        "language": result["language"],
        "duration": segments[-1]["end"] if segments else 0,
        "segments": segments,
        "num_speakers": 0
    }


def generate_markdown(data, audio_file, engine, model, elapsed, diarize=False):
    """Gera o conteúdo Markdown da transcrição."""
    basename = os.path.basename(audio_file)
    file_size = os.path.getsize(audio_file) / (1024 * 1024)
    word_count = sum(len(s["text"].split()) for s in data["segments"])

    md = []
    md.append(f"# Transcrição — {basename}\n")
    md.append(f"## Metadata\n")
    md.append(f"| Campo | Valor |")
    md.append(f"|-------|-------|")
    md.append(f"| **Arquivo** | {basename} |")
    md.append(f"| **Tamanho** | {file_size:.1f} MB |")
    md.append(f"| **Duração** | {format_timestamp(data['duration'])} |")
    md.append(f"| **Idioma** | {data['language']} |")
    md.append(f"| **Data de processamento** | {datetime.now().strftime('%Y-%m-%d %H:%M')} |")
    md.append(f"| **Palavras** | {word_count:,} |")
    md.append(f"| **Segmentos** | {len(data['segments'])} |")
    if data["num_speakers"] > 0:
        md.append(f"| **Locutores identificados** | {data['num_speakers']} |")
    md.append(f"| **Tempo de processamento** | {elapsed:.0f}s |")
    md.append(f"| **Engine** | {engine} (model: {model}) |")

    if diarize and data["num_speakers"] > 0:
        md.append(f"| **Diarização** | WhisperX + pyannote.audio |")

    md.append("")
    md.append("---\n")
    md.append("## Transcrição\n")

    # Mapear SPEAKER_XX para Locutor N
    speaker_map = {}
    speaker_counter = 0

    if diarize and data["num_speakers"] > 0:
        # Com diarização: agrupar por locutor
        current_speaker = None
        for seg in data["segments"]:
            speaker_id = seg.get("speaker", "unknown")

            if speaker_id not in speaker_map:
                speaker_counter += 1
                speaker_map[speaker_id] = f"Locutor {speaker_counter}"

            speaker_label = speaker_map[speaker_id]
            ts = format_timestamp(seg["start"])

            if speaker_id != current_speaker:
                md.append(f"**[{ts}] {speaker_label}**")
                current_speaker = speaker_id

            md.append(f"{seg['text']}\n")
    else:
        # Sem diarização: formato simples
        for seg in data["segments"]:
            ts = format_timestamp(seg["start"])
            md.append(f"**[{ts}]** {seg['text']}\n")

    # Adicionar legenda de locutores se houver diarização
    if speaker_map:
        md.append("\n---\n")
        md.append("## Locutores\n")
        md.append("| ID | Nome |")
        md.append("|-----|------|")
        for speaker_id, label in sorted(speaker_map.items(), key=lambda x: x[1]):
            md.append(f"| {label} | _(não identificado)_ |")
        md.append("")
        md.append("> Para renomear os locutores, diga ao Claude: ")
        md.append('> "Locutor 1 é João, Locutor 2 é Maria" e ele fará o replace no arquivo.\n')

    return "\n".join(md), word_count


def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(description="Audio Transcriber v2.0.0")
    parser.add_argument("audio_file", help="Arquivo de áudio/vídeo para transcrever")
    parser.add_argument("--prompt", help="Prompt customizado para processar transcript")
    parser.add_argument("--model", default="medium", help="Modelo Whisper (tiny/base/small/medium/large)")
    parser.add_argument("--language", "--idioma", default="pt", help="Idioma do áudio (default: pt)")
    parser.add_argument("--diarize", "--diarizar", action="store_true", help="Ativar diarização (identificar locutores)")
    parser.add_argument("--output-dir", help="Diretório de saída (default: mesmo do arquivo)")
    parser.add_argument("--srt", action="store_true", help="Gerar também arquivo .srt de legendas")
    parser.add_argument("--no-llm", action="store_true", help="Não processar com LLM (apenas transcript)")

    args = parser.parse_args()

    # Verificar arquivo existe
    if not os.path.exists(args.audio_file):
        console.print(f"[red]❌ Arquivo não encontrado: {args.audio_file}[/red]")
        sys.exit(1)

    # Output dir padrão = mesmo diretório do arquivo
    output_dir = args.output_dir or os.path.dirname(os.path.abspath(args.audio_file))

    console.print("[bold cyan]🎵 Audio Transcriber v2.0.0[/bold cyan]")
    console.print(f"[dim]Engine: {TRANSCRIBER} | Diarização: {'sim' if args.diarize else 'não'}[/dim]\n")

    file_size = os.path.getsize(args.audio_file) / (1024 * 1024)
    console.print(f"📂 Arquivo: {os.path.basename(args.audio_file)}")
    console.print(f"📊 Tamanho: {file_size:.1f} MB")

    # Verificar HF token se diarização solicitada
    hf_token = None
    if args.diarize:
        hf_token = get_hf_token()
        if not hf_token:
            console.print("\n[red]⚠️  Diarização requer token do HuggingFace![/red]")
            console.print("[yellow]   Opções:[/yellow]")
            console.print("[yellow]   1. export HF_TOKEN='hf_seu_token'[/yellow]")
            console.print("[yellow]   2. Salvar token em ~/.hf_token[/yellow]")
            console.print("[yellow]   3. huggingface-cli login[/yellow]")
            console.print("[yellow]   Token gratuito em: https://huggingface.co/settings/tokens[/yellow]")

            token_input = Prompt.ask("\n🔑 Cole seu token aqui (ou Enter para continuar sem diarização)")
            if token_input.strip():
                hf_token = token_input.strip()
                # Salvar para uso futuro
                hf_token_file = Path.home() / ".hf_token"
                hf_token_file.write_text(hf_token)
                console.print(f"[green]✅ Token salvo em {hf_token_file}[/green]")
            else:
                console.print("[yellow]ℹ️  Continuando sem diarização...[/yellow]")
                args.diarize = False

    # Transcrever
    start_time = time.time()

    if TRANSCRIBER == "whisperx":
        data = transcribe_with_whisperx(
            args.audio_file, model=args.model,
            language=args.language, diarize=args.diarize,
            hf_token=hf_token
        )
    elif TRANSCRIBER == "faster-whisper":
        if args.diarize:
            console.print("[yellow]⚠️  Diarização requer WhisperX. Instale: pip install whisperx[/yellow]")
            console.print("[yellow]   Transcrevendo sem diarização...[/yellow]")
            args.diarize = False
        data = transcribe_with_faster_whisper(args.audio_file, model=args.model, language=args.language)
    else:
        if args.diarize:
            console.print("[yellow]⚠️  Diarização requer WhisperX. Instale: pip install whisperx[/yellow]")
            args.diarize = False
        data = transcribe_with_whisper(args.audio_file, model=args.model, language=args.language)

    elapsed = time.time() - start_time

    # Gerar Markdown
    transcript_text, word_count = generate_markdown(
        data, args.audio_file, TRANSCRIBER, args.model, elapsed, args.diarize
    )

    # Salvar transcript
    basename = Path(args.audio_file).stem
    output_file = os.path.join(output_dir, f"{basename}.md")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(transcript_text)

    console.print(f"\n[green]📝 Transcript salvo: {output_file}[/green]")

    # Gerar SRT se solicitado
    if args.srt:
        srt_file = os.path.join(output_dir, f"{basename}.srt")
        with open(srt_file, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(data["segments"], 1):
                start_ts = format_timestamp(seg["start"]).replace(":", ",") + ",000"
                # Ajustar formato SRT: HH:MM:SS,mmm
                start_parts = format_timestamp(seg["start"])
                end_parts = format_timestamp(seg["end"])
                f.write(f"{i}\n")
                f.write(f"{start_parts},000 --> {end_parts},000\n")
                speaker_prefix = ""
                if "speaker" in seg:
                    speaker_prefix = f"[{seg['speaker']}] "
                f.write(f"{speaker_prefix}{seg['text']}\n\n")
        console.print(f"[green]📝 Legendas SRT salvas: {srt_file}[/green]")

    # Resumo
    console.print(f"\n[bold green]✅ Transcrição concluída![/bold green]")
    console.print(f"   Palavras: {word_count:,}")
    console.print(f"   Segmentos: {len(data['segments'])}")
    if data["num_speakers"] > 0:
        console.print(f"   Locutores: {data['num_speakers']}")
    console.print(f"   Tempo: {elapsed:.0f}s")

    # Processar com LLM (se não desativado)
    if not args.no_llm:
        cli_tool = detect_cli_tool()
        if cli_tool:
            console.print(f"\n[green]✅ CLI detectada: {cli_tool}[/green]")
            final_prompt = handle_prompt_workflow(args.prompt, transcript_text)
            if final_prompt:
                ata_text = process_with_llm(transcript_text, final_prompt, cli_tool)
                if ata_text:
                    ata_file = os.path.join(output_dir, f"{basename}-ata.md")
                    with open(ata_file, 'w', encoding='utf-8') as f:
                        f.write(ata_text)
                    console.print(f"[green]📝 Ata salva: {ata_file}[/green]")


if __name__ == "__main__":
    main()
