
def get_saved_gemini_key():
    try:
        cfg_path = os.path.join(WORKING_DIR, "api_config.json")
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8-sig") as f:
                d = json.load(f)
            k = d.get("gemini", {}).get("api_key", "").strip()
            if k:
                return k
    except Exception:
        pass
    return ""
import gradio as gr
import subprocess
import os
import sys
import json
import math
import psutil
import shutil
import datetime
import time
import urllib.parse
import platform
import threading
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn


import re
import library # Module for Library Logic
import studio # Biblioteca de cortes (galeria, estilos, música)
import subtitle_handler as subs # Module for Subtitles
import subtitle_editor as editor # Module for Editor Logic

# Path to the main script
MAIN_SCRIPT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main_improved.py")
WORKING_DIR = os.path.dirname(MAIN_SCRIPT_PATH)
sys.path.append(WORKING_DIR)

from i18n.i18n import I18nAuto
i18n = I18nAuto()

# --- PRESETS DEFINITIONS ---
FACE_PRESETS = {
    "Default (Balanced)": {"thresh": 0.35, "two_face": 0.60, "conf": 0.40, "dead_zone": 150},
    "Stable (Focus Main)": {"thresh": 0.60, "two_face": 0.80, "conf": 0.60, "dead_zone": 200},
    "Sensitive (Catch All)": {"thresh": 0.10, "two_face": 0.40, "conf": 0.30, "dead_zone": 100},
    "High Precision": {"thresh": 0.40, "two_face": 0.65, "conf": 0.75, "dead_zone": 150},
}

EXPERIMENTAL_PRESETS = {
    "Default (Off)": {"focus": False, "mar": 0.03, "score": 1.5, "motion": False, "motion_th": 3.0, "motion_sens": 0.05, "decay": 2.0},
    "Active Speaker (Balanced)": {"focus": True, "mar": 0.03, "score": 1.5, "motion": True, "motion_th": 3.0, "motion_sens": 0.05, "decay": 2.0},
    "Active Speaker (Sensitive)": {"focus": True, "mar": 0.02, "score": 1.0, "motion": True, "motion_th": 2.0, "motion_sens": 0.10, "decay": 1.0},
    "Active Speaker (Stable)": {"focus": True, "mar": 0.05, "score": 2.5, "motion": False, "motion_th": 5.0, "motion_sens": 0.02, "decay": 3.0},
}
# ---------------------------

VIRALS_DIR = os.path.join(WORKING_DIR, "VIRALS")
MODELS_DIR = os.path.join(WORKING_DIR, "models")

# Ensure directories exist
if not os.path.exists(VIRALS_DIR):
    os.makedirs(VIRALS_DIR, exist_ok=True)
if not os.path.exists(MODELS_DIR):
    os.makedirs(MODELS_DIR, exist_ok=True)

# Global variables
current_process = None
processing_lock = threading.Lock()


def _stop_process_tree(proc, timeout=3):
    """Stop the app child and its FFmpeg/yt-dlp descendants, then reap every handle."""
    if proc is None:
        return
    try:
        root = psutil.Process(proc.pid)
        descendants = root.children(recursive=True)
        for child in descendants:
            try:
                child.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        try:
            root.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        _, alive = psutil.wait_procs([*descendants, root], timeout=timeout)
        for child in alive:
            try:
                child.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        psutil.wait_procs(alive, timeout=timeout)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
        except Exception:
            pass
        try:
            proc.wait(timeout=timeout)
        except Exception:
            pass

# License helpers (online required)
def _license_settings_path():
    if os.name == 'nt':
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
        return os.path.join(base, 'ForjaViral', 'license_settings.json')
    sysname = platform.system().lower()
    if sysname == 'darwin':
        return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'ForjaViral', 'license_settings.json')
    return os.path.join(os.path.expanduser('~'), '.forja_viral', 'license_settings.json')


def _load_license_settings():
    try:
        p = _license_settings_path()
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                return {
                    'base_url': str(data.get('base_url') or '').strip(),
                    'license_key': str(data.get('license_key') or '').strip(),
                }
    except Exception:
        pass
    return {'base_url': '', 'license_key': ''}

# Helpers
def convert_color_to_ass(hex_color, alpha="00"):
    try:
        with open("debug_colors.log", "a") as f:
             f.write(f"INPUT: '{hex_color}'\n")
    except: pass

    if not hex_color:
        return f"&H{alpha}FFFFFF&"
    
    hex_clean = hex_color.lstrip('#').strip()
    
    # Handle rgb/rgba format: rgb(255, 215, 0)
    if hex_clean.lower().startswith("rgb"):
        try:
            # Extract numbers including floats
            nums = re.findall(r"[\d\.]+", hex_clean)
            if len(nums) >= 3:
                r = int(float(nums[0]))
                g = int(float(nums[1]))
                b = int(float(nums[2]))
                # Clamp
                r = max(0, min(255, r))
                g = max(0, min(255, g))
                b = max(0, min(255, b))
                # Convert to hex
                ret = f"&H{alpha}{b:02X}{g:02X}{r:02X}&".upper()
                try:
                    with open("debug_colors.log", "a") as f:
                         f.write(f"PARSED RGB: {ret}\n")
                except: pass
                return ret
        except Exception as e:
            try:
                with open("debug_colors.log", "a") as f:
                     f.write(f"RGB ERROR: {e}\n")
            except: pass

    # Handle 3-digit hex (e.g. F00 -> FF0000)
    if len(hex_clean) == 3:
        hex_clean = "".join([c*2 for c in hex_clean])
        
    if len(hex_clean) == 6:
        r = hex_clean[0:2]
        g = hex_clean[2:4]
        b = hex_clean[4:6]
        # Uppercase just in case
        ret = f"&H{alpha}{b}{g}{r}&".upper() 
        try:
            with open("debug_colors.log", "a") as f:
                 f.write(f"PARSED HEX: {ret}\n")
        except: pass
        return ret
        
    try:
        with open("debug_colors.log", "a") as f:
             f.write(f"INVALID: Defaulting to White\n")
    except: pass
    return f"&H{alpha}FFFFFF&"

def kill_process():
    global current_process
    if current_process is not None:
        try:
            proc = current_process
            _stop_process_tree(proc)
            if current_process is proc:
                current_process = None
            return i18n("Process terminated.")
        except Exception as e:
            current_process = None
            return i18n("Error terminating process: {}").format(e)
    return i18n("No process running.")

