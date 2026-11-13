"""Biblioteca de cortes: galeria, thumbnails, edição de legenda, música e metadados.

Trabalha direto na pasta VIRALS do app, sem depender do Gradio.
"""

from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIRALS = ROOT / "VIRALS"
MUSIC = ROOT / "music"
THUMBS = VIRALS / ".thumbs"
PREVIEWS = VIRALS / ".previews"

sys.path.insert(0, str(ROOT / "scripts"))

try:
    import adjust_subtitles
    import burn_subtitles
except Exception as exc:  # pragma: no cover
    print(f"[studio] Falha ao importar scripts: {exc}")
    adjust_subtitles = None
    burn_subtitles = None


# ---------------------------------------------------------------- utilidades
def _safe_name(value: str) -> str:
    text = re.sub(r"[^\w\s.-]", "", str(value or "")).strip()
    return re.sub(r"\s+", "_", text)[:80] or "corte"


def _project_dir(project: str) -> Path:
    return VIRALS / str(project)


def _load_segments(project: str) -> list[dict]:
    path = _project_dir(project) / "viral_segments.txt"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return []
    return data.get("segments", []) or []


def _save_segments(project: str, segments: list[dict]) -> None:
    path = _project_dir(project) / "viral_segments.txt"
    path.write_text(json.dumps({"segments": segments}, ensure_ascii=False, indent=4), encoding="utf-8")


def _index_of(base: str) -> int | None:
    match = re.match(r"^(\d{3})", base)
    return int(match.group(1)) if match else None


def _segment_for(project: str, base: str) -> dict:
    idx = _index_of(base)
    segments = _load_segments(project)
    if idx is not None and 0 <= idx < len(segments):
        return segments[idx]
    return {}


def _ass_color(hex_color: str, alpha: str = "00") -> str:
    value = str(hex_color or "").strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6:
        value = "FFFFFF"
    r, g, b = value[0:2], value[2:4], value[4:6]
    return f"&H{alpha}{b}{g}{r}&".upper()


def _ffprobe_duration(path: Path) -> float:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return float(json.loads(out.stdout)["format"]["duration"])
    except Exception:
        return 0.0


def _cache_tag(path: Path) -> str:
    try:
        return str(int(path.stat().st_mtime))
    except OSError:
        return "0"


# ---------------------------------------------------------------- projetos
def list_projects() -> list[str]:
    if not VIRALS.exists():
        return []
    projects = []
    for item in VIRALS.iterdir():
        if item.is_dir() and not item.name.startswith(".") and item.name not in {"models", "logs"}:
            projects.append(item)
    projects.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [p.name for p in projects]


def cuts(project: str) -> list[dict]:
    """Lista os cortes prontos do projeto (vídeo com legenda queimada ou final)."""
    if not project:
        return []
    folder = _project_dir(project)
    burned = folder / "burned_sub"
    final = folder / "final"
    found: dict[str, dict] = {}

    for folder_path in (burned, final):
        if not folder_path.exists():
            continue
        for video in folder_path.glob("*.mp4"):
            stem = video.stem
            if stem.startswith("temp_video_no_audio"):
                continue
            base = stem[:-len("_subtitled")] if stem.endswith("_subtitled") else stem
            if base.endswith("_processed"):
                base = base[:-len("_processed")]
            entry = found.setdefault(base, {"base": base, "video": None, "burned": None, "final": None})
            if folder_path == burned:
                entry["burned"] = video
                entry["video"] = video
            else:
                entry["final"] = video
                entry.setdefault("video", video)

    result = []
    for base, entry in found.items():
        video = entry.get("video")
        if not video or not video.exists() or video.stat().st_size < 1024:
            continue
        idx = _index_of(base)
        segment = _segment_for(project, base)
        title = str(segment.get("title") or base[4:].replace("_", " ")).strip()
        score = segment.get("score")
        result.append(
            {
                "base": base,
                "index": idx if idx is not None else 9999,
                "title": title,
                "score": score,
                "video": str(video),
                "burned": str(entry["burned"]) if entry.get("burned") else "",
                "final": str(entry["final"]) if entry.get("final") else "",
                "has_burned": bool(entry.get("burned")),
                "label": f"{idx:03d} • {title[:48]}" + (f" • nota {score}" if score is not None else ""),
            }
        )

    result.sort(key=lambda item: item["index"])
    return result


