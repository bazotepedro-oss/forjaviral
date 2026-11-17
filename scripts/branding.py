"""Marca d'água e encerramento promocional para os vídeos da Fábrica dos Cortes.

Tudo é local: o PNG da marca e o vídeo de divulgação ficam em webui/assets.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
ASSETS = APP_ROOT / "webui" / "assets"
WATERMARK_PATH = ASSETS / "watermark.png"
PROMO_PATH = ASSETS / "promo" / "ferramenta.mp4"

_CACHED_ENCODER: tuple[str, str] | None = None


def watermark_available() -> bool:
    return WATERMARK_PATH.is_file() and WATERMARK_PATH.stat().st_size > 1024


def promo_available() -> bool:
    return PROMO_PATH.is_file() and PROMO_PATH.stat().st_size > 100_000


def _duration(path: str | Path) -> float:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return max(0.0, float(result.stdout.strip() or 0))
    except Exception:
        return 0.0


def promo_duration() -> float:
    if not promo_available():
        return 0.0
    return _duration(PROMO_PATH)


def _encoder_works(name: str) -> bool:
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "color=black:s=256x256:d=0.04",
                "-c:v",
                name,
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            timeout=30,
        )
        return result.returncode == 0
    except Exception:
        return False


def _best_encoder() -> tuple[str, str]:
    global _CACHED_ENCODER
    if _CACHED_ENCODER is not None:
        return _CACHED_ENCODER
    if _encoder_works("h264_nvenc"):
        _CACHED_ENCODER = ("h264_nvenc", "fast")
    else:
        _CACHED_ENCODER = ("libx264", "veryfast")
    return _CACHED_ENCODER


def _encoder_args(encoder: str, preset: str) -> list[str]:
    if encoder == "h264_nvenc":
        return ["-c:v", "h264_nvenc", "-preset", preset, "-b:v", "5M"]
    return ["-c:v", "libx264", "-preset", preset, "-crf", "22"]


def _run(command: list[str], timeout: int = 1800) -> tuple[int, str]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        return result.returncode, (result.stdout or "") + (result.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "FFmpeg excedeu o tempo limite."
    except OSError as exc:
        return 1, str(exc)


def brand_video(
    input_video: str | Path,
    output_video: str | Path,
    width: int = 1080,
    height: int = 1920,
    *,
    watermark: bool = True,
    promo: bool = True,
    fps: int = 30,
) -> tuple[bool, str]:
    """Aplica marca d'água e/ou acrescenta o vídeo da ferramenta no final.

    Retorna (ok, mensagem). Se nada foi pedido ou os assets não existem,
    copia o vídeo original para o destino.
    """
    source = Path(input_video)
    target = Path(output_video)
    if not source.is_file():
        return False, f"Vídeo não encontrado: {source}"

    use_watermark = bool(watermark and watermark_available())
    use_promo = bool(promo and promo_available())
    if not use_watermark and not use_promo:
        shutil.copy2(source, target)
        return True, "Sem marca d'água ou encerramento."

    source_seconds = _duration(source)
    promo_seconds = promo_duration() if use_promo else 0.0

    width = max(2, int(width))
    height = max(2, int(height))
    width -= width % 2
    height -= height % 2
    vertical = height >= width

    inputs: list[str] = ["-i", str(source)]
    filters: list[str] = []

    if use_promo:
        inputs += ["-i", str(PROMO_PATH)]
        # O corte é preservado integralmente. O encerramento já começa com um
        # fade-in próprio, o que cria a transição sem encurtar o conteúdo.
        filters.append(
            f"[0:v]setpts=PTS-STARTPTS,scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps={fps},"
            "format=yuv420p[vmain]"
        )
        filters.append(
            "[0:a]asetpts=PTS-STARTPTS,aresample=48000,"
            "aformat=sample_fmts=fltp:channel_layouts=stereo[amain]"
        )
        if vertical:
            filters.append(
                f"[1:v]setpts=PTS-STARTPTS,scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,fps={fps},"
                "format=yuv420p,setsar=1,fade=t=in:st=0:d=0.30[vpromo]"
            )
        else:
            filters.append(
                f"[1:v]setpts=PTS-STARTPTS,scale=-2:{height}:flags=lanczos,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=#080605,fps={fps},"
                "format=yuv420p,setsar=1,fade=t=in:st=0:d=0.30[vpromo]"
            )
        filters.append(
            "[1:a]asetpts=PTS-STARTPTS,aresample=48000,"
            "aformat=sample_fmts=fltp:channel_layouts=stereo,"
            "afade=t=in:st=0:d=0.30[apromo]"
        )
        filters.append("[vmain][amain][vpromo][apromo]concat=n=2:v=1:a=1[vcat][acat]")
        vcat, acat = "vcat", "acat"
    else:
        filters.append(
            f"[0:v]setpts=PTS-STARTPTS,scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps={fps},"
            "format=yuv420p[vcat]"
        )
        filters.append(
            "[0:a]asetpts=PTS-STARTPTS,aresample=48000,"
            "aformat=sample_fmts=fltp:channel_layouts=stereo[acat]"
        )
        vcat, acat = "vcat", "acat"

    if use_watermark:
        wm_index = 2 if use_promo else 1
        inputs += ["-i", str(WATERMARK_PATH)]
        wm_width = 300 if vertical else 380
        margin = 32 if vertical else 48
        filters.append(f"[{wm_index}:v]scale={wm_width}:-1[wm]")
        filters.append(f"[{vcat}][wm]overlay=W-w-{margin}:{margin}:format=auto[vout]")
    else:
        filters.append(f"[{vcat}]null[vout]")
    filters.append(f"[{acat}]anull[aout]")

    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.stem + ".part.mp4")
    base = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        *inputs,
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[vout]",
        "-map",
        "[aout]",
    ]
    tail = ["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(temp)]

    encoder, preset = _best_encoder()
    code, log = _run([*base, *_encoder_args(encoder, preset), *tail])
    if code != 0 and encoder == "h264_nvenc":
        code, log = _run([*base, *_encoder_args("libx264", "veryfast"), *tail])
    if code != 0 or not temp.is_file() or temp.stat().st_size < 1024:
        try:
            temp.unlink()
        except OSError:
            pass
        return False, (log or "FFmpeg falhou ao aplicar a marca d'água/encerramento.")[-1600:]

    if use_promo and source_seconds > 0.5 and promo_seconds > 0.5:
        produced_seconds = _duration(temp)
        expected_seconds = source_seconds + promo_seconds
        # Garante que o encerramento foi acrescentado depois do corte, sem
        # substituir o final do conteúdo.
        if produced_seconds < expected_seconds - 0.75:
            try:
                temp.unlink()
            except OSError:
                pass
            return False, (
                "O encerramento não foi anexado corretamente: "
                f"corte de {source_seconds:.1f}s + encerramento de {promo_seconds:.1f}s, "
                f"mas o arquivo saiu com {produced_seconds:.1f}s."
            )

    os.replace(temp, target)
    extras = []
    if use_watermark:
        extras.append("marca d'água")
    if use_promo:
        extras.append(
            f"encerramento ({source_seconds:.1f}s de corte + {promo_seconds:.1f}s de vídeo = "
            f"{source_seconds + promo_seconds:.1f}s)"
        )
    return True, "Aplicado: " + " + ".join(extras) + "."