def count_generated_cuts(project_folder_path, start_time=None):
    """
    Conta com precisao a quantidade de videos de cortes gerados com sucesso nesta execucao.
    Verifica as pastas em ordem de prioridade de acordo com o workflow: burned_sub -> final -> cuts.
    Apenas arquivos .mp4 validos (> 20KB) e modificados apos start_time sao considerados.
    """
    if not project_folder_path or not os.path.exists(project_folder_path):
        return 0
    
    for subdir in ["burned_sub", "final", "cuts"]:
        folder = os.path.join(project_folder_path, subdir)
        if os.path.exists(folder):
            valid_cuts = []
            for f in os.listdir(folder):
                if not f.lower().endswith(".mp4"):
                    continue
                # Ignora video original de entrada e temporarios
                if "input" in f.lower() or "temp_video_no_audio" in f.lower() or f.endswith(".temp.mp4"):
                    continue
                full_path = os.path.join(folder, f)
                try:
                    if not os.path.isfile(full_path):
                        continue
                    # Video precisa ter pelo menos 20KB para ser valido
                    if os.path.getsize(full_path) < 20480:
                        continue
                    probe = subprocess.run(
                        [
                            "ffprobe", "-v", "error", "-show_entries",
                            "stream=codec_type:format=duration", "-of", "json", full_path,
                        ],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    media_info = json.loads(probe.stdout) if probe.returncode == 0 else {}
                    streams = media_info.get("streams") or []
                    duration = float((media_info.get("format") or {}).get("duration") or 0)
                    if not any(s.get("codec_type") == "video" for s in streams) or not math.isfinite(duration) or duration <= 0:
                        continue
                    # Se start_time foi informado, garante que foi criado/modificado nesta execucao
                    if start_time is not None:
                        if os.path.getmtime(full_path) < (start_time - 5):
                            continue
                    valid_cuts.append(full_path)
                except (OSError, ValueError, subprocess.SubprocessError):
                    continue
            
            if valid_cuts:
                return len(valid_cuts)
                
    return 0

GEMINI_MODELS = [
    'gemini-2.5-flash',
    'gemini-flash-latest',
    'gemini-2.5-flash-lite',
    'gemini-flash-lite-latest',
    'gemini-3.8-flash',
    'gemini-2.5-pro',
    'gemini-pro-latest'
]

G4F_MODELS = [
    'gpt-4o',
    'gpt-4o-mini',
    'gpt-4',
    'o1-mini',
    'o1',
    'deepseek-r1',
    'deepseek-v3',
    'llama-3.3-70b',
    'llama-3.1-405b',
    'claude-3.5-sonnet',
    'claude-3.7-sonnet',
    'gemini-2.0-flash',
    'qwen-2.5-72b'
]

def get_local_models():
    if not os.path.exists(MODELS_DIR): return []
    return [f for f in os.listdir(MODELS_DIR) if f.endswith(".gguf")]



def apply_face_preset(preset_name):
    if preset_name not in FACE_PRESETS:
        return [gr.update() for _ in range(4)] # No change
    
    p = FACE_PRESETS[preset_name]
    return p["thresh"], p["two_face"], p["conf"], p["dead_zone"]

def apply_experimental_preset(preset_name):
    if preset_name not in EXPERIMENTAL_PRESETS:
        return [gr.update() for _ in range(7)] # No change
        
    p = EXPERIMENTAL_PRESETS[preset_name]
    return p["focus"], p["mar"], p["score"], p["motion"], p["motion_th"], p["motion_sens"], p["decay"]

# Subtitle logic moved to subtitle_handler.py


def run_viral_cutter(input_source, project_name, url, video_file, segments, viral, themes, min_duration, max_duration, model, ai_backend, api_key, ai_model_name, chunk_size, workflow, face_model, face_mode, face_detect_interval, no_face_mode, 
                     face_filter_thresh, face_two_thresh, face_conf_thresh, face_dead_zone, focus_active_speaker, active_speaker_mar, active_speaker_score_diff, include_motion, active_speaker_motion_threshold, active_speaker_motion_sensitivity, active_speaker_decay,
                     use_custom_subs, font_name, font_size, font_color, highlight_color, outline_color, outline_thickness, shadow_color, shadow_size, is_bold, is_italic, is_uppercase, vertical_pos, alignment,
                     h_size, w_block, gap, mode, under, strike, border_s, remove_punc, video_quality, use_youtube_subs, translate_target):
    
    global current_process
    process_start_time = time.time()
    return_code = -1
    yield "", gr.update(value="Gerando...", interactive=False), gr.update(visible=True), None, gr.update(), _render_progress_html(3, "Iniciando...")

    cmd = [sys.executable, MAIN_SCRIPT_PATH]
    
    # Input Source Logic
    if input_source == "Existing Project":
        if not project_name:
             yield "Selecione um projeto.", gr.update(value="Gerar Cortes", interactive=True), gr.update(visible=False), None, gr.update(), _render_progress_html(0, "Selecione um projeto.")
             return
        full_project_path = os.path.join(VIRALS_DIR, project_name)
        cmd.extend(["--project-path", full_project_path])
    elif input_source == "Upload Video":
        if not video_file:
             yield "Envie um vídeo para continuar.", gr.update(value="Gerar Cortes", interactive=True), gr.update(visible=False), None, gr.update(), _render_progress_html(0, "Envie um vídeo.")
             return
        
        # Determine project name from filename
        original_filename = os.path.basename(video_file)
        name_no_ext = os.path.splitext(original_filename)[0]
        # Sanitize: Allow alphanumeric, space, dash, underscore
        safe_name = "".join([c for c in name_no_ext if c.isalnum() or c in " _-"]).strip()
        if not safe_name: safe_name = "Untitled_Upload"
        
        # Always append timestamp as requested
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name_upload = f"{safe_name}_{timestamp}"
        project_path = os.path.join(VIRALS_DIR, project_name_upload)
             
        os.makedirs(project_path, exist_ok=True)
        
        target_path = os.path.join(project_path, "input.mp4")
        shutil.copy(video_file, target_path)
        
        cmd.extend(["--project-path", project_path])
        # Skip YouTube subs as it is a local upload
        cmd.append("--skip-youtube-subs")
        
    else:
        if url: cmd.extend(["--url", url])
        # Pass Video Quality
        if video_quality: cmd.extend(["--video-quality", video_quality])
        # Pass Subtitle Option (if False, we skip)
        if not use_youtube_subs: cmd.append("--skip-youtube-subs")
        
    # Translation
    if translate_target and translate_target != "None":
            cmd.extend(["--translate-target", translate_target])

    
    cmd.extend(["--segments", str(int(segments))])
    if viral: cmd.append("--viral")
    if themes: cmd.extend(["--themes", themes])
    cmd.extend(["--min-duration", str(int(min_duration))])
    cmd.extend(["--max-duration", str(int(max_duration))])
    if api_key and api_key.strip():
        try:
            cfg_p = os.path.join(WORKING_DIR, "api_config.json")
            if os.path.exists(cfg_p):
                with open(cfg_p, "r", encoding="utf-8-sig") as cf:
                    cdata = json.load(cf)
                if cdata.get("gemini", {}).get("api_key") != api_key.strip():
                    cdata.setdefault("gemini", {})["api_key"] = api_key.strip()
                    with open(cfg_p, "w", encoding="utf-8") as cf:
                        json.dump(cdata, cf, indent=4)
        except Exception:
            pass

    cmd.extend(["--model", model])
    cmd.extend(["--ai-backend", ai_backend])
    if api_key: cmd.extend(["--api-key", api_key])
    
    # New AI Params
    if ai_model_name: cmd.extend(["--ai-model-name", str(ai_model_name)])
    if chunk_size: cmd.extend(["--chunk-size", str(int(chunk_size))])

    workflow_map = {"Full": "1", "Cut Only": "2", "Subtitles Only": "3"}
    cmd.extend(["--workflow", workflow_map.get(workflow, "1")])
    cmd.extend(["--face-model", face_model])
    cmd.extend(["--face-mode", face_mode])
    if face_detect_interval: cmd.extend(["--face-detect-interval", str(face_detect_interval)])
    if no_face_mode: cmd.extend(["--no-face-mode", no_face_mode])
    
    # New Face Params
    if face_filter_thresh is not None: cmd.extend(["--face-filter-threshold", str(face_filter_thresh)])
    if face_two_thresh is not None: cmd.extend(["--face-two-threshold", str(face_two_thresh)])
    if face_conf_thresh is not None: cmd.extend(["--face-confidence-threshold", str(face_conf_thresh)])
    if face_dead_zone is not None: cmd.extend(["--face-dead-zone", str(face_dead_zone)])


    
    cmd.append("--skip-prompts")
    
    if focus_active_speaker:
        cmd.append("--focus-active-speaker")
        if active_speaker_mar is not None: cmd.extend(["--active-speaker-mar", str(active_speaker_mar)])
        if active_speaker_score_diff is not None: cmd.extend(["--active-speaker-score-diff", str(active_speaker_score_diff)])
        if include_motion: cmd.append("--include-motion")
        if active_speaker_motion_threshold is not None: cmd.extend(["--active-speaker-motion-threshold", str(active_speaker_motion_threshold)])
        if active_speaker_motion_sensitivity is not None: cmd.extend(["--active-speaker-motion-sensitivity", str(active_speaker_motion_sensitivity)])
        if active_speaker_decay is not None: cmd.extend(["--active-speaker-decay", str(active_speaker_decay)])

    cmd.append("--skip-prompts") # Always skip prompts in WebUI to prevent freezing

    if use_custom_subs:
        subtitle_config = {
            "font": font_name, "base_size": int(font_size), "base_color": convert_color_to_ass(font_color), "highlight_color": convert_color_to_ass(highlight_color),
            "outline_color": convert_color_to_ass(outline_color), "outline_thickness": outline_thickness, "shadow_color": convert_color_to_ass(shadow_color),
            "shadow_size": shadow_size, "vertical_position": vertical_pos, "alignment": alignment, "bold": 1 if is_bold else 0, "italic": 1 if is_italic else 0, 
            "underline": 1 if under else 0, "strikeout": 1 if strike else 0, "border_style": border_s, "words_per_block": int(w_block), "gap_limit": gap,
            "mode": mode, "highlight_size": int(h_size), "remove_punctuation": remove_punc
        }
        # Uppercase is handled in main script or logic? 
        # Actually subtitle_config doesn't seem to natively support "uppercase" in get_subtitle_config default, but app.py was using it. 
        # I should probably add it back if I want to support it, but user said "PROHIBITED to remove existing ones".
        # I'll re-add 'uppercase': 1 if is_uppercase else 0 to the dict if the backend supports it, otherwise it's just ignored.
        # But wait, main_improved.py doesn't have 'uppercase' in get_subtitle_config. 
        # I'll keep it in the dict just in case logic uses it elsewhere or if I missed it.
        # Actually, standard ASS doesn't support uppercase flag directly in Style, it needs to be text transform.
        # But I'll leave it in the dict.
        subtitle_config["uppercase"] = 1 if is_uppercase else 0

        subtitle_config_path = os.path.join(WORKING_DIR, "temp_subtitle_config.json")
        try:
            with open(subtitle_config_path, "w", encoding="utf-8") as f:
                json.dump(subtitle_config, f, indent=4)
            cmd.extend(["--subtitle-config", subtitle_config_path])
        except Exception: pass 
    
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    if not processing_lock.acquire(blocking=False):
        yield "Já existe um processamento ativo. Aguarde ou cancele a execução atual.", gr.update(value="Gerar Cortes", interactive=True), gr.update(visible=False), None, gr.update(), _render_progress_html(0, "Já existe um processamento ativo.")
        return
    proc = None
    logs = ""
    project_folder_path = None
    actual_cuts = 0
    progress_percent = 3
    progress_label = "Iniciando..."
    asked_segments = int(segments or 1)
    to_debit = 0
    settlement_ok = False
    try:
        current_process = subprocess.Popen(
            cmd,
            cwd=WORKING_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            universal_newlines=True,
            env=env,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0,
        )
        proc = current_process
        if input_source == "Existing Project" and project_name:
             # If using existing project, we already know the path, but let's see if logs confirm it
             project_folder_path = os.path.join(VIRALS_DIR, project_name)

        last_update_time = time.time()
        is_last_download_line = False
        
        while proc is not None:
            if current_process is None:
                logs += "\n[AVISO] Processo cancelado pelo usuário.\n"
                break
            try:
                line = proc.stdout.readline() if (proc and proc.stdout) else ""
            except (UnicodeDecodeError, OSError):
                time.sleep(0.02)
                continue
            except Exception:
                break
            
            if not line:
                if current_process is None:
                    break
                try:
                    if proc is None or getattr(proc, 'poll', lambda: 0)() is not None:
                        break
                except Exception:
                    break
                time.sleep(0.05)
                continue
            
            clean_line = line.strip('\r\n')
            if not clean_line or clean_line.isspace():
                continue
            
            # Suprime cabeçalhos vazios ou repetitivos do Aria2
            if clean_line.startswith("*** Download Progress") or clean_line.startswith("FILE:"):
                continue

            is_download = (clean_line.startswith("[#") and "%" in clean_line) or (clean_line.startswith("[download]") and "%" in clean_line)
            if clean_line.startswith("[#") and "%" in clean_line:
                clean_line = f"[Download Turbo] {clean_line}"

            if is_download:
                if is_last_download_line:
                    last_newline = logs.rfind('\n', 0, -1)
                    if last_newline != -1:
                        logs = logs[:last_newline + 1] + clean_line + "\n"
                    else:
                        logs = clean_line + "\n"
                else:
                    logs += clean_line + "\n"
                    is_last_download_line = True
            else:
                is_last_download_line = False
                logs += clean_line + "\n"

            if "Project Folder:" in clean_line:
                parts = clean_line.split("Project Folder:")
                if len(parts) > 1: project_folder_path = parts[1].strip()

            # Atualiza a barra de progresso conforme o estagio do backend.
            lower_line = clean_line.lower()
            if "transcribing" in lower_line or "whisper" in lower_line or "transcrevendo" in lower_line:
                if progress_percent < 30:
                    progress_percent, progress_label = 30, "Transcrevendo o audio..."
            elif "creating viral" in lower_line or "analyzing" in lower_line or "gemini" in lower_line or "g4f" in lower_line or "viral segments" in lower_line:
                if progress_percent < 50:
                    progress_percent, progress_label = 50, "Analisando os melhores cortes..."
            elif "cutting" in lower_line or "cut segments" in lower_line or "cortando" in lower_line:
                if progress_percent < 70:
                    progress_percent, progress_label = 70, "Cortando os videos..."
            elif "subtitle" in lower_line or "legend" in lower_line or "burn" in lower_line:
                if progress_percent < 85:
                    progress_percent, progress_label = 85, "Aplicando legendas..."
            elif "download" in lower_line or "baixando" in lower_line:
                if progress_percent < 15:
                    progress_percent, progress_label = 15, "Baixando o video..."
            elif "done" in lower_line or "completed" in lower_line or "conclu" in lower_line:
                if progress_percent < 95:
                    progress_percent, progress_label = 95, "Finalizando..."
            
            # Throttle updates to avoid browser freeze (0.2s interval)
            current_time = time.time()
            if current_time - last_update_time > 0.2:
                yield logs, gr.update(visible=True, interactive=False), gr.update(visible=True), None, gr.update(), _render_progress_html(progress_percent, progress_label)
                last_update_time = current_time
        
        # Final yield to ensure all logs are shown
        yield logs, gr.update(visible=True, interactive=False), gr.update(visible=True), None, gr.update(), _render_progress_html(progress_percent, progress_label)
    except Exception as e:
        logs += f"\nErro ao executar o processo: {str(e)}\n"
        yield logs, gr.update(visible=True, interactive=False), gr.update(visible=True), None, gr.update(), _render_progress_html(0, "Erro no processamento.")
    finally:
        if proc is not None:
            try:
                if getattr(proc, 'poll', lambda: 0)() is None:
                    proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                _stop_process_tree(proc)
            except Exception:
                pass
            if getattr(proc, 'stdout', None):
                try: proc.stdout.close()
                except Exception: pass
            return_code = getattr(proc, 'returncode', -1)
            if return_code is None:
                return_code = -1
            if current_process is proc:
                current_process = None
        else:
            return_code = -1
        # Settle before yielding out of this generator so client disconnect/cancel
        # cannot release a reservation while leaving completed cuts available.
        try:
            actual_cuts = count_generated_cuts(project_folder_path, start_time=process_start_time)
            to_debit = min(actual_cuts, asked_segments)
            settlement_ok = _gate.settle_delivered(to_debit)
        except Exception as settlement_error:
            # If output counting itself fails, retain the full reservation rather than
            # accidentally releasing credits for potentially delivered files.
            try:
                _gate.settle_delivered(asked_segments)
            except Exception:
                pass
            logs += f"\n[AVISO CRÉDITOS] Falha ao liquidar reserva: {settlement_error}\n"
        finally:
            processing_lock.release()
    
    # Wait to ensure filesystem flush
    time.sleep(1.0)
    
    # Verificação justa de créditos: debita proporcionalmente pelos cortes efetivamente gerados!
    if actual_cuts > 0:
        try:
            if settlement_ok:
                logs += f"\n\n========================================================"
                if return_code == 0 and actual_cuts >= asked_segments:
                    logs += f"\n[CRÉDITOS] Sucesso total! {actual_cuts} corte(s) gerado(s) com sucesso."
                else:
                    logs += f"\n[CRÉDITOS] Processo finalizado com {actual_cuts} corte(s) entregue(s) com sucesso."
                logs += f"\n[CRÉDITOS] Reserva liquidada: {to_debit} crédito(s) pelos vídeos entregues."
                logs += f"\n[CRÉDITOS] Saldo restante: {_gate.state.credits} crédito(s)."
                logs += f"\n========================================================\n"
            else:
                logs += f"\n\n[AVISO CRÉDITOS] Cortes gerados ({actual_cuts}), mas não foi possível conectar ao servidor para sincronizar créditos.\n"
        except Exception as e_cred:
            logs += f"\n\n[AVISO CRÉDITOS] Erro ao sincronizar créditos com o servidor: {e_cred}\n"
    else:
        logs += f"\n\n========================================================"
        logs += "\n[ERRO] Nenhum corte foi gerado nesta execucao."
        logs += "\n[ERRO] Verifique a chave e o modelo da IA (Gemini/G4F)."
        logs += "\n[ERRO] Nenhum credito foi debitado."
        logs += f"\n[CRÉDITOS] Nenhum vídeo de corte foi finalizado nesta execução."
        logs += "\n[CRÉDITOS] Reserva integral devolvida." if settlement_ok else "\n[AVISO CRÉDITOS] Não foi possível confirmar a devolução; contate o suporte com este log."
        logs += f"\n[CRÉDITOS] Saldo preservado: {_gate.state.credits} crédito(s)."
        logs += f"\n========================================================\n"

    html_output = ""
    if project_folder_path and os.path.exists(project_folder_path):
        html_output = library.generate_project_gallery(project_folder_path, is_full_path=True)
    else:
        html_output = "<h3>Não foi possível localizar a pasta do projeto.</h3>"
    final_progress = (
        _render_progress_html(100, "Cortes prontos!")
        if actual_cuts > 0
        else _render_progress_html(0, "Nenhum corte foi gerado.")
    )
    yield logs, gr.update(value="Gerar Cortes", interactive=True), gr.update(visible=False), html_output, _render_topbar_html(), final_progress

css = """
/* ===== Fábrica dos Cortes • tema laranja estilo Opus ===== */
:root {
    --fdc-grad: linear-gradient(135deg, #FF8A2A 0%, #FF5C00 55%, #E04800 100%);
    --body-background-fill: #070504;
    --background-fill-primary: #070504;
    --background-fill-secondary: #0f0a07;
    --block-background-fill: transparent;
    --block-border-color: transparent;
    --block-shadow: none;
    --block-label-text-color: #cbb9ab;
    --block-title-text-color: #ffffff;
    --body-text-color: #f7efe9;
    --body-text-color-subdued: #a99a8d;
    --input-background-fill: #0c0908;
    --input-border-color: rgba(255, 255, 255, 0.09);
    --color-accent: #FF5C00;
    --color-accent-soft: rgba(255, 92, 0, 0.16);
    --checkbox-background-color-selected: #FF5C00;
    --checkbox-border-color-selected: #FF5C00;
    --button-primary-background-fill: linear-gradient(135deg, #FF8A2A 0%, #FF5C00 55%, #E04800 100%);
    --button-primary-background-fill-hover: linear-gradient(135deg, #FF9A3A 0%, #FF6A10 55%, #E85200 100%);
    --button-primary-text-color: #ffffff;
    --button-primary-border-color: transparent;
    --slider-color: #FF5C00;
}

html,
body {
    background: #070504 !important;
}

body {
    background:
        radial-gradient(1000px 520px at 100% -12%, rgba(255, 92, 0, 0.16), transparent 62%),
        radial-gradient(800px 420px at -8% 112%, rgba(255, 92, 0, 0.07), transparent 60%),
        #070504 !important;
    color: #f7efe9 !important;
}

/* O Gradio redefine estas variáveis no próprio .gradio-container; o !important mantém o tema escuro */
.gradio-container {
    --background-fill-primary: #070504 !important;
    --background-fill-secondary: #0f0a07 !important;
    --block-background-fill: transparent !important;
    --block-border-color: transparent !important;
    --block-label-text-color: #cbb9ab !important;
    --block-title-text-color: #ffffff !important;
    --body-text-color: #f7efe9 !important;
    --body-text-color-subdued: #a99a8d !important;
    --input-background-fill: #0c0908 !important;
    --input-background-fill-focus: #0c0908 !important;
    --input-border-color: rgba(255, 255, 255, 0.09) !important;
    --input-border-color-focus: rgba(255, 107, 26, 0.75) !important;
    --input-placeholder-color: #6f625a !important;
    --checkbox-label-background-fill: transparent !important;
    --checkbox-label-background-fill-hover: rgba(255, 92, 0, 0.06) !important;
    --checkbox-label-background-fill-selected: transparent !important;
    --checkbox-label-border-color: transparent !important;
    --checkbox-label-text-color: #f7efe9 !important;
    --checkbox-label-text-color-selected: #ffffff !important;
    --checkbox-background-color: #0c0908 !important;
    --checkbox-border-color: rgba(255, 255, 255, 0.18) !important;
    --checkbox-background-color-selected: #FF5C00 !important;
    --checkbox-border-color-selected: #FF5C00 !important;
    --button-secondary-background-fill: rgba(255, 92, 0, 0.10) !important;
    --button-secondary-background-fill-hover: rgba(255, 92, 0, 0.18) !important;
    --button-secondary-border-color: rgba(255, 92, 0, 0.35) !important;
    --button-secondary-text-color: #FFB27A !important;
    --button-primary-background-fill: linear-gradient(135deg, #FF8A2A 0%, #FF5C00 55%, #E04800 100%) !important;
    --button-primary-background-fill-hover: linear-gradient(135deg, #FF9A3A 0%, #FF6A10 55%, #E85200 100%) !important;
    --button-primary-text-color: #ffffff !important;
    --color-accent: #FF5C00 !important;
    --color-accent-soft: rgba(255, 92, 0, 0.16) !important;
    --border-color-primary: rgba(255, 107, 26, 0.16) !important;
    --panel-background-fill: #120c09 !important;
    --table-even-background-fill: #120c09 !important;
    --table-odd-background-fill: #0f0a07 !important;
    --slider-color: #FF5C00 !important;
    background: transparent !important;
    max-width: 1240px !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 20px 28px 48px 124px !important;
    box-sizing: border-box !important;
    color: #f7efe9 !important;
    font-family: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif !important;
}

footer {
    visibility: hidden !important;
    height: 0 !important;
}

::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: transparent;
}

::-webkit-scrollbar-thumb {
    background: rgba(255, 107, 26, 0.28);
    border-radius: 999px;
    border: 2px solid transparent;
    background-clip: padding-box;
}

/* ----- Barra lateral ----- */
#fdc-rail {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    bottom: 0 !important;
    width: 92px !important;
    height: 100vh !important;
    margin: 0 !important;
    padding: 0 !important;
    z-index: 60 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

#fdc-rail .block,
#fdc-rail .prose {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
    height: 100% !important;
    min-height: 0 !important;
}

.fdc-rail {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px 0 18px 0;
    background: linear-gradient(180deg, #0c0907 0%, #070504 100%);
    border-right: 1px solid rgba(255, 107, 26, 0.10);
    box-shadow: 14px 0 40px rgba(0, 0, 0, 0.35);
}

.fdc-rail-logo {
    width: 46px;
    height: 46px;
    margin-bottom: 26px;
}

.fdc-rail-logo img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    filter: drop-shadow(0 6px 16px rgba(255, 92, 0, 0.45));
}

.fdc-rail-item {
    position: relative;
    width: 50px;
    height: 50px;
    margin: 6px 0;
    border: none;
    border-radius: 16px;
    background: transparent;
    color: #8c7d71;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
}

.fdc-rail-item:hover {
    color: #FFB27A;
    background: rgba(255, 92, 0, 0.08);
}

.fdc-rail-item.active {
    color: #FF6A1A;
    background: rgba(255, 92, 0, 0.13);
    box-shadow: inset 0 0 0 1px rgba(255, 92, 0, 0.28);
}

.fdc-rail-item.active::before {
    content: "";
    position: absolute;
    left: -21px;
    top: 12px;
    bottom: 12px;
    width: 4px;
    border-radius: 0 6px 6px 0;
    background: var(--fdc-grad);
    box-shadow: 0 0 16px rgba(255, 92, 0, 0.6);
}

.fdc-rail-foot {
    margin-top: auto;
    font-size: 10px;
    letter-spacing: 0.6px;
    color: #6d6056;
}

/* ----- Blocos sem moldura (wrappers do Gradio) ----- */
.fdc-bare,
.fdc-bare .block,
.fdc-bare .prose {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

#progress_panel {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

/* ----- Barra superior (créditos + atualizar) ----- */
#fdc-topbar {
    align-items: center !important;
    gap: 12px !important;
    margin: 0 0 14px 0 !important;
}

.fv-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 11px 16px;
    border-radius: 16px;
    background: linear-gradient(180deg, rgba(27, 18, 12, 0.92), rgba(14, 10, 7, 0.92));
    border: 1px solid rgba(255, 107, 26, 0.14);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.28);
}

.fv-topbar-left {
    display: flex;
    flex-direction: column;
    gap: 3px;
    min-width: 0;
}

.fv-credits {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 800;
}

.fv-credits span {
    font-size: 14px;
    color: #ffffff;
}

.fv-sub {
    font-size: 12px;
    color: #a99a8d;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 560px;
}

.fv-status {
    font-weight: 900;
    padding: 7px 12px;
    border-radius: 999px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(0, 0, 0, 0.25);
    font-size: 11px;
    letter-spacing: 0.3px;
    white-space: nowrap;
}

.fv-status.ok {
    color: #4ade80;
    border-color: rgba(34, 197, 94, 0.35);
    background: rgba(34, 197, 94, 0.10);
}

.fv-status.bad {
    color: #f87171;
    border-color: rgba(239, 68, 68, 0.38);
    background: rgba(239, 68, 68, 0.10);
}

#refresh_credits {
    height: 52px !important;
    border-radius: 16px !important;
    font-weight: 800 !important;
    background: rgba(255, 92, 0, 0.10) !important;
    color: #FFB27A !important;
    border: 1px solid rgba(255, 92, 0, 0.35) !important;
}

#refresh_credits:hover {
    background: rgba(255, 92, 0, 0.18) !important;
}

/* ----- Abas no topo ----- */
.tab-wrapper {
    border-bottom: 1px solid rgba(255, 255, 255, 0.07) !important;
    margin-bottom: 22px !important;
}

.tab-container {
    gap: 4px !important;
}

.tab-container button {
    position: relative !important;
    display: inline-flex !important;
    align-items: center;
    gap: 9px;
    padding: 13px 18px !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    color: #9d8e82 !important;
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    transition: color 0.2s ease;
}

.tab-container button::before {
    content: "";
    width: 17px;
    height: 17px;
    flex-shrink: 0;
    background: currentColor;
    -webkit-mask: var(--fdc-ico, none) center / contain no-repeat;
    mask: var(--fdc-ico, none) center / contain no-repeat;
}

.tab-container button:hover {
    color: #ffd2b5 !important;
}

.tab-container button.selected {
    color: #ffffff !important;
}

.tab-container button.selected::after {
    content: "";
    position: absolute;
    left: 14px;
    right: 14px;
    bottom: -1px;
    height: 3px;
    border-radius: 3px;
    background: var(--fdc-grad);
    box-shadow: 0 0 14px rgba(255, 92, 0, 0.65);
}

/* ----- Cards ----- */
.fdc-card {
    position: relative;
    background: linear-gradient(180deg, rgba(31, 21, 15, 0.92) 0%, rgba(15, 10, 7, 0.95) 100%) !important;
    border: 1px solid rgba(255, 107, 26, 0.16) !important;
    border-radius: 22px !important;
    padding: 18px 18px 16px 18px !important;
    box-shadow: 0 16px 44px rgba(0, 0, 0, 0.36), inset 0 1px 0 rgba(255, 255, 255, 0.035) !important;
    gap: 12px !important;
}

.fdc-card .block {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

.gradio-container .form {
    background: transparent !important;
}

.fdc-head {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 0 0 12px 0;
}

.fdc-head .ico {
    width: 40px;
    height: 40px;
    flex-shrink: 0;
    border-radius: 13px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #FF8A4C;
    background: linear-gradient(135deg, rgba(255, 122, 26, 0.22), rgba(255, 92, 0, 0.05));
    border: 1px solid rgba(255, 107, 26, 0.28);
    box-shadow: 0 8px 22px rgba(255, 92, 0, 0.12);
}

.fdc-head .t {
    font-size: 15px;
    font-weight: 800;
    color: #ffffff;
    line-height: 1.2;
}

.fdc-head .s {
    font-size: 12px;
    color: #a99a8d;
    margin-top: 3px;
    line-height: 1.35;
}

.fdc-head .s a {
    color: #FF8A4C;
    font-weight: 700;
    text-decoration: none;
}

.fdc-head-lg .ico {
    width: 48px;
    height: 48px;
    border-radius: 15px;
}

.fdc-head-lg .t {
    font-size: 20px;
}

.fdc-head-lg .s {
    font-size: 13px;
}

/* ----- Campos ----- */
.gradio-container input:not([type="checkbox"]):not([type="radio"]):not(.border-none),
.gradio-container textarea,
.gradio-container select {
    background-color: #0c0908 !important;
    border: 1px solid rgba(255, 255, 255, 0.09) !important;
    border-radius: 14px !important;
    color: #ffffff !important;
    font-weight: 600 !important;
}

.gradio-container input:not([type="checkbox"]):not([type="radio"]):not(.border-none):focus,
.gradio-container textarea:focus {
    border-color: rgba(255, 107, 26, 0.75) !important;
    box-shadow: 0 0 0 3px rgba(255, 92, 0, 0.16) !important;
    outline: none !important;
}

.gradio-container input::placeholder,
.gradio-container textarea::placeholder {
    color: #6f625a !important;
    font-weight: 500 !important;
}

.gradio-container input.border-none {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

.gradio-container ul.options {
    background: #120c09 !important;
    border: 1px solid rgba(255, 107, 26, 0.22) !important;
    border-radius: 14px !important;
    box-shadow: 0 18px 44px rgba(0, 0, 0, 0.55) !important;
}

.gradio-container ul.options li {
    color: #f7efe9 !important;
}

.gradio-container ul.options li:hover,
.gradio-container ul.options li.selected {
    background: rgba(255, 92, 0, 0.16) !important;
    color: #ffffff !important;
}

.fdc-card input[type="number"] {
    font-size: 22px !important;
    font-weight: 800 !important;
    height: 54px !important;
    padding-left: 16px !important;
}

#url_input textarea,
#url_input input {
    padding-left: 46px !important;
    min-height: 52px !important;
    font-size: 14px !important;
}

#video_upload {
    border: 1.5px dashed rgba(255, 107, 26, 0.42) !important;
    border-radius: 18px !important;
    background: rgba(255, 92, 0, 0.035) !important;
    padding: 12px !important;
}

/* ----- Seleção segmentada (Fonte de entrada) ----- */
.fdc-seg .wrap {
    display: flex !important;
    gap: 10px !important;
    flex-wrap: wrap !important;
    background: transparent !important;
}

.fdc-seg label {
    flex: 1 1 0 !important;
    min-width: 0 !important;
    position: relative !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 9px !important;
    padding: 13px 12px !important;
    margin: 0 !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255, 255, 255, 0.09) !important;
    background: rgba(255, 255, 255, 0.025) !important;
    color: #d7c9bd !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    cursor: pointer !important;
    transition: all 0.2s ease;
}

.fdc-seg label::before {
    content: "";
    width: 18px;
    height: 18px;
    flex-shrink: 0;
    background: currentColor;
    -webkit-mask: var(--fdc-seg-ico, none) center / contain no-repeat;
    mask: var(--fdc-seg-ico, none) center / contain no-repeat;
}

.fdc-seg label:hover {
    border-color: rgba(255, 107, 26, 0.42) !important;
    color: #ffffff !important;
}

.fdc-seg label:has(input:checked) {
    background: linear-gradient(135deg, #FF8A2A 0%, #FF5C00 55%, #E04800 100%) !important;
    border-color: transparent !important;
    color: #ffffff !important;
    box-shadow: 0 12px 28px rgba(255, 92, 0, 0.32) !important;
}

.fdc-seg input[type="radio"] {
    position: absolute !important;
    opacity: 0 !important;
    width: 1px !important;
    height: 1px !important;
    margin: 0 !important;
    pointer-events: none !important;
}

/* ----- Chave liga/desliga ----- */
.fdc-switch label {
    display: flex !important;
    flex-direction: row-reverse !important;
    align-items: center !important;
    justify-content: space-between !important;
    gap: 12px !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #f7efe9 !important;
    font-size: 14px !important;
    font-weight: 700 !important;
}

.fdc-switch input[type="checkbox"] {
    -webkit-appearance: none !important;
    appearance: none !important;
    width: 46px !important;
    height: 27px !important;
    min-width: 46px !important;
    margin: 0 !important;
    border-radius: 999px !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    background-color: #2b211b !important;
    background-image: radial-gradient(circle 10px at 14px 13px, #ffffff 96%, transparent 100%) !important;
    background-repeat: no-repeat !important;
    cursor: pointer !important;
    transition: background-color 0.2s ease;
}

.fdc-switch input[type="checkbox"]:checked {
    background-color: #FF5C00 !important;
    background-image: radial-gradient(circle 10px at 32px 13px, #ffffff 96%, transparent 100%) !important;
    border-color: transparent !important;
    box-shadow: 0 6px 18px rgba(255, 92, 0, 0.35);
}

/* ----- Hero ----- */
.fdc-hero {
    position: relative;
    min-height: 176px;
    padding: 30px 34px;
    margin: 2px 0 18px 0;
    border-radius: 26px;
    border: 1px solid rgba(255, 107, 26, 0.2);
    overflow: hidden;
    background:
        radial-gradient(560px 260px at 88% 35%, rgba(255, 92, 0, 0.34), transparent 64%),
        linear-gradient(118deg, #160b06 0%, #241109 46%, #0c0705 100%);
    box-shadow: 0 26px 70px rgba(255, 92, 0, 0.12);
}

.fdc-hero::before {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background: var(--fdc-hero-bg, none) right center / cover no-repeat;
    opacity: 0.6;
    mix-blend-mode: screen;
}

.fdc-hero-title {
    position: relative;
    z-index: 2;
    display: flex;
    align-items: center;
    gap: 14px;
}

.fdc-hero-ico {
    display: flex;
    color: #FF5C00;
    filter: drop-shadow(0 6px 18px rgba(255, 92, 0, 0.45));
}

.fdc-hero h2 {
    margin: 0 !important;
    font-size: 46px !important;
    font-weight: 900 !important;
    letter-spacing: -1.2px !important;
    line-height: 1.02 !important;
    color: #ffffff !important;
}

.fdc-hero h2 span {
    background: linear-gradient(135deg, #FF8A2A 0%, #FF5C00 55%, #E04800 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent !important;
}

.fdc-hero-sub {
    position: relative;
    z-index: 2;
    margin: 10px 0 0 0;
    font-size: 15px;
    color: #cbb9ab;
}

.fdc-pill {
    position: absolute;
    right: 30px;
    top: 26px;
    z-index: 3;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    border-radius: 999px;
    border: 1px solid rgba(255, 107, 26, 0.36);
    background: rgba(12, 7, 4, 0.6);
    color: #FFB27A;
    font-size: 12px;
    font-weight: 800;
}

.fdc-hero-art {
    position: absolute;
    right: 24px;
    top: 50%;
    transform: translateY(-50%);
    z-index: 1;
    height: 210px;
    width: auto;
    object-fit: contain;
    pointer-events: none;
    filter: drop-shadow(0 18px 44px rgba(255, 92, 0, 0.5));
}

/* ----- Como funciona ----- */
.fdc-howto-art {
    position: absolute;
    right: 8px;
    top: 10px;
    opacity: 0.2;
    color: #FF5C00;
    pointer-events: none;
    filter: drop-shadow(0 0 22px rgba(255, 92, 0, 0.45));
}

.fdc-howto-art svg {
    width: 120px;
    height: 120px;
}

.fdc-step {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    margin-top: 14px;
}

.fdc-step .n {
    width: 30px;
    height: 30px;
    flex-shrink: 0;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #FF8A2A 0%, #FF5C00 55%, #E04800 100%);
    color: #ffffff;
    font-size: 13px;
    font-weight: 900;
    box-shadow: 0 8px 18px rgba(255, 92, 0, 0.35);
}

.fdc-step .tx {
    font-size: 13px;
    line-height: 1.45;
    color: #ead9cc;
    padding-top: 4px;
}

.fdc-step .tx b {
    color: #FF8A4C;
}

/* ----- Alerta de licença ----- */
.fdc-alert-wrap {
    margin: 0 0 14px 0 !important;
}

.fdc-alert-wrap textarea {
    min-height: 116px !important;
    resize: vertical !important;
    line-height: 1.5 !important;
}

/* ----- Progresso ----- */
.fdc-progress {
    background: linear-gradient(180deg, rgba(31, 21, 15, 0.92) 0%, rgba(15, 10, 7, 0.95) 100%);
    border: 1px solid rgba(255, 107, 26, 0.16);
    border-radius: 20px;
    padding: 16px 18px;
    box-shadow: 0 14px 40px rgba(0, 0, 0, 0.3);
    margin: 2px 0 14px 0;
}

.fdc-progress-top {
    display: flex;
    align-items: center;
    gap: 12px;
}

.fdc-progress-ico {
    width: 36px;
    height: 36px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #FF8A4C;
    background: rgba(255, 92, 0, 0.12);
    border: 1px solid rgba(255, 92, 0, 0.22);
}

.fdc-progress-label {
    flex: 1;
    font-size: 14px;
    font-weight: 700;
    color: #f1e4d9;
}

.fdc-progress-pct {
    font-size: 15px;
    font-weight: 900;
    color: #FF7A1A;
}

.fdc-progress-track {
    margin-top: 13px;
    height: 7px;
    background: rgba(255, 255, 255, 0.06);
    border-radius: 999px;
    overflow: hidden;
}

.fdc-progress-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(135deg, #FF8A2A 0%, #FF5C00 55%, #E04800 100%);
    box-shadow: 0 0 16px rgba(255, 92, 0, 0.6);
    transition: width 0.45s ease;
}

/* ----- Botão principal (o próprio <button> recebe o id) ----- */
#start_btn {
    width: 100% !important;
    height: 64px !important;
    border: none !important;
    border-radius: 20px !important;
    background: linear-gradient(135deg, #FF8A2A 0%, #FF5C00 55%, #E04800 100%) !important;
    color: #ffffff !important;
    font-size: 17px !important;
    font-weight: 900 !important;
    letter-spacing: 0.3px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 10px !important;
    box-shadow: 0 20px 46px rgba(255, 92, 0, 0.34), inset 0 1px 0 rgba(255, 255, 255, 0.28) !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease !important;
}

#start_btn::before {
    content: "";
    width: 20px;
    height: 20px;
    flex-shrink: 0;
    background: #ffffff;
    -webkit-mask: var(--fdc-start-ico, none) center / contain no-repeat;
    mask: var(--fdc-start-ico, none) center / contain no-repeat;
}

#start_btn:hover:not(:disabled) {
    transform: translateY(-1px);
    filter: brightness(1.06);
    box-shadow: 0 24px 56px rgba(255, 92, 0, 0.42), inset 0 1px 0 rgba(255, 255, 255, 0.28) !important;
}

#start_btn:disabled {
    opacity: 0.42 !important;
    box-shadow: none !important;
    cursor: not-allowed !important;
}

#license_check_btn {
    height: 52px !important;
    border-radius: 16px !important;
    background: linear-gradient(135deg, #FF8A2A 0%, #FF5C00 55%, #E04800 100%) !important;
    color: #ffffff !important;
    font-weight: 900 !important;
    font-size: 15px !important;
    border: none !important;
    box-shadow: 0 16px 36px rgba(255, 92, 0, 0.3) !important;
}

/* ----- Licença ----- */
#license-card {
    max-width: 640px;
    margin: 12px auto 0 auto !important;
}

/* ----- Detalhes técnicos ----- */
.fdc-logs {
    background: linear-gradient(180deg, rgba(31, 21, 15, 0.92) 0%, rgba(15, 10, 7, 0.95) 100%) !important;
    border: 1px solid rgba(255, 107, 26, 0.16) !important;
    border-radius: 18px !important;
    margin-top: 6px !important;
}

/* ----- Biblioteca ----- */
.fdc-lib-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    font-size: 12px;
    font-weight: 700;
    color: #a99a8d;
    margin: 4px 0 0 0;
}

.fdc-lib-project {
    color: #FF8A4C;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 60%;
}

.fdc-lib-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px;
    margin-top: 12px;
}

.fdc-lib-card {
    position: relative;
    background: linear-gradient(180deg, rgba(31, 21, 15, 0.95) 0%, rgba(15, 10, 7, 0.98) 100%);
    border: 1px solid rgba(255, 107, 26, 0.16);
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.32);
}

.fdc-lib-video {
    aspect-ratio: 9 / 16;
    background: #000;
    display: flex;
    align-items: center;
    justify-content: center;
}

.fdc-lib-video video {
    width: 100%;
    height: 100%;
    object-fit: contain;
}

.fdc-lib-body {
    padding: 10px 12px 14px;
}

.fdc-lib-title {
    font-size: 13px;
    font-weight: 700;
    color: #ffffff;
    line-height: 1.35;
}

.fdc-lib-tags {
    font-size: 10px;
    color: #a99a8d;
    margin-top: 4px;
    overflow-wrap: anywhere;
}

.fdc-lib-score {
    position: absolute;
    top: 10px;
    right: 10px;
    background: rgba(255, 92, 0, 0.92);
    color: #ffffff;
    font-weight: 900;
    font-size: 12px;
    padding: 4px 9px;
    border-radius: 999px;
    box-shadow: 0 6px 16px rgba(255, 92, 0, 0.35);
}

.fdc-lib-card {
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.fdc-lib-card:hover {
    transform: translateY(-2px);
    border-color: rgba(255, 107, 26, 0.42);
}

#library-panel .lib-toolbar {
    gap: 10px !important;
    align-items: center !important;
}

#library-panel .lib-main {
    gap: 16px !important;
    align-items: flex-start !important;
}

#library-panel .lib-bottom {
    gap: 16px !important;
    align-items: stretch !important;
}

#lib_pick {
    display: none !important;
}

#library-panel .fdc-card {
    gap: 10px !important;
}

#library-panel .lib-gallery-col {
    min-width: 0 !important;
}

#library-panel .lib-side {
    gap: 10px !important;
    position: sticky;
    top: 12px;
}

#library-panel .lib-side-title {
    font-size: 13px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: 0.2px;
}

#library-panel .lib-colors {
    gap: 14px !important;
}

#library-panel .lib-colors > div {
    flex: 1 1 0 !important;
    min-width: 0 !important;
}

#library-panel .lib-apply-row,
#library-panel .lib-danger-row {
    align-items: center !important;
    gap: 12px !important;
}

#library-panel button:not(.dialog-button) {
    height: 40px !important;
    border-radius: 12px !important;
    font-weight: 800 !important;
    font-size: 13px !important;
    border: 1px solid rgba(255, 107, 26, 0.28) !important;
    background: rgba(255, 92, 0, 0.08) !important;
    color: #FFD2B5 !important;
    box-shadow: none !important;
}

#library-panel button:not(.dialog-button):hover {
    background: rgba(255, 92, 0, 0.16) !important;
}

#library-panel button.primary {
    background: var(--fdc-grad) !important;
    color: #ffffff !important;
    border: none !important;
}

#library-panel button.stop {
    background: rgba(239, 68, 68, 0.14) !important;
    color: #fca5a5 !important;
    border-color: rgba(239, 68, 68, 0.35) !important;
}

#library-panel input[type="range"] {
    accent-color: #FF5C00 !important;
    height: 6px !important;
    cursor: pointer !important;
}

#library-panel input[type="color"] {
    width: 100% !important;
    height: 46px !important;
    padding: 4px !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    background: #0c0908 !important;
    cursor: pointer !important;
}

#library-panel button.dialog-button {
    width: 100% !important;
    height: 46px !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.16) !important;
    box-shadow: inset 0 0 0 2px rgba(0, 0, 0, 0.35), 0 6px 18px rgba(0, 0, 0, 0.25) !important;
    cursor: pointer !important;
}

#lib_project,
#lib_cut {
    background: #0c0908 !important;
    border: 1px solid rgba(255, 255, 255, 0.10) !important;
    border-radius: 14px !important;
    padding: 4px 12px !important;
}

#library-panel .form,
#library-panel .wrap {
    background: transparent !important;
}

#library-panel audio {
    width: 100% !important;
    height: 38px !important;
    filter: invert(0.92) hue-rotate(180deg) !important;
    border-radius: 10px !important;
}

#lib_video video,
#library-panel video {
    border-radius: 14px !important;
    background: #000 !important;
}

#library-panel .lib-player-wrap {
    background: #000 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 16px !important;
    overflow: hidden !important;
    box-shadow: 0 14px 34px rgba(0, 0, 0, 0.35) !important;
}

#library-panel .lib-player {
    width: 100% !important;
    max-height: 430px !important;
    display: block !important;
    background: #000 !important;
}

#lib_preview .lib-player {
    max-height: 300px !important;
}

#library-panel .lib-side-title {
    text-transform: uppercase !important;
    letter-spacing: 0.7px !important;
    font-size: 11px !important;
    color: #a99a8d !important;
}

/* Itens técnicos ocultos para o cliente (continuam no código) */
#advanced-face,
#subtitle-settings {
    display: none !important;
}
"""

import header
import ui_assets
import ui_icons
from html import escape as _esc
import license_gate
import license_client

# License gate (best default)
_LICENSE_SERVER = os.environ.get('FORJA_LICENSE_SERVER', 'https://forja-license-production.up.railway.app').rstrip('/')
_gate = license_gate.LicenseGate(base_url=_LICENSE_SERVER, app_version='1.0.0')

# ---------------------------
# Credits Topbar (client UI)
# Put a PNG at: webui/assets/credits.png  (you can replace it anytime)
# ---------------------------
def _credits_icon_html() -> str:
    try:
        import base64
        from pathlib import Path
        icon_path = Path(__file__).resolve().parent / "assets" / "credits.png"
        if icon_path.exists():
            b64 = base64.b64encode(icon_path.read_bytes()).decode("ascii")
            return f'<img src="data:image/png;base64,{b64}" style="width:18px;height:18px;vertical-align:middle;" />'
    except Exception:
        pass
    return '<span style="font-size:18px;line-height:1;">⚡</span>'


def _fmt_exp_ts(ts: int) -> str:
    try:
        if not ts:
            return "-"
        return time.strftime("%d/%m/%Y %H:%M", time.localtime(int(ts)))
    except Exception:
        return str(ts)


def _render_topbar_html() -> str:
    st = getattr(_gate, "state", None)
    ok = bool(getattr(st, "ok", False))
    credits = int(getattr(st, "credits", 0) or 0)
    exp = int(getattr(st, "exp", 0) or 0)
    reason = str(getattr(st, "reason", "") or "")

    status = "Ativo" if ok else "Bloqueado"
    exp_txt = _fmt_exp_ts(exp)

    # client-friendly reason
    if ok:
        sub = f"Expira em {exp_txt}"
        status_class = "ok"
    else:
        if reason == "expired":
            sub = "Licença expirada"
        elif reason == "no_credits":
            sub = "Sem créditos"
        elif reason == "hwid_mismatch":
            sub = "Ativada em outro PC"
        elif reason == "not_found":
            sub = "Chave não encontrada"
        else:
            sub = "Ativação necessária"
        status_class = "bad"

    icon = _credits_icon_html()

    return f"""
    <div class="fv-topbar">
      <div class="fv-topbar-left">
        <div class="fv-credits">{icon}<span>{credits} créditos</span></div>
        <div class="fv-sub">{sub}</div>
      </div>
      <div class="fv-status {status_class}">{status}</div>
    </div>
    """



def _app_version() -> str:
    try:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, "version.json"), "r", encoding="utf-8-sig") as fh:
            return str(json.load(fh).get("version") or "")
    except Exception:
        return ""


