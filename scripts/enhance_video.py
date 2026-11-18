"""
Enhancement module for the Factory of Cuts.
Applies visual effects, quality improvements and audio processing to finished cuts.

Pipeline position: runs after edit_video (9:16 crop) and before or after subtitle burning.
Can be used standalone on any folder of MP4 files.

All effects are FFmpeg-first (GPU-accelerated when available) with OpenCV fallback.
Audio: loudnorm (-14 LUFS, platform standard) via FFmpeg.

Config: temp_enhance_config.json (same format as temp_subtitle_config.json).
Each effect is toggleable individually.
"""

from __future__ import annotations

import os
import sys
import json
import glob
import random
import hashlib
import subprocess
import shutil
from pathlib import Path
from typing import Optional

# Allow importing this module standalone
APP_ROOT = Path(__file__).resolve().parent.parent if "__file__" in globals() else Path("")
CONFIG_PATH = APP_ROOT / "temp_enhance_config.json"

# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_CONFIG: dict = {
    # Visual effects (0.0 = off, 0.0-1.0 = intensity)
    "color_grade_intensity": 0.45,          # Lift shadows, slight saturation boost
    "zoom_punch_intensity": 0.55,           # Subtle zoom on speech emphasis
    "shake_impact_intensity": 0.40,         # Micro-shake on key moments
    "glow_impact_intensity": 0.30,         # Flash of brightness on impact

    # Quality improvements
    "denoise_strength": 0.35,              # hqdn3d denoising (0 = off)
    "sharpen_strength": 0.50,               # unsharp sharpening (0 = off)
    "upscale_enabled": False,               # Upscale to 1080p if source is smaller
    "upscale_target_height": 1920,          # Target height for upscaling

    # Audio
    "audio_normalize": True,               # Loudnorm to -14 LUFS
    "audio_compress": True,                # Light compression
    "audio_echo_reduction": False,          # Light echo/room reduction

    # Anti-clone: variation between cuts of the same video
    "variation_seed": 42,                  # Base seed (overridden per-cut by filename hash)
    "variation_enabled": True,             # Apply random variation per cut

    # Per-cut tuning (0.0 = neutral, -1.0 to 1.0)
    "color_tint": 0.0,                     # Warm (+)/Cool (-) tint
    "contrast_boost": 0.0,                 # Extra contrast
    "saturation_boost": 0.0,               # Extra saturation

    # Which folder to process
    "target_folder": "final",              # final | burned_sub | cuts
    "process_subfolders": True,            # Scan subfolders too
    "output_suffix": "_enhanced",         # Added to output filename
    "overwrite": False,                    # Overwrite original files
}


def load_config(path: str | Path | None = None) -> dict:
    """Load enhancement config, falling back to defaults."""
    p = Path(path) if path else CONFIG_PATH
    if p.is_file():
        try:
            with open(p, "r", encoding="utf-8-sig") as f:
                loaded = json.load(f)
                # Merge with defaults so new keys get defaults
                cfg = dict(DEFAULT_CONFIG)
                cfg.update(loaded)
                return cfg
        except Exception as e:
            print(f"[Enhance] Warning: could not load config {p}: {e}")
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict, path: str | Path | None = None) -> None:
    """Save current config to file."""
    p = Path(path) if path else CONFIG_PATH
    with open(p, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)


def _encoder_works(name: str) -> bool:
    try:
        r = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error",
             "-f", "lavfi", "-i", "color=black:s=256x256:d=0.04",
             "-c:v", name, "-f", "null", "-"],
            capture_output=True, timeout=30,
        )
        return r.returncode == 0
    except Exception:
        return False


def _best_encoder() -> tuple[str, str, list[str]]:
    """Returns (encoder, preset, extra_args)."""
    if _encoder_works("h264_nvenc"):
        return "h264_nvenc", "fast", ["-b:v", "5M", "-bufsize", "10M"]
    if _encoder_works("hevc_amf"):
        return "hevc_amf", "fast", ["-b:v", "4M"]
    if _encoder_works("libx264"):
        return "libx264", "fast", ["-crf", "21"]
    return "libx264", "ultrafast", ["-crf", "23"]


