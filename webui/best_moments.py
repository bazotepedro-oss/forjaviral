"""Build a 5/10 minute 16:9 podcast highlight compilation from AI-selected clips."""

from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from pathlib import Path
from typing import Callable

APP_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = APP_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import create_viral_segments  # noqa: E402


def list_compilations(project_dir: str | Path) -> list[dict]:
    """Lista os compilados já renderizados, do mais recente para o mais antigo."""
    folder = Path(project_dir) / "best_moments"
    if not folder.is_dir():
        return []
    items: list[dict] = []
    for meta in folder.glob("melhores_momentos_*.json"):
        video = meta.with_suffix(".mp4")
        if not video.is_file() or video.stat().st_size < 100_000:
            continue
        try:
            data = json.loads(meta.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        srt = meta.with_suffix(".srt")
        items.append(
            {
                "json_path": str(meta),
                "video_path": str(video),
                "srt_path": str(srt) if srt.is_file() else "",
                "title": str(data.get("title") or "Melhores Momentos"),
                "description": str(data.get("description") or ""),
                "target_minutes": int(data.get("target_minutes") or 0),
                "duration_seconds": float(data.get("actual_duration_seconds") or 0),
                "chapters": data.get("chapters") or [],
                "created_at": meta.stat().st_mtime,
            }
        )
    items.sort(key=lambda item: item["created_at"], reverse=True)
    return items


def _safe_segment(seg: dict, video_duration: float) -> dict | None:
    try:
        start = float(seg.get("start_time", 0))
        end = float(seg.get("end_time", 0))
        duration = end - start
        if not all(math.isfinite(v) for v in (start, end, duration)):
            return None
        if start < 0 or end > video_duration + 1 or duration < 15 or duration > 91:
            return None
        if start >= video_duration or end <= start:
            return None
        item = dict(seg)
        item["start_time"] = max(0.0, start)
        item["end_time"] = min(video_duration, end)
        item["duration"] = item["end_time"] - item["start_time"]
        try:
            item["score"] = max(0, min(100, int(float(item.get("score", 0)))))
        except (TypeError, ValueError):
            item["score"] = 0
        return item
    except (TypeError, ValueError):
        return None


_TOPIC_STOPWORDS = {
    "a", "o", "as", "os", "de", "da", "do", "das", "dos", "e", "é", "em", "no",
    "na", "nos", "nas", "um", "uma", "uns", "umas", "que", "para", "pra", "com",
    "por", "mas", "se", "ao", "aos", "à", "às", "seu", "sua", "seus", "suas",
    "ele", "ela", "eles", "elas", "isso", "isto", "aquilo", "esse", "essa",
    "este", "esta", "aquele", "aquela", "como", "mais", "menos", "muito",
    "muita", "muitos", "muitas", "já", "não", "sim", "vai", "vou", "tem",
    "ter", "foi", "ser", "são", "é", "aqui", "ali", "então", "porque",
    "sobre", "quando", "onde", "quem", "qual", "você", "voce", "eu", "nós",
    "nos", "eles", "delas", "deles", "the", "and", "for", "with", "that",
    "this", "you", "from", "his", "her", "are", "was", "were", "have", "has",
}


def _topic_tokens(value: str) -> set[str]:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return {token for token in text.split() if len(token) > 2 and token not in _TOPIC_STOPWORDS}


def _same_topic(left: dict, right: dict) -> bool:
    """Evita repetir o mesmo assunto com títulos diferentes no compilado."""
    a = _topic_tokens(left.get("title") or "")
    b = _topic_tokens(right.get("title") or "")
    if not a or not b:
        return False
    return len(a & b) / max(1, len(a | b)) >= 0.55


def select_compilation_segments(
    candidates: list[dict], target_seconds: int, video_duration: float, cold_open: bool = True
) -> list[dict]:
    """Select high-scoring, non-overlapping and topic-diverse clips near the target runtime."""
    valid = [item for raw in candidates if (item := _safe_segment(raw, video_duration))]
    valid.sort(key=lambda x: int(x.get("score", 0)), reverse=True)

    # A compilação não pode repetir o mesmo assunto só porque o modelo devolveu
    # dois títulos parecidos. Se a filtragem for agressiva demais, voltamos à
    # lista completa para não faltar material.
    unique: list[dict] = []
    for candidate in valid:
        if not any(_same_topic(candidate, kept) for kept in unique):
            unique.append(candidate)
    pool = unique if len(unique) >= 2 else valid

    selected: list[dict] = []
    total = 0.0

    def overlaps(candidate: dict) -> bool:
        start = float(candidate["start_time"])
        end = float(candidate["end_time"])
        return any(
            min(end, float(existing["end_time"])) - max(start, float(existing["start_time"])) > 3
            for existing in selected
        )

    def fill(limit: float) -> None:
        nonlocal total
        for candidate in pool:
            if len(selected) >= len(pool):
                break
            if candidate in selected:
                continue
            duration = float(candidate["duration"])
            if total + duration > limit + 0.001:
                continue
            if overlaps(candidate):
                continue
            selected.append(candidate)
            total += duration

    # O melhor momento abre o vídeo, mesmo que seja de uma parte mais adiantada
    # do podcast. O restante é escolhido por nota e depois ordenado no tempo.
    lead = None
    if cold_open and pool:
        lead = pool[0]
        selected.append(lead)
        total = float(lead["duration"])

    fill(target_seconds)
    if total < target_seconds * 0.95:
        fill(target_seconds + 30)
    if total < target_seconds * 0.92:
        fill(target_seconds + 60)
    if total < target_seconds * 0.85:
        fill(target_seconds + 90)

    # Se a seleção passou muito do alvo, remove os menores/mais fracos sem
    # mexer no cold open até caber numa margem de 12%.
    while total > target_seconds * 1.12 and len(selected) > 1:
        removable = [item for item in selected if item is not lead]
        drop = min(removable, key=lambda item: int(item.get("score", 0))) if removable else selected[-1]
        selected.remove(drop)
        total -= float(drop["duration"])

    if cold_open and lead in selected:
        selected = [lead, *sorted((item for item in selected if item is not lead), key=lambda x: float(x["start_time"]))]
    else:
        selected.sort(key=lambda x: float(x["start_time"]))
    return selected


def _srt_timestamp(seconds: float) -> str:
    ms = max(0, int(round(seconds * 1000)))
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def _write_compilation_srt(transcript: list[dict], clips: list[dict], path: Path) -> list[dict]:
    lines: list[str] = []
    chapters: list[dict] = []
    output_cursor = 0.0
    subtitle_index = 1

    for clip in clips:
        clip_start = float(clip["start_time"])
        clip_end = float(clip["end_time"])
        clip_duration = clip_end - clip_start
        chapters.append({
            "start_seconds": round(output_cursor, 3),
            "title": str(clip.get("title") or "Melhor momento"),
            "source_start": round(clip_start, 3),
            "source_end": round(clip_end, 3),
            "score": clip.get("score", 0),
        })

        for segment in transcript:
            seg_start = float(segment.get("start", 0) or 0)
            seg_end = float(segment.get("end", seg_start) or seg_start)
            start = max(clip_start, seg_start)
            end = min(clip_end, seg_end)
            text = re.sub(r"\s+", " ", str(segment.get("text") or "")).strip()
            if end <= start or not text:
                continue
            out_start = output_cursor + (start - clip_start)
            out_end = output_cursor + (end - clip_start)
            lines.extend([
                str(subtitle_index),
                f"{_srt_timestamp(out_start)} --> {_srt_timestamp(out_end)}",
                text,
                "",
            ])
            subtitle_index += 1

        output_cursor += clip_duration

    path.write_text("\n".join(lines), encoding="utf-8-sig")
    return chapters


def _concat_command(video: Path, clips: list[dict], output: Path, encoder: str) -> list[str]:
    command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for clip in clips:
        start = float(clip["start_time"])
        duration = float(clip["duration"])
        command.extend(["-ss", f"{start:.3f}", "-t", f"{duration:.3f}", "-i", str(video)])

    filters: list[str] = []
    concat_inputs = []
    for index, clip in enumerate(clips):
        duration = float(clip["duration"])
        fade_out = max(0.0, duration - 0.08)
        filters.append(
            f"[{index}:v]setpts=PTS-STARTPTS,scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=30,format=yuv420p[v{index}]"
        )
        filters.append(
            f"[{index}:a]asetpts=PTS-STARTPTS,aresample=48000,"
            f"afade=t=in:st=0:d=0.04,afade=t=out:st={fade_out:.3f}:d=0.08[a{index}]"
        )
        concat_inputs.extend([f"[v{index}]", f"[a{index}]"])
    filters.append(f"{''.join(concat_inputs)}concat=n={len(clips)}:v=1:a=1[vout][aout]")
    command.extend(["-filter_complex", ";".join(filters), "-map", "[vout]", "-map", "[aout]"])
    if encoder == "h264_nvenc":
        command.extend(["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "23", "-b:v", "0"])
    else:
        command.extend(["-c:v", "libx264", "-preset", "veryfast", "-crf", "22"])
    command.extend(["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output)])
    return command


def create_compilation(
    project_dir: str | Path,
    target_minutes: int,
    api_key: str,
    cold_open: bool = True,
    progress: Callable[[float, str], None] | None = None,
) -> dict:
    project_dir = Path(project_dir).resolve()
    target_minutes = 10 if int(target_minutes) >= 10 else 5
    target_seconds = target_minutes * 60
    video = project_dir / "input.mp4"
    if not video.is_file():
        raise FileNotFoundError("O projeto não tem input.mp4. Baixe/transcreva o podcast antes.")
    if not str(api_key or "").strip():
        raise ValueError("Informe a chave da API Gemini na aba Criar Cortes antes de gerar o compilado.")

    transcript = create_viral_segments.load_transcript(str(project_dir))
    video_duration = _probe_duration(video) or max(float(segment.get("end", 0) or 0) for segment in transcript)
    candidate_count = 24 if target_minutes == 5 else 32
    min_clip_seconds = 25

    output_dir = project_dir / "best_moments"
    analysis_dir = output_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    # create_viral_segments stores prompts/responses in project_folder; isolate
    # those analysis artifacts from the regular clip project's files.
    copied_transcript = False
    for name in ("input.tsv", "input.srt"):
        src = project_dir / name
        dst = analysis_dir / name
        if src.is_file():
            shutil.copy2(src, dst)
            copied_transcript = True
    if not copied_transcript:
        raise FileNotFoundError("Transcrição do projeto não encontrada (input.tsv/input.srt).")

    if progress:
        progress(0.08, "Analisando o podcast inteiro e procurando os melhores momentos...")

    result = create_viral_segments.create(
        candidate_count,
        True,
        None,
        min_clip_seconds,
        90,
        ai_mode="gemini",
        api_key=str(api_key).strip(),
        project_folder=str(analysis_dir),
        # Blocos menores são mais confiáveis em chaves gratuitas (limite de
        # tokens por minuto) e evitam uma única chamada de ~275 mil caracteres.
        chunk_size_arg=120000,
        model_name_arg="gemini-2.5-flash",
        extra_instruction=(
            "This transcript will become a long horizontal YouTube compilation, "
            "not a set of individual Shorts. Choose complete stories of 30 to 90 seconds "
            "that still work when watched back-to-back. Vary the subjects, guests and "
            "emotional tones: never choose two moments about the same story, argument or "
            "anecdote. The first selected moment will open the compilation, so the "
            "strongest hook and reaction peak must be among the candidates. Prefer moments "
            "with laughter, shock, disagreement, confession or a surprising reveal."
        ),
        progress_callback=(
            (lambda amount, text: progress(0.08 + float(amount) * 0.8, text))
            if progress else None
        ),
    )
    candidates = result.get("segments") or []
    if not candidates:
        error = str(getattr(create_viral_segments, "LAST_AI_ERROR", "") or "")
        lowered = error.lower()
        if "429" in error or "quota" in lowered or "limite" in lowered or "tempo limite" in lowered:
            raise RuntimeError(
                "A IA atingiu o limite de uso agora. Aguarde alguns minutos ou use outra chave Gemini. "
                "Nenhum crédito foi cobrado."
            )
        raise RuntimeError(error or "A IA não encontrou candidatos válidos.")

    clips = select_compilation_segments(candidates, target_seconds, video_duration, cold_open)
    if not clips:
        raise RuntimeError("A IA não encontrou momentos com duração e timestamps válidos.")
    total_seconds = sum(float(item["duration"]) for item in clips)
    if total_seconds < target_seconds * 0.85:
        raise RuntimeError(
            f"Só encontrei {len(clips)} momentos válidos ({total_seconds/60:.1f} min). "
            "Não gerei um compilado curto como se tivesse a duração pedida; os 10 créditos serão devolvidos. Tente outro episódio ou rode novamente."
        )
    if total_seconds > target_seconds * 1.12:
        raise RuntimeError(
            f"A seleção ficou com {total_seconds/60:.1f} min, acima do limite seguro para {target_minutes} min. "
            "Nada foi cobrado; tente novamente para a IA refazer a seleção."
        )

    if progress:
        progress(0.25, f"Selecionados {len(clips)} momentos ({total_seconds/60:.1f} min). Montando o vídeo 16:9...")

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    out_video = output_dir / f"melhores_momentos_{target_minutes}min_{timestamp}.mp4"
    out_srt = out_video.with_suffix(".srt")
    chapters = _write_compilation_srt(transcript, clips, out_srt)

    encoder_list = subprocess.run(
        ["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True, timeout=20
    ).stdout
    encoder = "h264_nvenc" if "h264_nvenc" in encoder_list else "libx264"
    command = _concat_command(video, clips, out_video, encoder)
    try:
        rendered = subprocess.run(command, capture_output=True, text=True, timeout=1800)
    except subprocess.TimeoutExpired:
        raise RuntimeError("A renderização passou de 30 minutos e foi interrompida; os créditos serão devolvidos.")
    if rendered.returncode != 0 and encoder == "h264_nvenc":
        if progress:
            progress(0.35, "GPU indisponível para o encoder. Continuando pela CPU...")
        command = _concat_command(video, clips, out_video, "libx264")
        try:
            rendered = subprocess.run(command, capture_output=True, text=True, timeout=1800)
        except subprocess.TimeoutExpired:
            raise RuntimeError("A renderização passou de 30 minutos e foi interrompida; os créditos serão devolvidos.")
    if rendered.returncode != 0 or not out_video.exists() or out_video.stat().st_size < 100_000:
        raise RuntimeError(f"Falha ao renderizar o compilado: {rendered.stderr[-1200:]}")

    media = _probe_media(out_video)
    if media["width"] != 1920 or media["height"] != 1080:
        raise RuntimeError(
            f"O compilado saiu em {media['width']}x{media['height']} em vez de 1920x1080. "
            "O arquivo não foi entregue; os créditos serão devolvidos."
        )
    if abs(media["fps"] - 30.0) > 0.6:
        raise RuntimeError(
            f"O compilado saiu em {media['fps']:.2f} FPS em vez de 30 FPS. "
            "O arquivo não foi entregue; os créditos serão devolvidos."
        )
    if media["duration"] < target_seconds * 0.85:
        raise RuntimeError(
            f"O vídeo final ficou com {media['duration']/60:.1f} min, abaixo do mínimo seguro para {target_minutes} min. "
            "Os créditos serão devolvidos."
        )
    if media["duration"] > target_seconds * 1.15:
        raise RuntimeError(
            f"O vídeo final ficou com {media['duration']/60:.1f} min, acima do limite para {target_minutes} min. "
            "Os créditos serão devolvidos."
        )

    chapter_lines = [
        f"{int(c['start_seconds']//60):02}:{int(c['start_seconds']%60):02} {c['title']}"
        for c in chapters
    ]
    description = "Melhores momentos do podcast.\n\nCapítulos:\n" + "\n".join(chapter_lines)
    title = f"Melhores Momentos — {project_dir.name}"
    (output_dir / f"melhores_momentos_{target_minutes}min_{timestamp}.json").write_text(
        json.dumps(
            {
                "title": title,
                "description": description,
                "target_minutes": target_minutes,
                "actual_duration_seconds": round(media["duration"], 3),
                "media": media,
                "clips": clips,
                "chapters": chapters,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    if progress:
        progress(1.0, "Compilado pronto. Legendas SRT e capítulos também foram salvos.")
    return {
        "video_path": str(out_video),
        "srt_path": str(out_srt),
        "title": title,
        "description": description,
        "clips": clips,
        "chapters": chapters,
        "duration_seconds": media["duration"],
        "media": media,
    }


def _probe_duration(path: Path) -> float:
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        )
        return float(json.loads(proc.stdout)["format"]["duration"])
    except Exception:
        return 0.0


def _probe_media(path: Path) -> dict:
    """Lê resolução, FPS, codecs e duração para validar a entrega antes de cobrar."""
    try:
        proc = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate,bit_rate",
                "-show_entries", "format=duration",
                "-of", "json", str(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        data = json.loads(proc.stdout)
    except Exception:
        return {"width": 0, "height": 0, "fps": 0.0, "duration": 0.0, "video_codec": "", "audio_codec": ""}

    video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})
    rate = str(video_stream.get("r_frame_rate") or "0/1")
    try:
        numerator, denominator = (int(part) for part in rate.split("/", 1))
        fps = numerator / denominator if denominator else 0.0
    except (TypeError, ValueError, ZeroDivisionError):
        fps = 0.0
    try:
        duration = float(data.get("format", {}).get("duration") or 0)
    except (TypeError, ValueError):
        duration = 0.0
    return {
        "width": int(video_stream.get("width") or 0),
        "height": int(video_stream.get("height") or 0),
        "fps": round(fps, 3),
        "duration": duration,
        "video_codec": str(video_stream.get("codec_name") or ""),
        "audio_codec": str(audio_stream.get("codec_name") or ""),
        "audio_bitrate": int(audio_stream.get("bit_rate") or 0),
    }