def _render_progress_html(percent: int, label: str) -> str:
    """Barra de progresso do app: ícone, rótulo, percentual e trilha laranja."""
    pct = max(0, min(100, int(percent)))
    return (
        '<div class="fdc-progress">'
        '<div class="fdc-progress-top">'
        f'<span class="fdc-progress-ico">{ui_icons.svg("rocket", 18)}</span>'
        f'<span class="fdc-progress-label">{_esc(str(label or ""))}</span>'
        f'<span class="fdc-progress-pct">{pct}%</span>'
        "</div>"
        f'<div class="fdc-progress-track"><div class="fdc-progress-fill" style="width:{pct}%"></div></div>'
        "</div>"
    )


def _card_head(icon: str, title: str, desc: str = "", desc_html: str = "") -> str:
    text = desc_html or _esc(desc)
    sub = f'<div class="s">{text}</div>' if text else ""
    return (
        '<div class="fdc-head">'
        f'<span class="ico">{ui_icons.svg(icon, 19)}</span>'
        f'<div><div class="t">{_esc(title)}</div>{sub}</div>'
        "</div>"
    )


def _license_head_html() -> str:
    return (
        '<div class="fdc-head fdc-head-lg">'
        f'<span class="ico">{ui_icons.svg("key-round", 22)}</span>'
        '<div><div class="t">Ativar licença</div>'
        '<div class="s">Cole a chave que chegou no seu e-mail de compra para liberar seus créditos.</div></div>'
        "</div>"
    )