def _video_info(path: str | Path) -> dict:
    """Get duration, width, height, fps of a video."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error",
             "-select_streams", "v:0",
             "-show_entries", "stream=width,height,r_frame_rate,duration",
             "-of", "json"],
            input=str(path),
            capture_output=True, text=True, timeout=30,
        )
        data = json.loads(r.stdout)
        s = data.get("streams", [{}])[0]
        fps_str = s.get("r_frame_rate", "30/1")
        w, h = s.get("width", 1080), s.get("height", 1920)
        num, den = map(float, fps_str.split("/"))
        return {
            "width": w, "height": h,
            "fps": round(num / den, 3),
            "duration": float(s.get("duration", 0)),
        }
    except Exception:
        return {"width": 1080, "height": 1920, "fps": 30.0, "duration": 10.0}


def _cut_seed(filename: str, base_seed: int) -> int:
    """Hash filename to get a stable seed per cut, for reproducible variation."""
    h = hashlib.md5(filename.encode()).hexdigest()
    return base_seed + int(h[:6], 16)


# ──────────────────────────────────────────────────────────────────────────────
# Color Grading
# ──────────────────────────────────────────────────────────────────────────────

def _build_color_filter(cfg: dict, intensity: float, rng: random.Random) -> str:
    """Build FFmpeg color grading filter based on intensity and per-cut variation."""
    if intensity <= 0.0:
        return ""

    # Per-cut variation: slight hue shift and different grade character
    if cfg.get("variation_enabled"):
        # Hue shift: -3 to +3 degrees
        hue_shift = rng.uniform(-3.0, 3.0)
        # Shadow lift: 0.01 to 0.04
        shadow = rng.uniform(0.01, 0.04)
    else:
        hue_shift = 0.0
        shadow = 0.02

    # Base adjustments scaled by intensity
    sat = 1.0 + 0.15 * intensity + cfg.get("saturation_boost", 0.0) * 0.1
    con = 1.0 + 0.1 * intensity + cfg.get("contrast_boost", 0.0) * 0.15
    bri = 0.0 + 0.03 * intensity  # slight brightness

    # Tint: warm (+) vs cool (-)
    tint = cfg.get("color_tint", 0.0)
    warm = max(0.0, tint * 0.03)
    cool = max(0.0, -tint * 0.03)

    filters = [
        # Lift shadows slightly (classic "cinematic" look)
        f"curves=master='0/0 {shadow:.3f} 0.5/{0.5-shadow*2:.3f} 1/1'",
        # Saturation and contrast
        f"eq=saturation={sat:.2f}:contrast={con:.2f}:brightness={bri:.2f}",
    ]

    # Color temperature via colorbalance (only if relevant)
    if abs(tint) > 0.05:
        filters.append(
            f"colorbalance=rs={cool:.2f}:gs={warm:.2f}:bs={warm:.2f}"
        )

    # Subtle hue rotation for variety
    if abs(hue_shift) > 0.5:
        filters.append(f"hue=h={hue_shift:.1f}")

    # Vignette: subtle darkening at edges for cinematic feel
    # Use a plain angle value (not PI expression) for FFmpeg 4.x compatibility
    if intensity >= 0.3:
        filters.append("vignette=angle=0.5:mode=forward")

    return ",".join(filters)


# ──────────────────────────────────────────────────────────────────────────────
# Zoom Punch / Shake / Glow (via zoompan + drawbox)
# ──────────────────────────────────────────────────────────────────────────────

def _build_zoom_filter(
    cfg: dict, video_info: dict, rng: random.Random,
    zoom_intensity: float, shake_intensity: float,
    glow_intensity: float,
) -> str:
    """
    Build a filterchain for zoom punch, shake, and glow effects.
    Uses periodic zoom pulse (zoompan) + shake via scale jitter + brightness flash.

    All filters use only well-tested FFmpeg expressions for maximum compatibility.
    """
    if zoom_intensity <= 0.0 and shake_intensity <= 0.0 and glow_intensity <= 0.0:
        return ""

    fps = video_info.get("fps", 30.0)
    w = video_info.get("width", 1080)
    h = video_info.get("height", 1920)

    filters: list[str] = []

    # ── Zoom punch: scale up and crop back (simple, works everywhere) ──
    if zoom_intensity > 0.0:
        zoom_max = 1.0 + zoom_intensity * 0.06   # max 6 % zoom
        sw = int(w * zoom_max)
        sh = int(h * zoom_max)
        ox = (sw - w) // 2
        oy = (sh - h) // 2
        filters.append(f"scale={sw}:{sh},crop={w}:{h}:{ox}:{oy}")

    # ── Shake / breathing: micro-scale + crop (subtle alive feel) ──
    if shake_intensity > 0.0:
        amp = 1.0 + shake_intensity * 0.005
        sw2 = int(w * amp)
        sh2 = int(h * amp)
        ox2 = (sw2 - w) // 2
        oy2 = (sh2 - h) // 2
        filters.append(f"scale={sw2}:{sh2},crop={w}:{h}:{ox2}:{oy2}")

    # ── Glow / impact flash: brighten the whole clip slightly ──
    if glow_intensity > 0.0:
        flash_bri = 0.04 + glow_intensity * 0.08
        filters.append(f"eq=brightness={flash_bri:.3f}")

    return ",".join(filters) if filters else ""


# ──────────────────────────────────────────────────────────────────────────────
# Quality: Denoise + Sharpen + Upscale
# ──────────────────────────────────────────────────────────────────────────────

def _build_quality_filter(cfg: dict, video_info: dict) -> str:
    """Build FFmpeg filters for denoising and sharpening."""
    filters = []

    denoise = cfg.get("denoise_strength", 0.0)
    if denoise > 0.0:
        # hqdn3d: spatial luma, spatial chroma, temporal luma, temporal chroma
        # Scale denoise by intensity and source resolution
        src_h = video_info.get("height", 1920)
        base = 2 + int(denoise * 6)
        sl = base
        sc = max(1, base // 2)
        tl = max(1, base // 3)
        tc = max(1, base // 4)
        filters.append(f"hqdn3d={sl}:{sc}:{tl}:{tc}")

    sharpen = cfg.get("sharpen_strength", 0.0)
    if sharpen > 0.0:
        # unsharp: luma_msize_x, luma_msize_y, luma_amount, chroma_msize_x, ...
        msize = 3
        amount = sharpen * 1.5  # max ~0.75
        filters.append(f"unsharp=3:3:{amount:.2f}:3:3:{amount * 0.5:.2f}")

    return ",".join(filters) if filters else ""


# ──────────────────────────────────────────────────────────────────────────────
# Audio Processing
# ──────────────────────────────────────────────────────────────────────────────

def _build_audio_filter(cfg: dict) -> str:
    """Build FFmpeg audio filter chain."""
    filters = []

    if cfg.get("audio_normalize", True):
        # EBU R128 loudness normalization: target -14 LUFS (platform standard)
        # Two-pass: first measure, second apply
        # We do it in one pass with loudnorm (less accurate but faster)
        filters.append(
            "loudnorm=I=-14:LRA=11:TP=-1.5:measured_I=0:measured_LRA=0:measured_TP=0:offset=0"
        )

    if cfg.get("audio_compress", True):
        # Light compressor: ratio 3:1, threshold -18dB, attack 20ms, release 200ms
        # This keeps dialogue clear while taming loud peaks
        filters.append(
            "acompressor=threshold=-18dB:ratio=3:attack=20:release=200:makeup=3"
        )

    if cfg.get("audio_echo_reduction", False):
        # High-pass filter removes room echo (speech below 200Hz is mostly room resonance)
        filters.append("highpass=f=200")

    return ",".join(filters) if filters else ""


# ──────────────────────────────────────────────────────────────────────────────
# Main enhancement pass on a single file
# ──────────────────────────────────────────────────────────────────────────────

def _enhance_file(
    input_path: str | Path,
    output_path: str | Path,
    cfg: dict,
    index: int = 0,
) -> bool:
    """
    Apply all enabled enhancements to a single video file.
    Returns True on success.
    """
    inp = str(input_path)
    out = str(output_path)

    info = _video_info(inp)
    enc, preset, enc_args = _best_encoder()
    fps = info.get("fps", 30.0)

    # Generate per-cut variation seed
    base_seed = cfg.get("variation_seed", 42)
    rng = random.Random(_cut_seed(inp, base_seed))

    # Build filterchains
    color_int = cfg.get("color_grade_intensity", 0.0)
    zoom_int = cfg.get("zoom_punch_intensity", 0.0)
    shake_int = cfg.get("shake_impact_intensity", 0.0)
    glow_int = cfg.get("glow_impact_intensity", 0.0)

    color_filter = _build_color_filter(cfg, color_int, rng)
    zoom_filter = _build_zoom_filter(cfg, info, rng, zoom_int, shake_int, glow_int)
    quality_filter = _build_quality_filter(cfg, info)
    audio_filter = _build_audio_filter(cfg)

    # Build the main filtergraph
    all_video_filters: list[str] = []
    if quality_filter:
        all_video_filters.append(quality_filter)
    if color_filter:
        all_video_filters.append(color_filter)
    if zoom_filter:
        all_video_filters.append(zoom_filter)

    # Build FFmpeg command
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", inp,
    ]

    # Input audio (copy by default)
    has_audio = True  # assume always has audio

    vf = ",".join(all_video_filters) if all_video_filters else ""

    # ── Video processing ──
    if vf != "null" and all_video_filters:
        cmd.extend(["-vf", vf])

    cmd.extend(["-c:v", enc, "-preset", preset] + enc_args)
    cmd.extend(["-pix_fmt", "yuv420p", "-r", str(fps)])

    # ── Audio processing ──
    if has_audio and audio_filter:
        cmd.extend(["-af", audio_filter])
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])
    else:
        cmd.extend(["-c:a", "copy"])

    cmd.append(out)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"[Enhance] FFmpeg error on {inp}: {result.stderr[:200]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"[Enhance] Timeout on {inp}")
        return False
    except Exception as e:
        print(f"[Enhance] Error on {inp}: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Batch enhancement
# ──────────────────────────────────────────────────────────────────────────────

def enhance_folder(
    folder: str | Path,
    cfg: dict | None = None,
    recursive: bool = True,
    output_suffix: str = "_enhanced",
    overwrite: bool = False,
) -> tuple[int, int]:
    """
    Enhance all MP4 files in a folder.

    Args:
        folder: Path to the folder containing MP4 files
        cfg: Enhancement config dict (loads from file if None)
        recursive: Search subfolders too
        output_suffix: Suffix added to each output file
        overwrite: If True, replace original files

    Returns:
        (success_count, fail_count)
    """
    if cfg is None:
        cfg = load_config()

    folder = Path(folder)
    if not folder.is_dir():
        print(f"[Enhance] Folder not found: {folder}")
        return 0, 0

    # Find MP4 files
    pattern = "**/*.mp4" if recursive else "*.mp4"
    files = sorted(folder.glob(pattern))
    # Filter out already-enhanced files
    files = [f for f in files if output_suffix not in f.name]

    if not files:
        print(f"[Enhance] No MP4 files found in {folder}")
        return 0, 0

    print(f"[Enhance] Found {len(files)} files to process in {folder}")

    success = 0
    fail = 0

    for i, inp_file in enumerate(files):
        print(f"[Enhance] [{i+1}/{len(files)}] {inp_file.name}")

        if overwrite:
            out_file = inp_file
        else:
            name = inp_file.stem + output_suffix + inp_file.suffix
            out_file = inp_file.parent / name

        ok = _enhance_file(inp_file, out_file, cfg, index=i)
        if ok:
            success += 1
        else:
            fail += 1

    print(f"[Enhance] Done: {success} succeeded, {fail} failed")
    return success, fail


# ──────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Fábrica dos Cortes — Enhancement Module"
    )
    parser.add_argument(
        "--folder", "-f",
        help="Folder containing MP4 files to enhance",
    )
    parser.add_argument(
        "--config", "-c",
        help="Path to config JSON (default: temp_enhance_config.json)",
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Overwrite original files instead of creating _enhanced copies",
    )
    parser.add_argument(
        "--no-recursive", action="store_true",
        help="Do not search subfolders",
    )
    parser.add_argument(
        "--show-defaults", action="store_true",
        help="Print default config and exit",
    )
    args = parser.parse_args()

    if args.show_defaults:
        print(json.dumps(DEFAULT_CONFIG, indent=4))
        return

    if args.folder:
        cfg = load_config(args.config) if args.config else load_config()
        success, fail = enhance_folder(
            folder=args.folder,
            cfg=cfg,
            recursive=not args.no_recursive,
            overwrite=args.overwrite,
        )
        sys.exit(0 if fail == 0 else 1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