def _cut_by_base(project: str, base: str) -> dict | None:
    for item in cuts(project):
        if item["base"] == base:
            return item
    return None


# ---------------------------------------------------------------- thumbnails
def thumbnail(project: str, base: str) -> Path | None:
    entry = _cut_by_base(project, base)
    if not entry:
        return None
    THUMBS.mkdir(parents=True, exist_ok=True)
    target = THUMBS / f"{_safe_name(project)}__{_safe_name(base)}.jpg"
    video = Path(entry["video"])
    try:
        if target.exists() and target.stat().st_mtime >= video.stat().st_mtime:
            return target
        duration = _ffprobe_duration(video)
        stamp = max(0.4, min(3.0, duration * 0.15)) if duration else 1.0
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-ss", f"{stamp:.2f}", "-i", str(video),
                "-frames:v", "1", "-vf", "scale=480:-2", "-q:v", "3", str(target),
            ],
            capture_output=True,
            timeout=60,
        )
        return target if target.exists() else None
    except Exception as exc:
        print(f"[studio] thumbnail falhou: {exc}")
        return None


def make_thumbnails(project: str) -> int:
    count = 0
    for item in cuts(project):
        if thumbnail(project, item["base"]):
            count += 1
    return count


# ---------------------------------------------------------------- galeria
def _media_url(path: Path) -> str:
    """URL do arquivo pelo mount /virals (StaticFiles montado no app)."""
    try:
        relative = Path(path).resolve().relative_to(VIRALS.resolve())
        return "/virals/" + urllib.parse.quote(relative.as_posix(), safe="/")
    except Exception:
        value = str(path).replace("\\", "/")
        return "/gradio_api/file=" + urllib.parse.quote(value, safe="/:")


def video_html(path, tag: str = "") -> str:
    """Player HTML5 próprio, usando o mesmo mount /virals da galeria."""
    if not path:
        return ""
    video = Path(str(path))
    if not video.exists():
        return ""
    url = _media_url(video)
    return (
        '<div class="lib-player-wrap">'
        f'<video class="lib-player" controls preload="metadata" playsinline>'
        f'<source src="{url}?v={_cache_tag(video)}-{tag}" type="video/mp4">'
        "</video></div>"
    )


def gallery_html(project: str, bump: int = 0) -> str:
    items = cuts(project)
    if not items:
        return (
            '<div style="padding:28px;text-align:center;color:#a99a8d;font-size:14px;">'
            "Nenhum corte pronto neste projeto ainda. Gere cortes na aba Criar Cortes."
            "</div>"
        )

    cards = []
    for item in items:
        video = Path(item["video"])
        poster = thumbnail(project, item["base"])
        poster_attr = f' poster="{_media_url(poster)}"' if poster else ""
        title = html.escape(item["title"])
        score = item["score"]
        score_html = (
            f'<span class="fdc-lib-score">{html.escape(str(score))}</span>' if score is not None else ""
        )
        tags = html.escape(" ".join(_segment_for(project, item["base"]).get("hashtags") or []))
        cards.append(
            f"""
            <div class="fdc-lib-card" data-base="{html.escape(str(item['base']), quote=True)}">
              <div class="fdc-lib-video">
                <video controls preload="metadata" playsinline{poster_attr}>
                  <source src="{_media_url(video)}?v={_cache_tag(video)}-{bump}" type="video/mp4">
                </video>
              </div>
              <div class="fdc-lib-body">
                <div class="fdc-lib-title">{title}</div>
                <div class="fdc-lib-tags">{tags}</div>
              </div>
              {score_html}
            </div>
            """
        )

    return (
        f'<div class="fdc-lib-head"><span>{len(items)} corte(s)</span>'
        f'<span class="fdc-lib-project">{html.escape(project)}</span></div>'
        '<div class="fdc-lib-grid">' + "".join(cards) + "</div>"
    )


