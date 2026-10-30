import os
import re
import yt_dlp
import sys
from i18n.i18n import I18nAuto
i18n = I18nAuto()

BROWSERS = ('chrome', 'edge', 'firefox', 'brave', 'opera', 'vivaldi', 'chromium', 'whale')

def get_aria2c_path():
    """Retorna o caminho do executavel aria2c se disponivel."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_aria2 = os.path.join(project_root, '.venv', 'Scripts', 'aria2c.exe')
    if os.path.exists(venv_aria2):
        return venv_aria2
    local_aria2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aria2c.exe')
    if os.path.exists(local_aria2):
        return local_aria2
    import shutil
    sys_aria2 = shutil.which('aria2c')
    if sys_aria2:
        return sys_aria2
    return None

def download_with_browser_cookies(url, ydl_opts):
    """Download video directly; fallback to browser cookies only if authentication/bot check is required."""
    def try_download(opts):
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    if ydl_opts.get('cookiefile'):
        try:
            try_download(ydl_opts)
            return
        except Exception as error:
            print(f"Cookies.txt recusado: {error}")

    # Tenta download direto (sem cookies). Funciona para a maioria dos videos publicos sem disparar erros de navegadores locais.
    options = {key: value for key, value in ydl_opts.items() if key != 'cookiefile'}
    try:
        try_download(options)
        return
    except Exception as first_error:
        error_str = str(first_error).lower()
        # Se o erro for de legenda (ex: 429), repassa para retry de video limpo
        if "unable to download video subtitles" in error_str or "429" in error_str:
            raise first_error

        # Se falhou com aria2c, tenta com o multi-threading nativo
        if options.get('external_downloader'):
            try:
                print("[TURBO] Tentando fallback para downloader nativo multi-thread...")
                native_opts = {k: v for k, v in options.items() if k not in ('external_downloader', 'external_downloader_args')}
                try_download(native_opts)
                return
            except Exception:
                pass

        # Se falhou por autenticacao/bloqueio, tenta cookies dos navegadores instalados silenciosamente
        last_error = first_error
        for browser in BROWSERS:
            try:
                browser_opts = {key: value for key, value in ydl_opts.items() if key != 'cookiefile'}
                browser_opts['cookiesfrombrowser'] = (browser,)
                browser_opts['quiet'] = True
                browser_opts['no_warnings'] = True
                try_download(browser_opts)
                return
            except Exception as b_err:
                last_error = b_err
                continue
        raise last_error

def sanitize_filename(name):
    """Remove caracteres inválidos, acentos e emojis para evitar erro de encoding no Windows/FFmpeg/Aria2."""
    import unicodedata
    # Normaliza e remove acentos/diacríticos e emojis para garantir 100% de compatibilidade de caminhos no Windows
    nfkd = unicodedata.normalize('NFKD', str(name))
    cleaned = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    cleaned = re.sub(r'[\\/*?:"<>|]', '', cleaned)
    cleaned = re.sub(r'[\r\n\t]+', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned or "Video" 

def progress_hook(d):
    if d['status'] == 'downloading':
        try:
            p = d.get('_percent_str', '').replace('%','')
            print(f"[download] {p}% - {d.get('_eta_str', 'N/A')} remaining", flush=True)
        except:
            pass
    elif d['status'] == 'finished':
        print(f"[download] Download concluído: {d['filename']}", flush=True)

def download(url, base_root="VIRALS", download_subs=True, quality="best", cookies_file=None):
    # 1. Extrair informacoes do video para pegar o titulo
    print(i18n("Extracting video information..."))
    title = None
    
    # Tentativa 1: Sem cookies (mais rapido e sem alarmes de navegadores locais)
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title')
    except Exception:
        title = None

    # Tentativa 2: Se falhar (ex: video restrito), tenta cookies fornecidos
    if not title and cookies_file and os.path.exists(cookies_file):
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'cookiefile': cookies_file}) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title')
        except Exception:
            pass

    # Tentativa 3: Se ainda falhar, tenta cookies dos navegadores instalados
    if not title:
        for browser in BROWSERS:
            try:
                with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'cookiesfrombrowser': (browser,)}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title')
                if title:
                    break
            except Exception:
                pass

    # Fallback final
    if title:
        safe_title = sanitize_filename(title)
        try:
            print(i18n("Detected title: {}").format(title))
        except UnicodeEncodeError:
            # Fallback for Windows consoles that choke on Emojis
            clean_title = title.encode('ascii', 'replace').decode('ascii')
            print(i18n("Detected title: {}").format(clean_title))
    else:
        print(i18n("WARNING: Title could not be obtained. Using 'Unknown_Video'."))
        safe_title = i18n("Unknown_Video")

    # 2. Criar estrutura de pastas
    project_folder = os.path.join(base_root, safe_title)
    os.makedirs(project_folder, exist_ok=True)
    
    # Caminho final do vídeo
    output_filename = 'input' 
    output_path_base = os.path.join(project_folder, output_filename)
    final_video_path = f"{output_path_base}.mp4"

    # Verificação inteligente
    if os.path.exists(final_video_path):
        if os.path.getsize(final_video_path) > 1024: 
            try:
                print(i18n("Video already exists at: {}").format(final_video_path))
            except UnicodeEncodeError:
                print(i18n("Video already exists at: {}").format(final_video_path.encode('ascii', 'replace').decode('ascii')))
            print(i18n("Skipping download and reusing local file."))
            return final_video_path, project_folder
        else:
            print(i18n("Existing file found but seems corrupted/empty. Downloading again..."))
            try:
                os.remove(final_video_path)
            except:
                pass

    # Limpeza de temp
    temp_path = f"{output_path_base}.temp.mp4"
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except:
            pass

    # Mapeamento de Qualidade Turbo
    # Prioriza MP4 direto (H.264/AAC) em 1080p ou 720p. 
    # Isso evita baixar 4K/WebM desnecessário de 3GB que trava o processador e demora 20 minutos.
    quality_map = {
        "best": 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
        "1080p": 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
        "720p": 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best',
        "480p": 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]/best',
        "4k": 'bestvideo+bestaudio/best',
    }
    selected_format = quality_map.get(quality, quality_map["best"])
    print(i18n("Configuring download quality: {} -> {}").format(quality, selected_format))

    ydl_opts = {
        'format': selected_format,
        'overwrites': True,
        'outtmpl': output_path_base, 
        'postprocessor_args': [
            '-movflags', 'faststart'
        ],
        'merge_output_format': 'mp4',
        'progress_hooks': [progress_hook],
        # Opções de Legenda
        'writesubtitles': download_subs,
        'writeautomaticsub': download_subs,
        'subtitleslangs': ['pt.*', 'en.*', 'sp.*'], # Prioritize generic PT, EN, SP
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
        'skip_download': False,
        'quiet': False,
        'no_warnings': False,
        'force_ipv4': True,

        # OTIMIZAÇÕES TURBO DE VELOCIDADE
        'concurrent_fragment_downloads': 10,  # Baixa até 10 fragmentos simultâneos
        'buffersize': 1024 * 1024 * 16,        # Buffer de 16MB em memória RAM
        'http_chunk_size': 10485760,            # Blocos de 10MB
        'retries': 10,
        'fragment_retries': 10,
    }

    # Ativa acelerador Aria2 se disponivel
    aria2_path = get_aria2c_path()
    if aria2_path:
        print(f"[TURBO] Acelerador Aria2 detectado ({aria2_path}) - Ativando 16 conexões simultâneas!")
        ydl_opts['external_downloader'] = aria2_path
        ydl_opts['external_downloader_args'] = [
            '-x', '16',
            '-s', '16',
            '-k', '1M',
            '-j', '8',
            '--min-split-size=1M',
            '--max-connection-per-server=16',
            '--summary-interval=2',
        ]
    else:
        print("[TURBO] Multi-threading nativo ativado (10 downloads simultâneos de fragmentos)!")
    if cookies_file:
        ydl_opts['cookiefile'] = cookies_file
    

    
    if download_subs:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegSubtitlesConvertor',
            'format': 'srt',
        }]

    try:
        print(i18n("Downloading video to: {}...").format(project_folder))
    except UnicodeEncodeError:
        print(i18n("Downloading video to: {}...").format(project_folder.encode('ascii', 'replace').decode('ascii')))
    
    # Tentativa 1: Com configuração original
    try:
        download_with_browser_cookies(url, ydl_opts)
    except yt_dlp.utils.DownloadError as e:
        error_str = str(e)
        if "No address associated with hostname" in error_str or "Failed to resolve" in error_str:
            print(i18n("\n[CRITICAL ERROR] Connection Failure: Could not access YouTube."))
            print(i18n("Check your internet connection or if there is any DNS block."))
            print(i18n("Details: {}").format(e))
            sys.exit(1)
        
        elif download_subs and ("Unable to download video subtitles" in error_str or "429" in error_str):
            print(i18n("\n[AVISO] Legendas nativas do YouTube indisponiveis (limite de requisicao 429)."))
            print(i18n("Prosseguindo com o download do video. O Whisper IA transcrevera o audio na proxima etapa com precisao maxima!"))
            
            ydl_opts['writesubtitles'] = False
            ydl_opts['writeautomaticsub'] = False
            ydl_opts['postprocessors'] = [p for p in ydl_opts.get('postprocessors', []) if 'Subtitle' not in p.get('key', '')]
            
            try:
                download_with_browser_cookies(url, ydl_opts)
            except Exception as e2:
                print(i18n("Fatal error on second attempt: {}").format(e2))
                raise
        elif "is not a valid URL" in error_str:
             print(i18n("Error: the entered link is not valid."))
             raise 
        else:
            print(i18n("Download error: {}").format(e))
            raise
    except Exception as e:
        print(i18n("Unexpected error: {}").format(e))
        raise

    # RENOMEAR LEGENDA PARA PADRÃO (input.vtt ou input.srt)
    # Se for VTT, converte para SRT para garantir compatibilidade.
    try:
        import glob
        # Pega a primeira que encontrar
        potential_subs = glob.glob(os.path.join(project_folder, "input.*.vtt")) + glob.glob(os.path.join(project_folder, "input.*.srt"))
        
        if potential_subs:
            best_sub = potential_subs[0]
            ext = os.path.splitext(best_sub)[1]
            new_name = os.path.join(project_folder, "input.srt") # Vamos padronizar tudo para .srt
            
            if ext.lower() == '.vtt':
                try:
                    print(i18n("Formatting complex VTT subtitle ({}) to clean SRT...").format(os.path.basename(best_sub)))
                except UnicodeEncodeError:
                    print(i18n("Formatting complex VTT subtitle ({}) to clean SRT...").format(os.path.basename(best_sub).encode('ascii', 'replace').decode('ascii')))
                try:
                    with open(best_sub, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    srt_content = []
                    counter = 1
                    
                    seen_texts = set()
                    last_text = ""
                    
                    for line in lines:
                        clean_line = line.strip()
                        # Ignora Headers e Metadados do VTT/Youtube
                        if clean_line.startswith("WEBVTT") or \
                           clean_line.startswith("X-TIMESTAMP") or \
                           clean_line.startswith("NOTE") or \
                           clean_line.startswith("Kind:") or \
                           clean_line.startswith("Language:"):
                            continue
                        
                        if "-->" in clean_line:
                            # Parse Timestamp
                            parts = clean_line.split("-->")
                            start = parts[0].strip()
                            # Remove tags de posicionamento "align:start position:0%"
                            end = parts[1].strip().split(' ')[0] 
                            
                            def fix_time(t):
                                t = t.replace('.', ',')
                                if t.count(':') == 1: 
                                    t = "00:" + t
                                return t
                            
                            current_start = fix_time(start)
                            current_end = fix_time(end)
                            
                        elif clean_line:
                             import html
                             # 1. Decodifica entidades HTML (&gt; -> >, &quot; -> ", etc.)
                             unescaped = html.unescape(clean_line)
                             # 2. Remove tags complexas <00:00:00.560><c> etc
                             text = re.sub(r'<[^>]+>', '', unescaped).strip()
                             # 3. Remove marcadores de troca de orador do YouTube (>> ou >>> ou &gt;&gt;)
                             text = re.sub(r'^(?:>>|>>>|\&gt;\&gt;|\&gt;\&gt;\&gt;)\s*', '', text)
                             text = re.sub(r'\s*(?:>>|>>>|\&gt;\&gt;|\&gt;\&gt;\&gt;)\s*', ' ', text).strip()
                             
                             if not text: continue
                             
                             # Lógica para remover duplicatas do estilo "Roll-up" ou "Karaoke"
                             # O YouTube repete a linha anterior às vezes.
                             # Ex:
                             # 1: "Quanto custa"
                             # 2: "Quanto custa\nQuantos quilos"
                             
                             # Vamos pegar apenas a ULTIMA linha se tiver quebras
                             lines_in_text = text.split('\n')
                             final_line = lines_in_text[-1].strip()
                             
                             if not final_line: continue

                             # Filtro de duplicidade consecutivo
                             if final_line == last_text:
                                 continue
                             
                             # Evita blocos ultra curtos (glitch de 10ms) que repetem texto
                             # Mas aqui estamos processando texto.
                             
                             srt_content.append(f"{counter}\n")
                             srt_content.append(f"{current_start} --> {current_end}\n")
                             srt_content.append(f"{final_line}\n\n")
                             
                             last_text = final_line
                             counter += 1
                    
                    with open(new_name, 'w', encoding='utf-8') as f_out:
                        f_out.writelines(srt_content)
                    
                    try:
                        print(i18n("Subtitle converted and cleaned: {}").format(new_name))
                    except UnicodeEncodeError:
                        print(i18n("Subtitle converted and cleaned: {}").format(new_name.encode('ascii', 'replace').decode('ascii')))
                    try: os.remove(best_sub) 
                    except: pass
                    
                except Exception as e_conv:
                    print(i18n("Failed to convert VTT: {}. Keeping original.").format(e_conv))
                    # Fallback: rename apenas
                    new_name_fallback = os.path.join(project_folder, "input.vtt")
                    if os.path.exists(new_name_fallback) and new_name_fallback != best_sub:
                        try: os.remove(new_name_fallback)
                        except: pass
                    os.rename(best_sub, new_name_fallback)

            else:
                # Já é SRT, só renomeia
                if os.path.exists(new_name) and new_name != best_sub:
                    try: os.remove(new_name)
                    except: pass
                os.rename(best_sub, new_name)
                try:
                    print(i18n("SRT subtitle renamed to: {}").format(new_name))
                except UnicodeEncodeError:
                    print(i18n("SRT subtitle renamed to: {}").format(new_name.encode('ascii', 'replace').decode('ascii')))
            
            # Limpa sobras
            for extra in potential_subs[1:]:
                try: os.remove(extra)
                except: pass

    except Exception as e_ren:
        print(i18n("Error processing subtitles: {}").format(e_ren))

    return final_video_path, project_folder