def _hero_html() -> str:
    art = ui_assets.data_uri("hero_logo.webp")
    art_html = f'<img class="fdc-hero-art" src="{art}" alt="" />' if art else ""
    return (
        '<div class="fdc-hero">'
        '<div class="fdc-hero-title">'
        f'<span class="fdc-hero-ico">{ui_icons.svg("scissors", 38, 1.9)}</span>'
        "<h2>Criar <span>Cortes</span></h2>"
        "</div>"
        '<p class="fdc-hero-sub">Transforme seus vídeos em cortes virais com poucos cliques.</p>'
        f'<div class="fdc-pill">{ui_icons.svg("zap", 14)}<span>Rápido. Inteligente. Profissional.</span></div>'
        f"{art_html}"
        "</div>"
    )


def _howto_html() -> str:
    steps = [
        "Cole o link do vídeo ou envie um arquivo.",
        "Escolha quantos cortes quer e a duração.",
        "Clique em <b>Gerar Cortes</b> e acompanhe a barra de progresso.",
    ]
    items = "".join(
        f'<div class="fdc-step"><span class="n">{number}</span><div class="tx">{text}</div></div>'
        for number, text in enumerate(steps, 1)
    )
    art = f'<div class="fdc-howto-art">{ui_icons.svg("film", 120, 1.2)}</div>'
    return art + _card_head("lightbulb", "Como funciona", "Do link ao corte pronto em 3 passos") + items