# ---------------------------------------------------------------- metadados
def metadata(project: str, base: str) -> dict:
    segment = _segment_for(project, base)
    title = str(segment.get("title") or base[4:].replace("_", " ")).strip()
    hashtags = " ".join(segment.get("hashtags") or [])
    reasoning = str(segment.get("reasoning") or segment.get("description") or "").strip()
    hook = str(segment.get("hook") or "").strip()
    emotion = str(segment.get("emotion") or "").strip()
    parts = []
    if hook:
        parts.append(f'"{hook}"')
    if reasoning:
        parts.append(reasoning)
    if emotion:
        parts.append(f"Tom do corte: {emotion}")
    if hashtags:
        parts.append(hashtags)
    parts.append(f"Corte do podcast {project}.")
    return {"title": title, "description": "\n\n".join(parts), "hashtags": hashtags}


def rename_cut(project: str, base: str, new_title: str) -> str:
    new_title = str(new_title or "").strip()
    if not new_title:
        return "Digite o novo título."
    segments = _load_segments(project)
    idx = _index_of(base)
    if idx is None or idx >= len(segments):
        return "Corte não encontrado no viral_segments.txt."
    segments[idx]["title"] = new_title
    _save_segments(project, segments)
    return "Título atualizado."


def set_feedback(project: str, base: str, verdict: str) -> str:
    path = _project_dir(project) / "feedback.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception:
        data = {}
    segment = _segment_for(project, base)
    data[base] = {
        "verdict": verdict,
        "title": segment.get("title") or base,
        "score": segment.get("score"),
        "at": int(time.time()),
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return "Corte aprovado." if verdict == "approve" else "Corte reprovado (feedback salvo)."


# ---------------------------------------------------------------- apagar
def delete_cut(project: str, base: str) -> str:
    folder = _project_dir(project)
    targets = []
    for name in (f"{base}_subtitled.mp4", f"{base}_processed_subtitled.mp4", f"{base}.mp4"):
        targets.append(folder / "burned_sub" / name)
    for name in (f"{base}_processed.mp4", f"{base}.mp4"):
        targets.append(folder / "final" / name)
    targets.append(folder / "cuts" / f"{base}_original_scale.mp4")
    targets.append(folder / "cuts" / f"{base}.mp4")
    for name in (f"{base}_processed.json", f"{base}.json"):
        targets.append(folder / "subs" / name)
    for name in (f"{base}_processed.ass", f"{base}.ass"):
        targets.append(folder / "subs_ass" / name)
    removed = 0
    for path in targets:
        if path.exists():
            try:
                path.unlink()
                removed += 1
            except OSError:
                pass
    thumb = THUMBS / f"{_safe_name(project)}__{_safe_name(base)}.jpg"
    if thumb.exists():
        try:
            thumb.unlink()
        except OSError:
            pass
    return f"Corte apagado ({removed} arquivo(s))." if removed else "Nenhum arquivo encontrado."


def delete_project(project: str, confirm: bool) -> str:
    if not confirm:
        return "Marque a confirmação para apagar o projeto."
    folder = _project_dir(project)
    if not folder.exists():
        return "Projeto não encontrado."
    shutil.rmtree(folder, ignore_errors=True)
    return "Projeto apagado."


# ---------------------------------------------------------------- ZIP
def export_zip(project: str) -> str:
    folder = _project_dir(project)
    if not folder.exists():
        return ""
    out = folder / f"FabricaDosCortes_{_safe_name(project)}_{time.strftime('%Y%m%d_%H%M')}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for sub in ("burned_sub", "subs_ass", "subs"):
            current = folder / sub
            if current.exists():
                for file in current.glob("*"):
                    if file.is_file() and (sub != "burned_sub" or file.suffix.lower() == ".mp4"):
                        zf.write(file, arcname=f"{sub}/{file.name}")
        for item in cuts(project):
            thumb = THUMBS / f"{_safe_name(project)}__{_safe_name(item['base'])}.jpg"
            if thumb.exists():
                zf.write(thumb, arcname=f"thumbnails/{thumb.name}")
        zf.writestr(
            "metadados.json",
            json.dumps(
                [metadata(project, item["base"]) for item in cuts(project)],
                ensure_ascii=False,
                indent=2,
            ),
        )
    return str(out)


# ---------------------------------------------------------------- legenda
def style_from_preset(name: str) -> dict:
    try:
        import subtitle_handler as subs

        preset = subs.SUBTITLE_PRESETS.get(name) or {}
    except Exception:
        preset = {}
    default = {
        "font_name": "Montserrat-ExtraBold",
        "font_size": 30,
        "highlight_size": 35,
        "base_color": "#FFFFFF",
        "highlight_color": "#00FF00",
        "outline_color": "#000000",
        "shadow_color": "#000000",
        "outline_thickness": 3,
        "shadow_size": 2,
        "bold": True,
        "italic": False,
        "uppercase": True,
        "words_per_block": 3,
        "gap_limit": 0.4,
        "mode": "highlight",
        "underline": False,
        "strikeout": False,
        "border_style": 1,
        "vertical_position": 200,
        "alignment": 2,
        "remove_punctuation": True,
    }
    default.update(preset or {})
    return default


def apply_style(project: str, base: str, style: dict) -> str:
    if adjust_subtitles is None or burn_subtitles is None:
        return "Módulos de legenda indisponíveis."
    entry = _cut_by_base(project, base)
    if not entry:
        return "Corte não encontrado."
    folder = _project_dir(project)
    final = Path(entry["final"]) if entry.get("final") else None
    if not final or not final.exists():
        final = Path(entry["video"])

    subs_dir = folder / "subs"
    json_path = subs_dir / f"{base}_processed.json"
    if not json_path.exists():
        json_path = subs_dir / f"{base}.json"
    if not json_path.exists():
        return "JSON de legenda não encontrado para este corte."

    ass_dir = folder / "subs_ass"
    ass_dir.mkdir(exist_ok=True)
    ass_path = ass_dir / f"{json_path.stem}.ass"

    face_modes = {}
    modes_file = folder / "face_modes.json"
    if modes_file.exists():
        try:
            face_modes = json.loads(modes_file.read_text(encoding="utf-8"))
        except Exception:
            face_modes = {}

    adjust_subtitles.generate_ass_from_file(
        str(json_path),
        str(ass_path),
        str(folder),
        _ass_color(style.get("base_color", "#FFFFFF")),
        int(style.get("font_size", 30)),
        int(style.get("highlight_size", 35)),
        _ass_color(style.get("highlight_color", "#00FF00")),
        int(style.get("words_per_block", 3)),
        float(style.get("gap_limit", 0.4)),
        style.get("mode", "highlight"),
        int(style.get("vertical_position", 200)),
        int(style.get("alignment", 2)),
        style.get("font_name", "Montserrat-ExtraBold"),
        _ass_color(style.get("outline_color", "#000000")),
        _ass_color(style.get("shadow_color", "#000000")),
        1 if style.get("bold") else 0,
        1 if style.get("italic") else 0,
        1 if style.get("underline") else 0,
        1 if style.get("strikeout") else 0,
        int(style.get("border_style", 1)),
        float(style.get("outline_thickness", 3)),
        float(style.get("shadow_size", 2)),
        1 if style.get("uppercase") else 0,
        face_modes,
        bool(style.get("remove_punctuation", True)),
    )

    burned = folder / "burned_sub" / f"{base}_subtitled.mp4"
    burned.parent.mkdir(exist_ok=True)
    backup_dir = folder / "burned_sub" / "_backup"
    backup_dir.mkdir(exist_ok=True)
    if burned.exists():
        shutil.copy2(burned, backup_dir / f"{base}_{time.strftime('%Y%m%d_%H%M%S')}.mp4")

    temp_out = folder / "burned_sub" / f"{base}_restyle.mp4"
    ok, message = burn_subtitles.burn_video_file(str(final), str(ass_path), str(temp_out))
    if not ok:
        return f"Falha ao queimar a legenda: {message}"
    os.replace(temp_out, burned)
    return f"Legenda aplicada em {burned.name}."


# ---------------------------------------------------------------- música
def music_tracks() -> list[dict]:
    MUSIC.mkdir(parents=True, exist_ok=True)
    tracks = []
    for path in MUSIC.rglob("*"):
        if path.suffix.lower() in {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}:
            tracks.append({"name": path.stem, "path": str(path)})
    tracks.sort(key=lambda item: item["name"].lower())
    return tracks


def music_choices() -> list[tuple[str, str]]:
    return [(track["name"], track["path"]) for track in music_tracks()]


def save_music_upload(file_path: str) -> str:
    if not file_path or not os.path.exists(file_path):
        return ""
    MUSIC.mkdir(parents=True, exist_ok=True)
    source = Path(file_path)
    target = MUSIC / f"upload_{_safe_name(source.stem)}{source.suffix.lower()}"
    shutil.copy2(source, target)
    return str(target)


def _music_filter(gain: float, fade_start: float, duck: bool) -> str:
    if duck:
        return (
            "[0:a]volume=1.0[voice];"
            f"[1:a]volume={gain:.2f},afade=t=out:st={fade_start:.2f}:d=1.5[bg];"
            "[bg][voice]sidechaincompress=threshold=0.05:ratio=6:attack=15:release=350[ducked];"
            "[voice][ducked]amix=inputs=2:duration=first:dropout_transition=2[a]"
        )
    return (
        "[0:a]volume=1.0[voice];"
        f"[1:a]volume={gain:.2f},afade=t=out:st={fade_start:.2f}:d=1.5[bg];"
        "[voice][bg]amix=inputs=2:duration=first:dropout_transition=2[a]"
    )


def preview_music(project: str, base: str, track: str, volume: int = 18, duck: bool = True, seconds: int = 30) -> tuple[str, str]:
    """Gera uma prévia curta (padrão 30s) com a música, sem alterar o corte final."""
    entry = _cut_by_base(project, base)
    if not entry:
        return "Corte não encontrado.", ""
    if not track or not os.path.exists(track):
        return "Escolha ou envie uma música.", ""
    burned = Path(entry["burned"]) if entry.get("burned") else Path(entry["video"])
    gain = max(0.0, min(1.0, int(volume) / 100.0))
    clip = max(5, int(seconds))
    fade_start = max(0.0, clip - 1.5)
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    output = PREVIEWS / f"{base}_music_{int(time.time())}.mp4"
    command = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-t", str(clip), "-i", str(burned),
        "-t", str(clip), "-i", str(track),
        "-filter_complex", _music_filter(gain, fade_start, bool(duck)),
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(output),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0 or not output.exists():
        return f"Falha na prévia: {result.stderr[-240:]}", ""
    _cleanup_previews()
    return "Prévia de 30s pronta. Veja o player na seção Música.", str(output)


def preview_video(project: str, base: str, tag: str = "preview") -> str:
    """Copia o corte para uma URL nova, forçando o player a recarregar."""
    entry = _cut_by_base(project, base)
    if not entry:
        return ""
    source = Path(entry["video"])
    if not source.exists():
        return ""
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    target = PREVIEWS / f"{base}_{tag}_{int(time.time())}{source.suffix}"
    shutil.copy2(source, target)
    _cleanup_previews()
    return str(target)


def _cleanup_previews(keep: int = 12) -> None:
    try:
        files = sorted(PREVIEWS.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in files[keep:]:
            old.unlink(missing_ok=True)
    except OSError:
        pass


def apply_music(project: str, base: str, track: str, volume: int = 18, duck: bool = True) -> str:
    entry = _cut_by_base(project, base)
    if not entry:
        return "Corte não encontrado."
    if not track or not os.path.exists(track):
        return "Escolha ou envie uma música."
    video = Path(entry["video"])
    burned = Path(entry["burned"]) if entry.get("burned") else video
    backup_dir = burned.parent / "_backup"
    backup_dir.mkdir(exist_ok=True)
    shutil.copy2(burned, backup_dir / f"{burned.stem}_{time.strftime('%Y%m%d_%H%M%S')}.mp4")

    gain = max(0.0, min(1.0, int(volume) / 100.0))
    duration = _ffprobe_duration(burned)
    fade_start = max(0.0, duration - 1.5)
    output = burned.parent / f"{burned.stem}_music.mp4"

    command = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(burned),
        "-i", str(track),
        "-filter_complex", _music_filter(gain, fade_start, bool(duck)),
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(output),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        return f"Falha ao mixar: {result.stderr[-300:]}"
    os.replace(output, burned)
    return f"Música aplicada ({volume}%{', com ducking' if duck else ''})."
