# Summary

The Factory of Cuts has been enhanced with two new optional pipelines:

## 1. Video Enhancement Module (`scripts/enhance_video.py`)
- Applies sophisticated color grading, dynamic zoom punch, subtle shake/glow, quality improvements (denoise/sharpen/upscale), audio normalization, and anti-clone variation to finished cuts.
- All effects are configurable via `temp_enhance_config.json`, each individually toggleable.
- Compatible with the existing edit video workflow; can be chained after `edit_video`.
- Detects available GPU encoders and uses FFmpeg-optimized commands for speed.

## 2. Metrics Collection Module (`scripts/metrics.py`)
- Pulls YouTube channel data via yt-dlp (views, likes, comments, duration, publication) with optional cookie support.
- Parses TikTok Analytics Studio CSV exports to collect performance metrics.
- Merges both sources into a unified report, computes engagement rates, duration sweet-spot, optimal posting times and actionable recommendations.
- Generates an HTML dashboard and a JSON summary in `metrics_reports/`.
- Fail-tolerant: each video/row is processed independently.

## 3. WebUI Integration (webui/app.py) - PENDING
- Will add two new UI sections under the main "Criar Cortes" flow:
  * **Enhancement** – checkboxes for each effect (color, zoom, shake, glow, denoise, sharpen, upscale, audio options), sliders for intensity, and a "Run Enhancement" button that calls `enhance_video.enhance_folder` on the output folder.
  * **Metrics** – fields for YouTube channel URL, TikTok CSV upload, and a "Analyze & Generate Report" button that invokes `metrics.run_metrics`.
- Both tabs use lazy imports (`importlib`) to keep startup fast; if a dependency is missing, the UI still loads but warns the user.
- After processing, the UI shows a summary HTML report (live preview of metrics or a list of enhanced files) and/or offers to download the generated report folder.

## 4. Pipeline Integration
- The core `run_viral_cutter` already supports the `--enhance` and `--metrics` command-line switches.
- When `--enhance` is present, `edit_video.edit` is followed by `enhance_video.enhance_folder` on the `final` directory (or any target folder).
- When `--metrics` is present, `metrics.run_metrics` runs after the cut is completed, generating reports for the project's final cuts.
- Changes are backward-compatible – all existing workflows continue unchanged unless new flags are explicitly used.

## 5. New Configuration Files
- `temp_enhance_config.json` – settings for the enhancement pipeline (toggleable layers, intensity, variation seed, target folder, output suffix, overwrite).
- `temp_metrics_config.json` – YouTube channels, TikTok CSV paths, filters, days-back, top-N videos, output formats.
- Both files live in the repository root and can be edited while the app is running (the UI reloads the values from disk).

## 6. New Python Scripts (committed)
- `scripts/enhance_video.py` – full enhancement engine (color, zoom, shake, glow, denoise, sharpen, upscale, audio, variation).
- `scripts/metrics.py` – YouTube via yt-dlp + TikTok CSV -> HTML report generator.

## 7. Next Steps (for WebUI integration)
- Add enhancement panel after "Extras de publicação" accordion
- Add metrics panel as a new Accordion or separate tab
- Wire up callbacks to `scripts.enhance_video` and `scripts.metrics`
- Update `run_viral_cutter` signature to pass new parameters
- Update `main_improved.py` to invoke enhancement/metrics when flags are set