def _rail_html() -> str:
    logo = ui_assets.data_uri("logo_rail.webp") or ui_assets.data_uri("logo.png")
    logo_html = f'<img src="{logo}" alt="Fábrica dos Cortes" />' if logo else ""
    items = [
        ("scissors", "Criar Cortes", True),
        ("layout-grid", i18n("Library"), False),
        ("key-round", "Licença", False),
    ]
    buttons = []
    for icon, label, active in items:
        safe = _esc(label, quote=True)
        classes = "fdc-rail-item active" if active else "fdc-rail-item"
        buttons.append(
            f'<button type="button" class="{classes}" data-goto="{safe}" title="{safe}" aria-label="{safe}">'
            f"{ui_icons.svg(icon, 22, 1.9)}</button>"
        )
    return (
        '<div class="fdc-rail">'
        f'<div class="fdc-rail-logo">{logo_html}</div>'
        + "".join(buttons)
        + f'<div class="fdc-rail-foot">v{_app_version()}</div>'
        + "</div>"
    )


def _dynamic_css() -> str:
    rules = []
    hero_bg = ui_assets.data_uri("bg_streaks.webp")
    if hero_bg:
        rules.append(f':root {{ --fdc-hero-bg: url("{hero_bg}"); }}')
    for index, icon in enumerate(["key-round", "scissors", "layout-grid"], 1):
        rules.append(f".tab-container button:nth-child({index}) {{ --fdc-ico: {ui_icons.mask_uri(icon)}; }}")
    for index, icon in enumerate(["youtube", "folder-open", "upload"], 1):
        rules.append(f".fdc-seg label:nth-child({index}) {{ --fdc-seg-ico: {ui_icons.mask_uri(icon)}; }}")
    rules.append(f"#start_btn {{ --fdc-start-ico: {ui_icons.mask_uri('zap')}; }}")
    link_icon = ui_icons.color_uri("link", "#FF8A4C")
    if link_icon:
        rules.append(
            f"#url_input textarea, #url_input input {{ background-image: {link_icon} !important; "
            "background-repeat: no-repeat; background-position: 16px center; background-size: 18px 18px; }"
        )
    return "\n".join(rules)


def _render_blocked_banner() -> tuple[str, bool]:
    st = getattr(_gate, "state", None)
    ok = bool(getattr(st, "ok", False))
    reason = str(getattr(st, "reason", "") or "")
    exp = int(getattr(st, "exp", 0) or 0)
    credits = int(getattr(st, "credits", 0) or 0)
    lk = str(getattr(_gate, "license_key", "") or "").strip()

    if ok:
        return ("", False)

    title = "Ativação necessária"
    msg = "Para gerar e exportar, ative sua licença."
    if reason == "expired":
        title = "Licença expirada"
        msg = "Sua licença expirou. Renove para continuar gerando."
    elif reason == "no_credits":
        title = "Sem créditos"
        msg = "Você ficou sem créditos. Recarregue para continuar."
    elif reason == "hwid_mismatch":
        title = "Ativada em outro PC"
        msg = "Essa chave já está vinculada a outro computador."
    elif reason == "not_found":
        title = "Chave não encontrada"
        msg = "Confira a chave e tente novamente."
    elif reason == "server_error":
        title = "Servidor indisponível"
        msg = "Não foi possível validar agora. Verifique sua internet e tente novamente."

    support_msg = (
        "Olá! Quero renovar minha licença da Fábrica dos Cortes (fabricadecortes.com).\n"
        f"Chave: {lk or '[sua-chave]'}\n"
        f"Motivo: {reason}\n"
        f"Créditos: {credits}\n"
        f"Exp: {_fmt_exp_ts(exp)}"
    )

    # Safe embed in HTML
    safe_support = (
        support_msg.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    html_block = f"""
    <div style="border:1px solid rgba(255,255,255,.10); background: rgba(0,0,0,.18); border-radius: 16px; padding: 14px 14px; margin: 10px 0 14px 0;">
      <div style="font-weight:900; font-size:14px; margin-bottom:6px;">⛔ {title}</div>
      <div style="color:rgba(255,255,255,.78); font-size:13px; margin-bottom:10px;">{msg}</div>
      <div style="font-size:12px; color:rgba(255,255,255,.70); margin-bottom:6px;">Mensagem para renovar (copie e envie)</div>
      <textarea readonly style="width:100%; min-height: 72px; resize: vertical; border-radius: 12px; padding: 10px 10px;
        border:1px solid rgba(255,255,255,.10); background: rgba(255,255,255,.04); color: rgba(255,255,255,.90); font-size: 12px;">{safe_support}</textarea>
    </div>
    """
    return (html_block, True)

_gate.load_local()
_gate.check_on_start()


css = css + _dynamic_css()

with gr.Blocks(title="Fábrica dos Cortes", theme=gr.themes.Default(primary_hue="orange", neutral_hue="slate"), css=css) as demo:
    gr.HTML(_rail_html(), elem_id="fdc-rail")
    with gr.Row(elem_id="fdc-topbar"):
        with gr.Column(scale=6, min_width=260):
            topbar_html = gr.HTML(value=_render_topbar_html(), elem_classes="fdc-bare")
        with gr.Column(scale=1, min_width=170):
            topbar_refresh = gr.Button(i18n('Atualizar créditos'), variant='secondary', size="sm", elem_id="refresh_credits")
    if hasattr(gr, 'Timer'):
        _t = gr.Timer(12)
        _t.tick(fn=lambda: (_gate.check_now(), _render_topbar_html())[1], inputs=[], outputs=[topbar_html])
    with gr.Tabs():
        with gr.Tab("Licença"):
            with gr.Column(elem_classes="fdc-card", elem_id="license-card"):
                gr.HTML(_license_head_html(), elem_classes="fdc-bare")
                _gate.ui_block()
        with gr.Tab("Criar Cortes"):
             _banner_html, _banner_visible = _render_blocked_banner()
             blocked_banner = gr.HTML(value=_banner_html, visible=_banner_visible, elem_classes="fdc-bare fdc-alert-wrap")
             gr.HTML(_hero_html(), elem_classes="fdc-bare")
             with gr.Row(equal_height=True):
                 with gr.Column(scale=3, elem_classes="fdc-card"):
                     gr.HTML(_card_head("link", "Fonte de entrada", "Cole o link do YouTube, use um projeto salvo ou envie um vídeo"))
                     input_source = gr.Radio(
                         [(i18n("YouTube URL"), "YouTube URL"), (i18n("Existing Project"), "Existing Project"), ("Usar Vídeo", "Upload Video")],
                         value="YouTube URL",
                         show_label=False,
                         container=False,
                         elem_classes="fdc-seg",
                     )
                     url_input = gr.Textbox(show_label=False, container=False, placeholder="https://www.youtube.com/watch?v=...", visible=True, elem_id="url_input")
                     video_upload = gr.File(show_label=False, file_count="single", file_types=["video"], visible=False, elem_id="video_upload")
                     project_selector = gr.Dropdown(choices=[], show_label=False, container=False, visible=False)
                 with gr.Column(scale=2, elem_classes="fdc-card fdc-howto"):
                     gr.HTML(_howto_html())
             with gr.Row(equal_height=True):
                 with gr.Column(min_width=160, elem_classes="fdc-card"):
                     gr.HTML(_card_head("key", "Chave API Gemini", desc_html='Grátis em <a href="https://aistudio.google.com" target="_blank">aistudio.google.com</a>'))
                     api_key_input = gr.Textbox(type="password", value=get_saved_gemini_key(), placeholder="Cole sua chave (AIza...)", show_label=False, container=False)
                 with gr.Column(min_width=160, elem_classes="fdc-card"):
                     gr.HTML(_card_head("sliders-horizontal", "Qualidade", "720p é o mais rápido e ideal para celular"))
                     video_quality_input = gr.Dropdown(
                         choices=[("720p (Ultra Rápido)", "720p"), ("1080p (Alta Definição)", "1080p"), ("480p (Super Leve)", "480p"), ("Melhor Disponível", "best"), ("4K Ultra HD", "4k")],
                         value="720p",
                         show_label=False,
                         container=False,
                     )
                 with gr.Column(min_width=160, elem_classes="fdc-card"):
                     gr.HTML(_card_head("languages", "Traduzir legendas", "Opcional, para outro idioma"))
                     translate_input = gr.Dropdown(choices=["None", "pt", "en", "es", "fr", "de", "it", "ru", "ja", "ko", "zh-CN"], value="None", show_label=False, container=False)
                 with gr.Column(min_width=160, elem_classes="fdc-card"):
                     gr.HTML(_card_head("youtube", "Legendas oficiais", "Mais rápido quando o YouTube já tem"))
                     use_youtube_subs_input = gr.Checkbox(label="Usar legendas do YouTube", value=True, elem_classes="fdc-switch")
             with gr.Row(equal_height=True):
                 with gr.Column(min_width=160, elem_classes="fdc-card"):
                     gr.HTML(_card_head("scissors", "Cortes", "Quantos vídeos gerar"))
                     segments_input = gr.Number(value=3, precision=0, show_label=False, container=False)
                 with gr.Column(min_width=160, elem_classes="fdc-card"):
                     gr.HTML(_card_head("timer", "Duração mínima", "Em segundos"))
                     min_dur_input = gr.Number(value=15, show_label=False, container=False)
                 with gr.Column(min_width=160, elem_classes="fdc-card"):
                     gr.HTML(_card_head("clock", "Duração máxima", "Em segundos"))
                     max_dur_input = gr.Number(value=90, show_label=False, container=False)
             viral_input = gr.Checkbox(value=True, visible=False)
             themes_input = gr.Textbox(visible=False)
             ai_backend_input = gr.Dropdown(choices=[(i18n("Gemini"), "gemini")], value="gemini", visible=False)
             ai_model_input = gr.Dropdown(choices=GEMINI_MODELS, label=i18n("AI Model"), value=GEMINI_MODELS[0], allow_custom_value=True, visible=False)
             chunk_size_input = gr.Number(label=i18n("Chunk Size"), value=250000, precision=0, visible=False)
             model_input = gr.Dropdown(["tiny", "small", "medium", "large", "large-v1", "large-v2", "large-v3", "turbo", "large-v3-turbo", "distil-large-v2", "distil-medium.en", "distil-small.en", "distil-large-v3"], label=i18n("Whisper Model"), value="large-v3-turbo", visible=False)
             workflow_input = gr.Dropdown(choices=[(i18n("Full"), "Full"), (i18n("Cut Only"), "Cut Only"), (i18n("Subtitles Only"), "Subtitles Only")], label=i18n("Workflow"), value="Full", visible=False)
             face_model_input = gr.Dropdown(["insightface", "mediapipe"], label=i18n("Face Model"), value="insightface", visible=False)
             face_mode_input = gr.Dropdown(choices=[(i18n("Auto"), "auto"), ("1", "1"), ("2", "2")], label=i18n("Face Mode"), value="auto", visible=False)
             face_detect_interval_input = gr.Textbox(label=i18n("Face Det. Interval"), value="0.17,1.0", visible=False)
             no_face_mode_input = gr.Dropdown(choices=[(i18n("Padding (9:16)"), "padding"), (i18n("Zoom (Center)"), "zoom")], label=i18n("No Face Fallback"), value="zoom", visible=False)

             def on_source_change(source):
                 if source == "YouTube URL":
                     return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(value="Full")
                 elif source == "Upload Video":
                     return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(value="Full")
                 projs = library.get_existing_projects()
                 return gr.update(visible=False), gr.update(choices=projs, visible=True), gr.update(visible=False), gr.update(value="Subtitles Only")

             input_source.change(on_source_change, inputs=input_source, outputs=[url_input, project_selector, video_upload, workflow_input])
             with gr.Accordion(i18n("Advanced Face Settings"), open=False, elem_id="advanced-face"):
                 face_preset_input = gr.Dropdown(choices=[(i18n(k), k) for k in FACE_PRESETS.keys()], label=i18n("Configuration Presets"), value="Default (Balanced)", interactive=True)
                 with gr.Row():
                      face_filter_thresh_input = gr.Slider(label=i18n("Ignore Small Faces (0.0 - 1.0)"), minimum=0.0, maximum=1.0, value=0.35, step=0.05, info=i18n("Relative size to ignore background."))
                      face_two_thresh_input = gr.Slider(label=i18n("Threshold for 2 Faces (0.0 - 1.0)"), minimum=0.0, maximum=1.0, value=0.60, step=0.05, info=i18n("Size of 2nd face to activate split mode."))
                      face_conf_thresh_input = gr.Slider(label=i18n("Minimum Confidence (0.0 - 1.0)"), minimum=0.0, maximum=1.0, value=0.40, step=0.05, info=i18n("Ignore detections with low confidence."))
                      face_dead_zone_input = gr.Slider(label=i18n("Dead Zone (Stabilization)"), minimum=0, maximum=200, value=150, step=5, info=i18n("Movement pixels to ignore."))
                 
                 face_preset_input.change(apply_face_preset, inputs=face_preset_input, outputs=[face_filter_thresh_input, face_two_thresh_input, face_conf_thresh_input, face_dead_zone_input])

                 with gr.Accordion(i18n("Experimental: Active Speaker & Motion"), open=False):
                        experimental_preset_input = gr.Dropdown(choices=[(i18n(k), k) for k in EXPERIMENTAL_PRESETS.keys()], label=i18n("Configuration Presets"), value="Default (Off)", interactive=True)
                        focus_active_speaker_input = gr.Checkbox(label=i18n("Experimental: Focus on Speaker"), value=False, info=i18n("Tries to focus only on the speaking person instead of split screen."))
                        with gr.Row():
                            active_speaker_mar_input = gr.Slider(label=i18n("MAR Threshold (Mouth Open)"), minimum=0.01, maximum=0.20, value=0.03, step=0.005, info=i18n("Mouth open sensitivity."))
                            active_speaker_score_diff_input = gr.Slider(label=i18n("Score Difference"), minimum=0.5, maximum=10.0, value=1.5, step=0.5, info=i18n("Minimum difference to focus on 1 face."))
                            
                        with gr.Row():
                            include_motion_input = gr.Checkbox(label=i18n("Consider Motion"), value=False, info=i18n("Increases score with motion (gestures)."))
                            
                        with gr.Row():
                            active_speaker_motion_threshold_input = gr.Slider(label=i18n("Motion Dead Zone"), minimum=0.0, maximum=20.0, value=3.0, step=0.5, info=i18n("Pixels ignored."))
                            active_speaker_motion_sensitivity_input = gr.Slider(label=i18n("Motion Sensitivity"), minimum=0.01, maximum=0.5, value=0.05, step=0.01, info=i18n("Points per pixel."))
                            active_speaker_decay_input = gr.Slider(label=i18n("Switch Speed"), minimum=0.5, maximum=5.0, value=2.0, step=0.5, info=i18n("Speed to lose focus."))

                        experimental_preset_input.change(apply_experimental_preset, inputs=experimental_preset_input, outputs=[focus_active_speaker_input, active_speaker_mar_input, active_speaker_score_diff_input, include_motion_input, active_speaker_motion_threshold_input, active_speaker_motion_sensitivity_input, active_speaker_decay_input])
             with gr.Accordion(i18n("Subtitle Settings (alpha)"), open=False, elem_id="subtitle-settings"):
                preset_input = gr.Dropdown(choices=[(i18n("Manual"), "Manual")] + [(i18n(k), k) for k in subs.SUBTITLE_PRESETS.keys()], label=i18n("Quick Presets"), value="Hormozi (Classic)")
                use_custom_subs = gr.Checkbox(label=i18n("Enable Subtitle Customization (Includes Preset)"), value=True)
                
                # Previews (Always Visible)
                preview_html = gr.HTML(value=f"<div style='text-align:center; padding:10px; color:#666;'>{i18n('Select options or preset to preview')}</div>")
                
                with gr.Row():
                    preview_vid_btn = gr.Button(i18n("🎬 Render Animated Preview (Slow)"), size="sm")
                preview_vid = gr.Video(label=i18n("Animated Preview"), height=300, autoplay=True, interactive=False)
                
                with gr.Accordion(i18n("Advanced Settings"), open=False):
                    gr.Markdown(f"### {i18n('Appearance')}")
                    with gr.Row():
                        font_name_input = gr.Textbox(label=i18n("Font Name"), value="Montserrat-Regular")
                        font_size_input = gr.Slider(label=i18n("Font Size (Base)"), minimum=8, maximum=80, value=12)
                        highlight_size_input = gr.Slider(label=i18n("Highlight Size"), minimum=8, maximum=80, value=14)
                    
                    with gr.Row():
                        font_color_input = gr.ColorPicker(label=i18n("Base Color"), value="#FFFFFF")
                        highlight_color_input = gr.ColorPicker(label=i18n("Highlight Color"), value="#00FF00")
                        outline_color_input = gr.ColorPicker(label=i18n("Outline Color"), value="#000000")
                        shadow_color_input = gr.ColorPicker(label=i18n("Shadow Color"), value="#000000")
                    
                    gr.Markdown(f"### {i18n('Styling & Effects')}")
                    with gr.Row():
                        outline_thickness_input = gr.Slider(label=i18n("Outline Thickness"), minimum=0, maximum=10, value=1.5)
                        shadow_size_input = gr.Slider(label=i18n("Shadow Size"), minimum=0, maximum=10, value=2)
                        border_style_input = gr.Dropdown(choices=[(i18n("Outline"), 1), (i18n("Opaque Box"), 3)], label=i18n("Border Style"), value=1)
                    
                    with gr.Row():
                        bold_input = gr.Checkbox(label=i18n("Bold"))
                        italic_input = gr.Checkbox(label=i18n("Italic"))
                        uppercase_input = gr.Checkbox(label=i18n("Uppercase"))
                        remove_punc_input = gr.Checkbox(label=i18n("Remove Punctuation"), value=True)
                        underline_input = gr.Checkbox(label=i18n("Underline"))
                        strikeout_input = gr.Checkbox(label=i18n("Strikeout"))
                        
                    gr.Markdown(f"### {i18n('Positioning & Layout')}")
                    with gr.Row():
                        vertical_pos_input = gr.Slider(label=i18n("V-Pos (Margin V)"), minimum=0, maximum=500, value=210)
                        alignment_input = gr.Dropdown(choices=[(i18n("Left"), 1), (i18n("Center"), 2), (i18n("Right"), 3)], label=i18n("Alignment"), value=2)
                        gap_limit_input = gr.Slider(label=i18n("Gap Limit"), minimum=0.0, maximum=5.0, value=0.5, step=0.1)
                        mode_input = gr.Dropdown(choices=[(i18n("Highlight"), "highlight"), (i18n("Word by Word"), "word_by_word"), (i18n("No Highlight"), "no_highlight")], label=i18n("Mode"), value="highlight")
                        words_per_block_input = gr.Slider(label=i18n("Words per Block"), minimum=1, maximum=20, value=3, step=1)

                manual_inputs = [
                    font_name_input, font_size_input, font_color_input, highlight_color_input, 
                    outline_color_input, outline_thickness_input, shadow_color_input, shadow_size_input, 
                    bold_input, italic_input, uppercase_input,
                    highlight_size_input, words_per_block_input, gap_limit_input, mode_input,
                    underline_input, strikeout_input, border_style_input,
                    vertical_pos_input, alignment_input,
                    remove_punc_input
                ]
                
                # Update manual inputs when preset changes
                preset_input.change(subs.apply_preset, inputs=[preset_input], outputs=manual_inputs)
                
                # Auto-update PREVIEW HTML on any change
                for inp in manual_inputs:
                    inp.change(subs.generate_preview_html, inputs=manual_inputs, outputs=preview_html)
                
                # Render video button
                preview_vid_btn.click(
                    subs.render_preview_video,
                    inputs=manual_inputs,
                    outputs=preview_vid
                )
                
                # Initial load
                demo.load(subs.generate_preview_html, inputs=manual_inputs, outputs=preview_html)
                demo.load(subs.apply_preset, inputs=[preset_input], outputs=manual_inputs) # Apply default preset on load

             progress_html = gr.HTML(value=_render_progress_html(0, "Pronto para gerar"), elem_id="progress_panel")
             with gr.Row():
                 start_btn = gr.Button("Gerar Cortes", variant="primary", interactive=bool(getattr(getattr(_gate,"state",None),"ok",False)), elem_id="start_btn", scale=4)
                 stop_btn = gr.Button("Parar", variant="stop", visible=False, scale=1)
             stop_btn.click(kill_process, outputs=[])
             def _sync_license_ui():
                 _gate.check_now()
                 html_block, vis = _render_blocked_banner()
                 ok = bool(getattr(getattr(_gate,"state",None),"ok",False))
                 return (
                     _render_topbar_html(),
                     gr.update(value=html_block, visible=vis),
                     gr.update(interactive=ok),
                 )

             # Atualiza topo + bloqueio + botão principal
             topbar_refresh.click(fn=_sync_license_ui, inputs=[], outputs=[topbar_html, blocked_banner, start_btn])

             results_html = gr.HTML(label="Resultados", elem_classes="fdc-results")
             with gr.Accordion("Detalhes técnicos", open=False, elem_classes="fdc-logs"):
                 logs_output = gr.Textbox(label="Logs", lines=8, autoscroll=True, elem_id="logs_output")
             
             # Force scroll to bottom via JS
             logs_output.change(fn=None, inputs=[], outputs=[], js="""
                function() {
                    var ta = document.querySelector('#logs_output textarea');
                    if(ta) {
                        // Setup scroll listener once to track user intent
                        if (!ta._scrollerSetup) {
                            ta._isSticky = true; // Default to sticky
                            ta.addEventListener('scroll', function() {
                                var diff = ta.scrollHeight - ta.scrollTop - ta.clientHeight;
                                // If near bottom (<50px), enable sticky. Else disable.
                                if (diff <= 50) {
                                     ta._isSticky = true;
                                } else {
                                     ta._isSticky = false;
                                }
                            });
                            ta._scrollerSetup = true;
                        }
                        
                        // Apply scroll only if sticky
                        if(ta._isSticky === undefined || ta._isSticky === true) {
                            ta.scrollTop = ta.scrollHeight;
                        }
                    }
                }
             """)
             
             # MUST pass all all new inputs to the run function
             start_btn.click(
                 _gate.require_precheck_and_prepay(
                     run_viral_cutter,
                     lambda args, kwargs: int(args[4] or 1)
                 ),
                 inputs=[

                 input_source, project_selector, url_input, video_upload, segments_input, viral_input, themes_input, min_dur_input, max_dur_input, 
                 model_input, ai_backend_input, api_key_input, ai_model_input, chunk_size_input, 
                 workflow_input, face_model_input, face_mode_input, face_detect_interval_input, no_face_mode_input, 
                 face_filter_thresh_input, face_two_thresh_input, face_conf_thresh_input, face_dead_zone_input, focus_active_speaker_input, 
                 active_speaker_mar_input, active_speaker_score_diff_input, include_motion_input, active_speaker_motion_threshold_input, active_speaker_motion_sensitivity_input, active_speaker_decay_input,
                 use_custom_subs, 
                 # Expanded Manual Inputs mapping
                 font_name_input, font_size_input, font_color_input, highlight_color_input, 
                 outline_color_input, outline_thickness_input, shadow_color_input, shadow_size_input, 
                 bold_input, italic_input, uppercase_input, vertical_pos_input, alignment_input,
                 # New Inputs
                 highlight_size_input, words_per_block_input, gap_limit_input, mode_input, 
                 underline_input, strikeout_input, border_style_input, remove_punc_input,
                 video_quality_input, use_youtube_subs_input, translate_input
             ], outputs=[logs_output, start_btn, stop_btn, results_html, topbar_html, progress_html])

        with gr.Tab(i18n("Library")):
            _lib_projects = studio.list_projects()
            _lib_first = _lib_projects[0] if _lib_projects else None
            _lib_cuts = studio.cuts(_lib_first) if _lib_first else []
            _lib_first_base = _lib_cuts[0]["base"] if _lib_cuts else None
            _lib_first_video = _lib_cuts[0]["video"] if _lib_cuts else None
            _lib_tracks = studio.music_choices()
            _lib_first_track = _lib_tracks[0][1] if _lib_tracks else None
            with gr.Column(elem_id="library-panel"):
                gr.HTML(_card_head("layout-grid", i18n("Library"), "Seus cortes prontos: legenda, música, thumbnails e download"))
                with gr.Row(elem_classes="lib-toolbar"):
                    lib_project = gr.Dropdown(choices=_lib_projects, value=_lib_first, show_label=False, container=False, scale=5, elem_id="lib_project")
                    lib_refresh = gr.Button("Atualizar", size="sm", scale=1)
                    lib_thumbs = gr.Button("Thumbnails", size="sm", scale=1)
                    lib_zip = gr.Button("Baixar ZIP", size="sm", scale=1)
                with gr.Row(equal_height=False, elem_classes="lib-main"):
                    with gr.Column(scale=3, elem_classes="fdc-card lib-gallery-col"):
                        lib_gallery = gr.HTML(studio.gallery_html(_lib_first) if _lib_first else studio.gallery_html(""))
                    with gr.Column(scale=2, elem_classes="fdc-card lib-side"):
                        gr.HTML('<div class="lib-side-title">Corte selecionado</div>')
                        lib_video = gr.HTML(value=studio.video_html(_lib_first_video) if _lib_first_video else "", elem_id="lib_video")
                        lib_cut = gr.Dropdown(
                            choices=[(c["label"], c["base"]) for c in _lib_cuts],
                            value=_lib_first_base,
                            show_label=False,
                            container=False,
                            elem_id="lib_cut",
                        )
                        with gr.Row():
                            lib_approve = gr.Button("Aprovar", size="sm")
                            lib_reject = gr.Button("Reprovar", size="sm")
                        with gr.Row():
                            lib_new_title = gr.Textbox(placeholder="Novo título do corte", show_label=False, container=False, scale=3)
                            lib_rename_btn = gr.Button("Renomear", size="sm", scale=1)
                        lib_status = gr.Markdown("")
                with gr.Row(equal_height=False, elem_classes="lib-bottom"):
                    with gr.Column(scale=3, elem_classes="fdc-card"):
                        gr.HTML(_card_head("captions", "Editar legenda", "Fonte, cores e posição — aplica sem recortar de novo"))
                        lib_preset = gr.Dropdown(choices=list(subs.SUBTITLE_PRESETS.keys()), value="Hormozi (Classic)", show_label=False, container=False)
                        with gr.Row():
                            lib_font = gr.Textbox(value="Montserrat-ExtraBold", label="Fonte")
                            lib_size = gr.Slider(16, 60, value=30, step=1, label="Tamanho")
                        with gr.Row():
                            lib_hl_size = gr.Slider(16, 70, value=35, step=1, label="Destaque")
                            lib_pos = gr.Slider(0, 500, value=200, step=5, label="Posição vertical")
                        with gr.Row(elem_classes="lib-colors"):
                            lib_color = gr.ColorPicker(value="#FFFFFF", label="Cor base")
                            lib_hl_color = gr.ColorPicker(value="#00FF00", label="Cor destaque")
                            lib_outline = gr.ColorPicker(value="#000000", label="Contorno")
                        with gr.Row():
                            lib_mode = gr.Dropdown(choices=[("Destacar", "highlight"), ("Palavra a palavra", "word_by_word"), ("Sem destaque", "no_highlight")], value="highlight", label="Modo")
                            lib_upper = gr.Checkbox(value=True, label="Maiúsculas")
                        with gr.Row(elem_classes="lib-apply-row"):
                            lib_apply_all = gr.Checkbox(label="Aplicar em todos os cortes", value=False, scale=3)
                            lib_apply_btn = gr.Button("Aplicar legenda", variant="primary", scale=2)
                    with gr.Column(scale=2, elem_classes="fdc-card"):
                        gr.HTML(_card_head("play", "Música", "Ouça a faixa, teste 30s com o vídeo e aplique com ducking"))
                        with gr.Row():
                            lib_track = gr.Dropdown(choices=_lib_tracks, value=_lib_first_track, show_label=False, container=False, scale=4, info="Envie uma música ou coloque arquivos na pasta music/")
                            lib_track_refresh = gr.Button("Atualizar lista", size="sm", scale=1)
                        lib_track_audio = gr.Audio(label="Ouvir a música", value=_lib_first_track, interactive=False)
                        with gr.Row():
                            lib_vol = gr.Slider(0, 100, value=18, step=1, label="Volume (%)")
                            lib_duck = gr.Checkbox(value=True, label="Abaixar na voz")
                        with gr.Row(elem_classes="lib-apply-row"):
                            lib_preview_btn = gr.Button("Prévia com música (30s)", size="sm", scale=1)
                            lib_apply_music_btn = gr.Button("Aplicar música", variant="primary", scale=1)
                        lib_preview_video = gr.HTML(value="", visible=False, elem_id="lib_preview")
                        lib_music_upload = gr.File(label="Enviar música (mp3, wav, m4a)", file_types=["audio"], type="filepath")
                with gr.Row(equal_height=False, elem_classes="lib-bottom"):
                    with gr.Column(scale=2, elem_classes="fdc-card"):
                        gr.HTML(_card_head("info", "Metadados", "Título, descrição e hashtags prontos para o YouTube"))
                        lib_meta_btn = gr.Button("Carregar metadados do corte", size="sm")
                        lib_title = gr.Textbox(label="Título")
                        lib_desc = gr.Textbox(label="Descrição", lines=4)
                        lib_tags = gr.Textbox(label="Hashtags")
                    with gr.Column(scale=1, elem_classes="fdc-card"):
                        gr.HTML(_card_head("circle-alert", "Zona de risco", "Apagar corte ou projeto"))
                        lib_delete_cut_btn = gr.Button("Apagar corte", variant="stop", size="sm")
                        lib_confirm_delete = gr.Checkbox(label="Confirmo apagar o projeto", value=False)
                        lib_delete_project_btn = gr.Button("Apagar projeto", variant="stop", size="sm")
                lib_pick = gr.Textbox(value="", show_label=False, container=False, elem_id="lib_pick", visible=True)
                lib_zip_file = gr.File(label="Download do ZIP", visible=False)

            def _lib_meta(project, base):
                meta = studio.metadata(project, base) if project and base else {"title": "", "description": "", "hashtags": ""}
                return meta["title"], meta["description"], meta["hashtags"]

            def _lib_selection(project, base):
                entry = studio._cut_by_base(project, base) if project and base else None
                video = entry["video"] if entry else None
                title, desc, tags = _lib_meta(project, base)
                return gr.update(value=studio.video_html(video)), title, desc, tags

            def _lib_on_project(project):
                items = studio.cuts(project) if project else []
                first_base = items[0]["base"] if items else None
                first_video = items[0]["video"] if items else None
                title, desc, tags = _lib_meta(project, first_base)
                return (
                    gr.update(value=studio.gallery_html(project) if project else ""),
                    gr.update(choices=[(i["label"], i["base"]) for i in items], value=first_base),
                    gr.update(value=studio.video_html(first_video)),
                    title,
                    desc,
                    tags,
                )

            def _lib_refresh(project):
                projects = studio.list_projects()
                project = project if project in projects else (projects[0] if projects else None)
                items = studio.cuts(project) if project else []
                first_base = items[0]["base"] if items else None
                first_video = items[0]["video"] if items else None
                title, desc, tags = _lib_meta(project, first_base)
                return (
                    gr.update(choices=projects, value=project),
                    gr.update(value=studio.gallery_html(project) if project else ""),
                    gr.update(choices=[(i["label"], i["base"]) for i in items], value=first_base),
                    gr.update(value=studio.video_html(first_video)),
                    title,
                    desc,
                    tags,
                )

            def _lib_preset_values(name):
                s = studio.style_from_preset(name)
                return (
                    s["font_name"], int(s["font_size"]), int(s["highlight_size"]),
                    s["base_color"], s["highlight_color"], s["outline_color"],
                    int(s["vertical_position"]), s["mode"], bool(s["uppercase"]),
                )

            def _lib_apply_style(project, base, preset, font, size, hlsize, color, hlcolor, outline, pos, mode, upper, apply_all):
                if not project or not base:
                    return "Selecione um projeto e um corte.", gr.update(), gr.update()
                style = studio.style_from_preset(preset)
                style.update({
                    "font_name": font or style["font_name"],
                    "font_size": int(size),
                    "highlight_size": int(hlsize),
                    "base_color": color,
                    "highlight_color": hlcolor,
                    "outline_color": outline,
                    "vertical_position": int(pos),
                    "mode": mode,
                    "uppercase": bool(upper),
                })
                targets = [item["base"] for item in studio.cuts(project)] if apply_all else [base]
                messages = []
                for target in targets:
                    messages.append(studio.apply_style(project, target, style))
                preview = studio.preview_video(project, base, "style")
                label = f"{len(targets)} corte(s) atualizado(s)." if apply_all else messages[-1]
                return label, gr.update(value=studio.gallery_html(project, bump=int(time.time()))), gr.update(value=studio.video_html(preview, "style"))

            def _lib_preview_music(project, base, track, vol, duck):
                message, preview = studio.preview_music(project, base, track, int(vol), bool(duck), 30)
                return message, (gr.update(value=studio.video_html(preview, "music"), visible=True) if preview else gr.update())

            def _lib_apply_music(project, base, track, vol, duck):
                if not project or not base:
                    return "Selecione um projeto e um corte.", gr.update(), gr.update()
                message = studio.apply_music(project, base, track, int(vol), bool(duck))
                preview = studio.preview_video(project, base, "music")
                return message, gr.update(value=studio.gallery_html(project, bump=int(time.time()))), gr.update(value=studio.video_html(preview, "music"))

            def _lib_track_audio(track):
                return gr.update(value=track) if track else gr.update()

            def _lib_upload_track(upload):
                if not upload:
                    return gr.update(), gr.update(), "Nenhum arquivo enviado."
                saved = studio.save_music_upload(upload)
                if not saved:
                    return gr.update(), gr.update(), "Falha ao salvar a música."
                return gr.update(choices=studio.music_choices(), value=saved), gr.update(value=saved), "Música enviada."

            def _lib_refresh_tracks():
                return gr.update(choices=studio.music_choices())

            def _lib_rename(project, base, title):
                if not project or not base:
                    return "Selecione um corte.", gr.update(), gr.update()
                message = studio.rename_cut(project, base, title)
                items = studio.cuts(project)
                return (
                    message,
                    gr.update(value=studio.gallery_html(project, bump=int(time.time()))),
                    gr.update(choices=[(i["label"], i["base"]) for i in items], value=base),
                )

            def _lib_delete_cut(project, base):
                if not project or not base:
                    return "Selecione um corte.", gr.update(), gr.update(), gr.update()
                message = studio.delete_cut(project, base)
                items = studio.cuts(project)
                next_base = items[0]["base"] if items else None
                next_video = items[0]["video"] if items else None
                return (
                    message,
                    gr.update(value=studio.gallery_html(project, bump=int(time.time()))),
                    gr.update(choices=[(i["label"], i["base"]) for i in items], value=next_base),
                    gr.update(value=studio.video_html(next_video)),
                )

            def _lib_delete_project(project, confirm):
                message = studio.delete_project(project, bool(confirm))
                projects = studio.list_projects()
                first = projects[0] if projects else None
                items = studio.cuts(first) if first else []
                first_base = items[0]["base"] if items else None
                return (
                    message,
                    gr.update(choices=projects, value=first),
                    gr.update(value=studio.gallery_html(first) if first else ""),
                    gr.update(choices=[(i["label"], i["base"]) for i in items], value=first_base),
                    gr.update(value=studio.video_html(items[0]["video"]) if items else ""),
                )

            def _lib_pick_select(base, project):
                base = str(base or "").strip()
                item = studio._cut_by_base(project, base) if project and base else None
                if not item:
                    return gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
                title, desc, tags = _lib_meta(project, base)
                return (
                    gr.update(value=base),
                    gr.update(value=studio.video_html(item["video"])),
                    title,
                    desc,
                    tags,
                )

            def _lib_zip(project):
                path = studio.export_zip(project) if project else ""
                if not path:
                    return "Selecione um projeto.", gr.update(visible=False)
                return "ZIP gerado.", gr.update(value=path, visible=True)

            def _lib_thumbs(project):
                count = studio.make_thumbnails(project) if project else 0
                return f"{count} thumbnail(s) geradas.", gr.update(value=studio.gallery_html(project, bump=int(time.time())))

            lib_project.change(
                _lib_on_project, lib_project,
                [lib_gallery, lib_cut, lib_video, lib_title, lib_desc, lib_tags],
            )
            lib_refresh.click(
                _lib_refresh, lib_project,
                [lib_project, lib_gallery, lib_cut, lib_video, lib_title, lib_desc, lib_tags],
            )
            lib_cut.change(_lib_selection, [lib_project, lib_cut], [lib_video, lib_title, lib_desc, lib_tags])
            lib_pick.change(_lib_pick_select, [lib_pick, lib_project], [lib_cut, lib_video, lib_title, lib_desc, lib_tags])
            lib_meta_btn.click(_lib_meta, [lib_project, lib_cut], [lib_title, lib_desc, lib_tags])
            lib_preset.change(
                _lib_preset_values, lib_preset,
                [lib_font, lib_size, lib_hl_size, lib_color, lib_hl_color, lib_outline, lib_pos, lib_mode, lib_upper],
            )
            lib_apply_btn.click(
                _lib_apply_style,
                [lib_project, lib_cut, lib_preset, lib_font, lib_size, lib_hl_size, lib_color, lib_hl_color, lib_outline, lib_pos, lib_mode, lib_upper, lib_apply_all],
                [lib_status, lib_gallery, lib_video],
                show_progress="hidden",
            )
            lib_track.change(_lib_track_audio, lib_track, lib_track_audio)
            lib_track_refresh.click(_lib_refresh_tracks, None, lib_track)
            lib_music_upload.change(
                _lib_upload_track, lib_music_upload,
                [lib_track, lib_track_audio, lib_status],
            )
            lib_preview_btn.click(
                _lib_preview_music,
                [lib_project, lib_cut, lib_track, lib_vol, lib_duck],
                [lib_status, lib_preview_video],
                show_progress="hidden",
            )
            lib_apply_music_btn.click(
                _lib_apply_music,
                [lib_project, lib_cut, lib_track, lib_vol, lib_duck],
                [lib_status, lib_gallery, lib_video],
                show_progress="hidden",
            )
            lib_rename_btn.click(_lib_rename, [lib_project, lib_cut, lib_new_title], [lib_status, lib_gallery, lib_cut])
            lib_delete_cut_btn.click(
                _lib_delete_cut, [lib_project, lib_cut],
                [lib_status, lib_gallery, lib_cut, lib_video],
            )
            lib_delete_project_btn.click(
                _lib_delete_project, [lib_project, lib_confirm_delete],
                [lib_status, lib_project, lib_gallery, lib_cut, lib_video],
            )
            lib_zip.click(_lib_zip, lib_project, [lib_status, lib_zip_file], show_progress="hidden")
            lib_thumbs.click(_lib_thumbs, lib_project, [lib_status, lib_gallery])
            lib_approve.click(lambda p, b: studio.set_feedback(p, b, "approve") if p and b else "Selecione um corte.", [lib_project, lib_cut], lib_status)
            lib_reject.click(lambda p, b: studio.set_feedback(p, b, "reject") if p and b else "Selecione um corte.", [lib_project, lib_cut], lib_status)

    # Navegação lateral: liga os ícones às abas e mantém o ícone ativo sincronizado.
    demo.load(
        fn=None,
        inputs=None,
        outputs=None,
        js="""
        () => {
          if (window.__fdcNavReady) return;
          window.__fdcNavReady = true;
          const visibleTabs = () => Array.from(document.querySelectorAll('.tab-container button'))
            .filter((b) => !b.closest('.visually-hidden'));
          const findTab = (label) => visibleTabs().find((b) => (b.textContent || '').trim() === label);
          const syncRail = () => {
            const selected = visibleTabs().find((b) => b.classList.contains('selected'));
            const current = selected ? (selected.textContent || '').trim() : '';
            document.querySelectorAll('.fdc-rail-item').forEach((el) => {
              const shouldBeActive = el.getAttribute('data-goto') === current;
              if (shouldBeActive !== el.classList.contains('active')) el.classList.toggle('active', shouldBeActive);
            });
          };
          document.addEventListener('click', (event) => {
            const item = event.target && event.target.closest ? event.target.closest('.fdc-rail-item') : null;
            if (!item) return;
            const tab = findTab(item.getAttribute('data-goto'));
            if (tab) tab.click();
            setTimeout(syncRail, 80);
          });
          new MutationObserver(syncRail).observe(document.body, { subtree: true, attributes: true, attributeFilter: ['class'] });
          setTimeout(() => {
            const create = findTab('Criar Cortes');
            if (create && !create.classList.contains('selected')) create.click();
            syncRail();
          }, 500);
        }
        """,
    )

    # Recarrega o player quando o HTML troca de corte e permite clicar no card.
    demo.load(
        fn=None,
        inputs=None,
        outputs=None,
        js="""
        () => {
          if (window.__fdcPlayerFix) return;
          window.__fdcPlayerFix = true;
          const fixPlayers = () => {
            document.querySelectorAll('#library-panel video.lib-player, #lib_preview video.lib-player').forEach((v) => {
              const src = v.querySelector('source')?.getAttribute('src') || v.getAttribute('src');
              if (!src) return;
              if (v.dataset.fdcSrc === src) return;
              v.dataset.fdcSrc = src;
              try { v.load(); } catch (e) {}
            });
          };
          const observer = new MutationObserver(fixPlayers);
          observer.observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ['src'] });
          setInterval(fixPlayers, 700);
          document.addEventListener('click', (event) => {
            const card = event.target && event.target.closest ? event.target.closest('.fdc-lib-card') : null;
            if (!card) return;
            const base = card.getAttribute('data-base');
            const pick = document.querySelector('#lib_pick textarea, #lib_pick input');
            if (!base || !pick) return;
            const proto = pick.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
            const setter = Object.getOwnPropertyDescriptor(proto, 'value') ? Object.getOwnPropertyDescriptor(proto, 'value').set : null;
            if (setter) setter.call(pick, base); else pick.value = base;
            pick.dispatchEvent(new Event('input', { bubbles: true }));
            pick.dispatchEvent(new Event('change', { bubbles: true }));
          });
        }
        """,
    )
if __name__ == "__main__":
    import webbrowser
    import threading
    import time
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--colab", action="store_true", help="Run in Google Colab mode")
    args = parser.parse_args()

    if args.colab:
        print("Running in Colab mode. Generating public link with Static Mounts...")
        library.set_url_mode("fastapi")
        
        # Broaden allowed paths for Colab
        allowed_dirs = [VIRALS_DIR, WORKING_DIR, os.getcwd(), "."]
        
        # Explicitly set static paths
        try:
            gr.set_static_paths(paths=allowed_dirs)
            print(f"DEBUG: Registered static paths: {allowed_dirs}")
        except AttributeError:
            print("DEBUG: gr.set_static_paths not available")
        
        print(f"DEBUG: Allowed paths for Gradio: {allowed_dirs}")
        
        # Launch with prevent_thread_lock to allow mounting
        app, local_url, share_url = demo.queue().launch(
            share=True, 
            allowed_paths=allowed_dirs,
            prevent_thread_lock=True
        )
        
        # Mount the VIRALS directory explicitly
        app.mount("/virals", StaticFiles(directory=VIRALS_DIR), name="virals")
        print(f"Mounted /virals to {VIRALS_DIR}")
        
        demo.block_thread()
    else:
        # Check environment
        is_windows = (os.name == 'nt')
        
        library.set_url_mode("fastapi")
        allowed_dirs = [VIRALS_DIR, WORKING_DIR, os.getcwd(), "."]
        try:
            gr.set_static_paths(paths=allowed_dirs)
        except AttributeError: pass
        
        from fastapi.responses import FileResponse
        from fastapi import BackgroundTasks

        # Helper to attach routes to any FastAPI app (whether created by Gradio or us)
        def attach_extra_routes(fastapi_app):
            fastapi_app.mount("/virals", StaticFiles(directory=VIRALS_DIR), name="virals")
            
            @fastapi_app.get("/export_xml_api")
            def export_xml_api(project: str, segment: int, background_tasks: BackgroundTasks, format: str = "premiere"):
                try:
                    # License check (online required)
                    s = _load_license_settings()
                    if not s.get('base_url') or not s.get('license_key'):
                        return {"error": "License required: missing license settings."}
                    st = license_client.check_license_online(
                        base_url=s['base_url'],
                        license_key=s['license_key'],
                        hwid=license_client.compute_hwid_hash(),
                        app_version='1.0.0',
                    )
                    if not st.ok:
                        return {"error": f"License required: {st.reason}"}
                    project_path = os.path.join(VIRALS_DIR, project)
                    script_path = os.path.join(WORKING_DIR, "scripts", "export_xml.py")
                    cmd = [sys.executable, script_path, "--project", project_path, "--segment", str(segment), "--format", format]
                    subprocess.run(cmd, check=True)
                    proj_name = os.path.basename(project_path)
                    zip_filename = f"export_{proj_name}_seg{segment}.zip"
                    file_path = os.path.join(project_path, zip_filename)
                    if os.path.exists(file_path):
                        return FileResponse(file_path, filename=zip_filename, media_type='application/zip')
                    else:
                        return {"error": f"File generation failed. Expected: {file_path}"}
                except Exception as e:
                    return {"error": str(e)}
            
            print(f"Mounted /virals to {VIRALS_DIR}")

        if is_windows:
            print("Running in Windows environment (using Gradio launch for convenience).")
            # Windows: Use demo.launch() for convenience (auto-browser, etc)
            try:
                app, local_url, share_url = demo.queue().launch(
                    share=False, 
                    allowed_paths=allowed_dirs, 
                    inbrowser=True,
                    server_name="0.0.0.0",
                    server_port=7860,
                    prevent_thread_lock=True
                )
            except OSError:
                print("Porta 7860 ocupada. Localizando proxima porta disponivel...")
                app, local_url, share_url = demo.queue().launch(
                    share=False, 
                    allowed_paths=allowed_dirs, 
                    inbrowser=True,
                    server_name="0.0.0.0",
                    prevent_thread_lock=True
                )
            attach_extra_routes(app)
            demo.block_thread()
        else:
            print("Running in Linux/Container environment (using Uvicorn for stability).")
            # Linux/HF: Use Uvicorn for explicit loop control
            app = FastAPI()
            attach_extra_routes(app)
            # Disable SSR to prevent Node proxying issues on HF Spaces
            app = gr.mount_gradio_app(app, demo.queue(), path="/", allowed_paths=allowed_dirs, ssr_mode=False)
            uvicorn.run(app, host="0.0.0.0", port=7860)
