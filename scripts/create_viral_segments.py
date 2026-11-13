import json
import os
import re
import sys
import time
import ast
import io
import unicodedata

# Configura stdout para evitar erros de encoding no Windows (substitui caracteres inválidos por ?)
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    try:
        # Mantém encoding original mas ignora erros (substitui por ?)
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=sys.stdout.encoding or 'utf-8', errors='replace', line_buffering=True)
    except:
        pass

# Tenta importar bibliotecas de IA opcionalmente
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    import g4f
    HAS_G4F = True
except ImportError:
    HAS_G4F = False

try:
    from llama_cpp import Llama
    HAS_LLAMA_CPP = True
except ImportError:
    HAS_LLAMA_CPP = False

# Guarda o último motivo de falha da IA para mostrar um erro útil no lugar de cortes falsos.
LAST_AI_ERROR = ""


def _set_ai_error(message):
    global LAST_AI_ERROR
    LAST_AI_ERROR = str(message or "").strip()

def clean_json_response(response_text):
    """
    Limpa e extrai a lista de segmentos virais da resposta do modelo de IA.
    Suporta:
    1. Blocos de markdown ```json ... ```
    2. Listas JSON brutas contendo diretamente os segmentos [ {...}, {...} ]
    3. Objetos JSON contendo chaves como 'segments', 'viral_moments', 'cuts', 'cortes', 'items', 'results'
    4. Fragment parser para respostas truncadas por limite de tokens
    """
    if not isinstance(response_text, str):
        response_text = str(response_text)
    
    if not response_text:
        return {"segments": []}

    # 1. Limpeza preliminar: remove tags de pensamento (DeepSeek R1) e normaliza escapes
    response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL)
    try:
        if "\\n" in response_text or "\\\"" in response_text:
            response_text = response_text.replace("\\n", "\n").replace('\\"', '"').replace("\\'", "'")
    except Exception:
        pass

    # 2. Tentativa Direta A: Extrair bloco markdown ```json ... ``` se existir
    markdown_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response_text)
    if markdown_match:
        cand = markdown_match.group(1).strip()
        try:
            parsed = json.loads(cand)
            if isinstance(parsed, list):
                return {"segments": parsed}
            elif isinstance(parsed, dict):
                for k in ["segments", "viral_moments", "cuts", "cortes", "items", "results"]:
                    if k in parsed and isinstance(parsed[k], list):
                        return {"segments": parsed[k]}
        except Exception:
            pass

    # 3. Tentativa Direta B: Tentar parsear o texto inteiro como JSON direto
    trimmed = response_text.strip()
    if (trimmed.startswith("{") and trimmed.endswith("}")) or (trimmed.startswith("[") and trimmed.endswith("]")):
        try:
            parsed = json.loads(trimmed)
            if isinstance(parsed, list):
                return {"segments": parsed}
            elif isinstance(parsed, dict):
                for k in ["segments", "viral_moments", "cuts", "cortes", "items", "results"]:
                    if k in parsed and isinstance(parsed[k], list):
                        return {"segments": parsed[k]}
        except Exception:
            pass

    # 4. Tentativa C: Busca flexível por qualquer objeto JSON contendo 'segments', 'cuts', 'cortes' ou 'viral'
    keywords = ['segments', 'cuts', 'cortes', 'viral']
    matches = []
    for kw in keywords:
        matches.extend([m.start() for m in re.finditer(kw, response_text, re.IGNORECASE)])
    matches = sorted(list(set(matches)))

    for match_idx in matches:
        start_search = max(0, match_idx - 5000)
        snippet_before = response_text[start_search:match_idx]
        last_open_rel = snippet_before.rfind('{')
        if last_open_rel != -1:
            real_start = start_search + last_open_rel
            candidate_text = response_text[real_start:]
            try:
                decoder = json.JSONDecoder()
                obj, _ = decoder.raw_decode(candidate_text)
                if isinstance(obj, dict):
                    for k in ["segments", "viral_moments", "cuts", "cortes", "items", "results"]:
                        if k in obj and isinstance(obj[k], list):
                            return {"segments": obj[k]}
            except Exception:
                pass

    # 5. Tentativa D: Tentar achar qualquer lista JSON bruta [ { ... } ]
    array_start = response_text.find('[')
    if array_start != -1:
        candidate_arr = response_text[array_start:]
        try:
            decoder = json.JSONDecoder()
            arr_obj, _ = decoder.raw_decode(candidate_arr)
            if isinstance(arr_obj, list) and len(arr_obj) > 0 and isinstance(arr_obj[0], dict):
                return {"segments": arr_obj}
        except Exception:
            pass

    # 6. Tentativa E: Fragment Parser (para JSON truncado no meio de um chunk)
    try:
        match_list = re.search(r'["\']?(?:segments|cuts|cortes)["\']?\s*:\s*\[', response_text, re.IGNORECASE)
        start_pos = match_list.end() if match_list else response_text.find('[') + 1
        if start_pos > 0:
            current_pos = start_pos
            found_segments = []
            decoder = json.JSONDecoder()
            while current_pos < len(response_text):
                while current_pos < len(response_text) and response_text[current_pos] in ' \t\n\r,':
                    current_pos += 1
                if current_pos >= len(response_text) or response_text[current_pos] == ']':
                    break
                try:
                    obj, end_pos = decoder.raw_decode(response_text[current_pos:])
                    if isinstance(obj, dict):
                        found_segments.append(obj)
                    current_pos += end_pos
                except json.JSONDecodeError:
                    break
            if found_segments:
                print(f"[INFO] Recuperado {len(found_segments)} segmentos de JSON truncado.")
                return {"segments": found_segments}
    except Exception:
        pass

    return {"segments": []}


def preprocess_transcript_for_ai(segments):
    """
    Concatenates transcript segments into a single string with embedded time tags.
    """
    if not segments:
        return ""

    full_text = ""
    last_tag_time = -100  # Force first tag
    
    # Try to start with (0s) based on first segment
    first_start = segments[0].get('start', 0)
    full_text += f"({int(first_start)}s) "
    last_tag_time = first_start

    for seg in segments:
        text = seg.get('text', '').strip()
        end_time = seg.get('end', 0)
        
        full_text += text + " "
        
        if end_time - last_tag_time >= 4:
            full_text += f"({int(end_time)}s) "
            last_tag_time = end_time

    return full_text.strip()

GEMINI_FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.8-flash",
]


def _gemini_retry_delay(error_str, attempt):
    """Espera sugerida pelo Google, limitada a 70s para nao travar o app."""
    match = re.search(r"retry in (\d+(\.\d+)?)s", error_str)
    if match:
        return min(float(match.group(1)) + 2.0, 70.0)
    return min(20.0 * (attempt + 1), 70.0)


def call_gemini(prompt, api_key, model_name='gemini-2.5-flash'):
    _set_ai_error("")
    if not HAS_GEMINI:
        _set_ai_error("Gemini: biblioteca google-generativeai nao instalada")
        raise ImportError("A biblioteca 'google-generativeai' não está instalada. Instale com: pip install google-generativeai")

    genai.configure(api_key=api_key)

    models_to_try = [model_name]
    for fallback in GEMINI_FALLBACK_MODELS:
        if fallback not in models_to_try:
            models_to_try.append(fallback)

    # Cada modelo ganha no maximo duas tentativas. Se a cota estourar, o proximo
    # modelo e testado na hora, em vez de esperar minutos no mesmo modelo.
    for name in models_to_try:
        for attempt in range(2):
            try:
                response = genai.GenerativeModel(name).generate_content(prompt)
                return response.text
            except Exception as e:
                error_str = str(e)
                err_lower = error_str.lower()
                _set_ai_error(f"Gemini: {error_str[:500]}")

                if "API_KEY_INVALID" in error_str or "api key not valid" in err_lower:
                    print("\n[ERRO CRÍTICO GEMINI] Chave de API inválida ou revogada! Obtenha sua chave gratuita em https://aistudio.google.com/ e insira no campo Gemini API Key.")
                    return "{}"

                if "429" in error_str or "quota exceeded" in err_lower or "rate limit" in err_lower:
                    if "perday" in err_lower.replace(" ", "") or "per day" in err_lower or "daily" in err_lower:
                        print(f"[429] Cota diaria esgotada em '{name}'. Tentando outro modelo...")
                        break
                    if attempt == 0:
                        wait_time = _gemini_retry_delay(error_str, attempt)
                        print(f"[429] Limite por minuto em '{name}'. Aguardando {wait_time:.0f}s...", flush=True)
                        time.sleep(wait_time)
                        continue
                    print(f"[429] '{name}' continua limitado. Tentando outro modelo...")
                    break

                if "404" in error_str or "not found" in err_lower or "no longer available" in err_lower:
                    print(f"[Gemini 404] Modelo '{name}' indisponivel. Tentando outro modelo...")
                    break

                print(f"Erro na API do Gemini ({name}): {e}")
                break

    print("Falha em todos os modelos do Gemini.")
    _set_ai_error("Gemini: falha em todos os modelos (quota/limite de requisicoes)")
    return "{}"

def call_g4f(prompt, model_name=None):
    _set_ai_error("")
    if not HAS_G4F:
        _set_ai_error("G4F: biblioteca nao instalada")
        raise ImportError("A biblioteca 'g4f' não está instalada. Instale com: pip install g4f")
    if not model_name:
        model_name = g4f.models._all_models[0]
    
    max_retries = 3
    base_wait = 5
    
    for attempt in range(max_retries):
        try:
            response = g4f.ChatCompletion.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            
            if isinstance(response, dict):
                if 'error' in response:
                    raise Exception(f"API Error: {response['error']}")
                if 'choices' in response and isinstance(response['choices'], list):
                    if len(response['choices']) > 0:
                         content = response['choices'][0].get('message', {}).get('content', '')
                         if content:
                             return content
                if not response:
                     raise ValueError("Empty Dict response")

                return json.dumps(response)

            if not response:
                print(f"[WARN] G4F retornou resposta vazia. Tentativa {attempt+1}/{max_retries}")
                time.sleep(base_wait)
                continue
            
            if isinstance(response, str):
                return response

            try:
                return json.dumps(response, ensure_ascii=False)
            except:
                return str(response)
            
        except Exception as e:
            print(f"[WARN] Erro na API do G4F (Tentativa {attempt+1}/{max_retries}): {e}")
            _set_ai_error(f"G4F: {e}")
            if attempt < max_retries - 1:
                wait_time = base_wait * (2 ** attempt)
                time.sleep(wait_time)
            
    print(f"Falha crítica após {max_retries} tentativas no G4F.")
    _set_ai_error("G4F: falha apos varias tentativas")
    return "{}"

def load_transcript(project_folder):
    """Parses input.tsv or input.srt from the project folder."""
    input_tsv = os.path.join(project_folder, 'input.tsv')
    input_srt = os.path.join(project_folder, 'input.srt')

    transcript_segments = []
    
    # Try to load TSV first (more reliable time)
    if os.path.exists(input_tsv):
        try:
            with open(input_tsv, 'r', encoding='utf-8') as f:
                # Skip header
                lines = f.readlines()[1:] 
                for line in lines:
                    parts = line.strip().split('\t')
                    if len(parts) >= 3:
                        start_ms = float(parts[0])
                        end_ms = float(parts[1])
                        text = parts[2]
                        transcript_segments.append({
                            'start': start_ms / 1000.0, 
                            'end': end_ms / 1000.0, 
                            'text': text
                        })
        except Exception as e:
            print(f"Error parsing TSV: {e}")

    # Fallback to SRT parser if TSV empty/failed
    if not transcript_segments and os.path.exists(input_srt):
         with open(input_srt, 'r', encoding='utf-8') as f:
             srt_content = f.read()
         pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n((?:(?!\n\n).)*)', re.DOTALL)
         matches = pattern.findall(srt_content)
         
         def srt_time_to_seconds(t_str):
             h, m, s = t_str.replace(',', '.').split(':')
             return int(h) * 3600 + int(m) * 60 + float(s)

         for m in matches:
             start_sec = srt_time_to_seconds(m[1])
             end_sec = srt_time_to_seconds(m[2])
             text = m[3].replace('\n', ' ')
             transcript_segments.append({'start': start_sec, 'end': end_sec, 'text': text})

    if not transcript_segments:
        raise ValueError("Could not parse transcript from TSV or SRT.")
    
    return transcript_segments

def _normalize_for_match(text):
    """Normaliza texto para comparar frases entre a IA e a transcrição."""
    value = unicodedata.normalize("NFKD", str(text or ""))
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.lower()
    value = re.sub(r"[^\w\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _tokens_for_match(text):
    return [token for token in _normalize_for_match(text).split() if token]


def _parse_time_ref(value):
    """Converte a referência de tempo da IA em segundos.

    Aceita "(90s)", "90", "1:30" e "1:02:45". Antes, um timecode com dois pontos
    era lido como o primeiro número ("1"), jogando o corte para o início.
    """
    text = str(value or "").strip()
    if not text:
        return 0
    timecode = re.search(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", text)
    if timecode:
        hours, minutes, seconds = timecode.groups()
        if seconds is None:
            return int(hours) * 60 + int(minutes)
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    match = re.search(r"\d+", text)
    return int(match.group()) if match else 0


def _safe_score(value):
    """Aceita nota em numero ou texto e mantem sempre um inteiro entre 0 e 100."""
    try:
        score = int(float(str(value).strip().replace('%', '').replace(',', '.')))
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, score))


def _match_score(window_text, target):
    """Quanto a janela de fala corresponde ao trecho informado pela IA.

    1.0 quando o trecho aparece literalmente (caso esperado). Caso contrario,
    devolve a fracao de palavras do trecho encontradas na janela, para tolerar
    pequenas diferencas de transcricao.
    """
    if not target:
        return 0.0
    if target in window_text:
        return 1.0
    target_tokens = set(_tokens_for_match(target))
    if not target_tokens:
        return 0.0
    return len(target_tokens & set(_tokens_for_match(window_text))) / len(target_tokens)


MAX_SENTENCE_BLOCK_SECONDS = 12.0
MAX_SENTENCE_BLOCK_WORDS = 45


def _build_sentence_blocks(transcript_segments):
    """Agrupa segmentos da transcrição em blocos de frase.

    Além da pontuação e das pausas, fecha o bloco quando ele fica longo demais.
    Legendas automáticas do YouTube costumam não ter pontuação nenhuma; sem esse
    limite o vídeo inteiro virava um único bloco e todos os cortes colapsavam
    para 0 - duração total.
    """
    blocks = []
    current = None

    for segment in transcript_segments:
        text = str(segment.get("text") or "").strip()
        if not text:
            continue

        start = float(segment.get("start", 0) or 0)
        end = float(segment.get("end", start) or start)

        if current is None:
            current = {"start": start, "end": end, "text": text}
        else:
            gap = start - current["end"]
            too_long = (current["end"] - current["start"]) >= MAX_SENTENCE_BLOCK_SECONDS
            too_many_words = len(current["text"].split()) >= MAX_SENTENCE_BLOCK_WORDS
            if gap > 1.2 or too_long or too_many_words:
                blocks.append(current)
                current = {"start": start, "end": end, "text": text}
            else:
                current["end"] = end
                current["text"] = current["text"] + " " + text

        if re.search(r"[.!?…][\"')\]]?\s*$", text):
            blocks.append(current)
            current = None

    if current is not None:
        blocks.append(current)

    return [block for block in blocks if block["end"] > block["start"]]


def _best_block_index(blocks, phrase, around_time=None):
    """Encontra o bloco com maior sobreposição de palavras com a frase da IA."""
    phrase_tokens = set(_tokens_for_match(phrase))
    if not phrase_tokens:
        return None

    best_index = None
    best_score = 0.0

    for index, block in enumerate(blocks):
        if around_time is not None:
            if block["end"] < around_time - 90 or block["start"] > around_time + 90:
                continue

        block_tokens = set(_tokens_for_match(block.get("text", "")))
        if not block_tokens:
            continue

        score = len(phrase_tokens & block_tokens) / len(phrase_tokens)
        if score > best_score:
            best_score = score
            best_index = index

    return best_index if best_score >= 0.34 else None


def _block_index_at_time(blocks, timestamp):
    if not blocks:
        return None
    for index, block in enumerate(blocks):
        if block["start"] <= timestamp < block["end"]:
            return index
    return min(range(len(blocks)), key=lambda index: abs(blocks[index]["start"] - timestamp))


def _block_index_for_end(blocks, timestamp):
    """Para o fim, usa o bloco que contém o tempo ou o bloco anterior (fim da frase)."""
    if not blocks:
        return None
    for index, block in enumerate(blocks):
        if block["start"] <= timestamp < block["end"]:
            return index

    previous = None
    for index, block in enumerate(blocks):
        if block["start"] <= timestamp:
            previous = index
        else:
            break
    return previous if previous is not None else 0


def _snap_segments_to_sentences(segments, transcript_segments, min_duration, max_duration):
    """Ajusta início/fim para frases completas sem perder o ponto exato do hook.

    O início só recua até o começo da frase quando a diferença é pequena; caso
    contrário mantém o trecho exato que a IA escolheu. O fim é esticado até o
    fim da frase para não terminar no meio de uma ideia.
    """
    blocks = _build_sentence_blocks(transcript_segments)
    if not blocks:
        return segments

    snapped = []
    for segment in segments:
        try:
            start = float(segment.get("start_time", 0) or 0)
            end = float(segment.get("end_time", start) or start)
            if end <= start:
                end = start + min_duration

            start_index = _block_index_at_time(blocks, start)
            end_index = _block_index_for_end(blocks, end)

            if start_index is None or end_index is None:
                snapped.append(segment)
                continue

            if end_index < start_index:
                end_index = start_index

            block_start = float(blocks[start_index]["start"])
            new_start = block_start if (start - block_start) <= 2.5 else start

            block_end = float(blocks[end_index]["end"])
            new_end = block_end if (block_end - end) <= 2.5 else end

            # Duração mínima: avança até o fim de frases completas.
            while end_index < len(blocks) - 1 and (new_end - new_start) < min_duration:
                end_index += 1
                new_end = float(blocks[end_index]["end"])

            # Duração máxima: recua até a última frase que ainda cabe.
            while end_index > start_index and (new_end - new_start) > max_duration:
                end_index -= 1
                new_end = float(blocks[end_index]["end"])

            if (new_end - new_start) > max_duration:
                new_end = new_start + max_duration

            if new_end <= new_start:
                snapped.append(segment)
                continue

            updated = dict(segment)
            updated["start_time"] = round(new_start, 3)
            updated["end_time"] = round(new_end, 3)
            updated["duration"] = round(new_end - new_start, 3)
            snapped.append(updated)
        except Exception:
            snapped.append(segment)

    return snapped


def process_segments(raw_segments, transcript_segments, min_duration, max_duration, output_count=None):
    """
    Aligns raw AI segments (with reference tags) to actual transcript timestamps.
    Applies constraints, validation, and deduplication.
    """
    
    all_segments = raw_segments
    tempo_minimo = min_duration
    tempo_maximo = max_duration
    
    # Sort segments by score (descending)
    try:
        all_segments.sort(key=lambda x: int(x.get('score', 0)), reverse=True)
    except:
        pass

    # --- POST-PROCESSING: Match Text to Timestamps ---
    processed_segments = []
    
    print(f"[DEBUG] Matching {len(all_segments)} raw segments to timestamps...")
    
    for seg in all_segments:
        try:
            # 1. Parse Reference Time
            ref_time_val = _parse_time_ref(seg.get('start_time_ref', '(0s)'))
                
            # Find segment index closest to ref_time
            start_idx = 0
            min_diff = 999999
            for i, s in enumerate(transcript_segments):
                diff = abs(s['start'] - ref_time_val)
                if diff < min_diff:
                    min_diff = diff
                    start_idx = i
                if s['start'] > ref_time_val + 10: 
                    break
            
            # Backtrack curto: o texto da IA será usado para achar a frase exata.
            start_idx = max(0, start_idx - 2)
            
            # 2. Localiza a frase exata de inicio usando o texto informado pela IA.
            # O casamento reverso (janela dentro do texto) foi removido: ele aceitava
            # qualquer trecho curto parecido e fazia o corte comecar no lugar errado.
            start_text_target = _normalize_for_match(seg.get('start_text', ''))

            final_start_time = -1
            match_start_idx = -1

            if start_text_target:
                search_begin = max(0, start_idx - 3)
                search_limit = min(len(transcript_segments), start_idx + 60)
                candidates = []
                for i in range(search_begin, search_limit):
                    window_text = " ".join(
                        _normalize_for_match(transcript_segments[j]['text'])
                        for j in range(i, min(i + 3, len(transcript_segments)))
                    )
                    if _match_score(window_text, start_text_target) >= 0.75:
                        candidates.append(i)
                if candidates:
                    # Havendo mais de uma ocorrencia, usa a mais proxima do timestamp da IA.
                    match_start_idx = min(
                        candidates,
                        key=lambda idx: abs(float(transcript_segments[idx]['start']) - ref_time_val),
                    )
                    final_start_time = transcript_segments[match_start_idx]['start']

            # Fallback: usa o timestamp informado pela IA.
            if final_start_time == -1:
                final_start_time = transcript_segments[start_idx]['start'] if start_idx < len(transcript_segments) else ref_time_val
                match_start_idx = start_idx

            # 3. Find End Text
            end_text_target = _normalize_for_match(seg.get('end_text', ''))
            final_end_time = -1

            # Optional: the AI can provide an approximate end tag.
            end_ref_raw = seg.get('end_time_ref')
            end_ref_val = _parse_time_ref(end_ref_raw) if end_ref_raw not in (None, '') else None

            end_matches = []
            if match_start_idx != -1 and end_text_target:
                search_end_limit = min(len(transcript_segments), match_start_idx + 200)
                for i in range(match_start_idx, search_end_limit):
                    window_text = " ".join(
                        _normalize_for_match(transcript_segments[j]['text'])
                        for j in range(max(match_start_idx, i - 2), i + 1)
                    )
                    if _match_score(window_text, end_text_target) >= 0.75:
                        end_matches.append(i)

            if end_matches:
                if end_ref_val is not None:
                    chosen = min(
                        end_matches,
                        key=lambda idx: abs(float(transcript_segments[idx].get('end', 0)) - end_ref_val),
                    )
                else:
                    # Prefer the last occurrence inside the max duration: the AI's end_text
                    # may repeat earlier, and the first match can cut the story in half.
                    valid = [
                        idx for idx in end_matches
                        if float(transcript_segments[idx].get('end', 0)) - final_start_time <= tempo_maximo
                    ]
                    chosen = valid[-1] if valid else end_matches[-1]
                final_end_time = transcript_segments[chosen]['end']
            elif end_ref_val is not None:
                nearest = min(
                    transcript_segments,
                    key=lambda item: abs(float(item.get('end', 0)) - end_ref_val),
                )
                final_end_time = nearest['end']
            
            # Fallback End Time
            if final_end_time == -1:
                 final_end_time = final_start_time + tempo_minimo 
            
            # A duracao final e ajustada em _snap_segments_to_sentences, sempre em
            # frases completas. Cortar ou esticar aqui no meio da frase era o que
            # deixava os cortes sem nexo.
            if final_end_time <= final_start_time:
                final_end_time = final_start_time + tempo_minimo

            duration = final_end_time - final_start_time

            # Construct Final Segment
            raw_title = str(seg.get('title') or 'Viral Segment').strip()
            hashtags = re.findall(r"#[\wÀ-ÿ]+", raw_title)
            for tag in re.findall(r"#[\wÀ-ÿ]+", str(seg.get('hashtags') or '')):
                if tag not in hashtags:
                    hashtags.append(tag)
            clean_title = re.sub(r"\s*#[\wÀ-ÿ]+", "", raw_title)
            clean_title = re.sub(r"\s{2,}", " ", clean_title).strip(" -–—")
            if len(clean_title) > 110:
                clean_title = clean_title[:107].rsplit(" ", 1)[0].rstrip(" ,.;-") + "..."
            if not clean_title:
                clean_title = raw_title or "Viral Segment"

            processed_segments.append({
                "title": clean_title,
                "hashtags": hashtags,
                "start_time": final_start_time,
                "end_time": final_end_time,
                "hook": "",
                "hook_line": seg.get('hook_line', ''),
                "reasoning": seg.get('reasoning', ''),
                "description": seg.get('reasoning', ''),
                "emotion": seg.get('emotion', ''),
                "score": _safe_score(seg.get('score')),
                "duration": duration,
                "_start_text": seg.get('start_text', ''),
                "_end_text": seg.get('end_text', ''),
            })

        except Exception as e:
            print(f"[WARN] Error processing segment {seg}: {e}")
            continue

    # Deduplication
    processed_segments = _snap_segments_to_sentences(
        processed_segments,
        transcript_segments,
        tempo_minimo,
        tempo_maximo,
    )

    # O hook e a primeira frase realmente falada dentro do corte, nao o titulo.
    # Recalculado depois do snap para refletir o audio que o cliente vai ouvir.
    hook_blocks = _build_sentence_blocks(transcript_segments)
    for segment in processed_segments:
        try:
            hook_index = _block_index_at_time(hook_blocks, float(segment.get("start_time", 0) or 0))
            if hook_index is None:
                continue
            hook_text = re.sub(r"\s+", " ", str(hook_blocks[hook_index].get("text") or "")).strip()
            if hook_text:
                segment["hook"] = hook_text
                segment["hook_line"] = hook_text
        except Exception:
            continue

    unique_segments = []
    processed_segments.sort(key=lambda x: int(x.get('score', 0)), reverse=True)
    
    for candidate in processed_segments:
        is_dup = False
        for existing in unique_segments:
            s1, e1 = candidate['start_time'], candidate['end_time']
            # Simple float equality isn't safe, but max/min handles it
            s2, e2 = existing['start_time'], existing['end_time']
            
            overlap_start = max(s1, s2)
            overlap_end = min(e1, e2)
            
            if overlap_end > overlap_start:
                intersection = overlap_end - overlap_start
                if intersection > 5: # more than 5 seconds overlap
                    is_dup = True
                    print(f"[DEBUG] Dropping overlap: '{candidate.get('title')}' ({s1:.1f}-{e1:.1f}) overlaps with '{existing.get('title')}' ({s2:.1f}-{e2:.1f}) by {intersection:.1f}s")
                    break
        if not is_dup:
            unique_segments.append(candidate)

    all_segments = unique_segments
    print(f"[DEBUG] Finished processing. {len(all_segments)} segments valid.")

    if output_count and len(all_segments) > output_count:
        print(f"Filtrando os top {output_count} segmentos de {len(all_segments)} candidatos encontrados nos chunks.")
        all_segments = all_segments[:output_count]
    elif output_count and len(all_segments) < output_count:
        print(f"[AVISO] A IA retornou {len(all_segments)} corte(s) valido(s), menos que os {output_count} solicitados.")

    final_result = {"segments": all_segments}
    
    # Validação básica de que temos start_time
    validated_segments = []
    for seg in final_result['segments']:
        if 'start_time' in seg:
             validated_segments.append(seg)
    
    final_result['segments'] = validated_segments
    
    return final_result


def create(num_segments, viral_mode, themes, tempo_minimo, tempo_maximo, ai_mode="manual", api_key=None, project_folder="tmp", chunk_size_arg=None, model_name_arg=None):
    quantidade_de_virals = num_segments

    # 1. Load Transcript
    transcript_segments = load_transcript(project_folder)

    # 2. Pre-process Content
    formatted_content = preprocess_transcript_for_ai(transcript_segments)
    content = formatted_content

    # Load Config and Prompt
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, 'api_config.json')
    prompt_path = os.path.join(base_dir, 'prompt.txt')

    config = {
        "selected_api": "gemini",
        "gemini": {
            "api_key": "",
            "model": "gemini-2.5-flash",
            "chunk_size": 15000
        },
        "g4f": {
            "chunk_size": 2000
        }
    }

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8-sig') as f:
                loaded_config = json.load(f)
                if "gemini" in loaded_config: config["gemini"].update(loaded_config["gemini"])
                if "g4f" in loaded_config: config["g4f"].update(loaded_config["g4f"])
                if "selected_api" in loaded_config: config["selected_api"] = loaded_config["selected_api"]
        except Exception as e:
            print(f"Erro ao ler api_config.json: {e}")

    # Config Vars
    current_chunk_size = 15000
    model_name = ""
    
    if ai_mode == "gemini":
        cfg_chunk = config["gemini"].get("chunk_size", 250000)
        current_chunk_size = chunk_size_arg if chunk_size_arg and int(chunk_size_arg) > 0 else cfg_chunk
        cfg_model = config["gemini"].get("model", "gemini-2.5-flash")
        model_name = model_name_arg if model_name_arg else cfg_model
        if not api_key: api_key = config["gemini"].get("api_key", "")
            
    elif ai_mode == "g4f":
        cfg_chunk = config["g4f"].get("chunk_size", 25000)
        current_chunk_size = chunk_size_arg if chunk_size_arg and int(chunk_size_arg) > 0 else cfg_chunk
        cfg_model = config["g4f"].get("model", "gpt-4o-mini")
        model_name = model_name_arg if model_name_arg else cfg_model

    elif ai_mode == "local":
        current_chunk_size = chunk_size_arg if chunk_size_arg and int(chunk_size_arg) > 0 else 15000
        model_name = model_name_arg if model_name_arg else ""

    if ai_mode == "gemini":
        if not HAS_GEMINI:
            print("[ERRO] A biblioteca google-generativeai nao esta instalada.")
            print("[DICA] Rode o instalador ou use o backend G4F.")
            return {"segments": []}
        if not (str(api_key or "").strip() or str(config["gemini"].get("api_key") or "").strip()):
            print("\n[ERRO] Gemini API key nao configurada.")
            print("[DICA] Cole sua chave no campo 'Gemini API Key' ou selecione o backend G4F.")
            return {"segments": []}
    if ai_mode == "g4f" and not HAS_G4F:
        print("[ERRO] A biblioteca g4f nao esta instalada.")
        print("[DICA] Rode o instalador ou selecione outro backend de IA.")
        return {"segments": []}

    system_prompt_template = ""
    if os.path.exists(prompt_path):
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt_template = f.read()
    else:
        print("Aviso: prompt.txt não encontrado. Usando prompt interno.")
        system_prompt_template = """You are a World-Class Viral Video Editor.
{context_instruction}
Analyze the transcript below with time tags (XXs). Find {amount} viral segments.
Constraints: Each segment MUST be between {min_duration} seconds and {max_duration} seconds.
IMPORTANT: Output "Title", "Hook", and "Reasoning" in the SAME LANGUAGE as the transcript (e.g., if transcript is Portuguese, output Portuguese).
TRANSCRIPT:
{transcript_chunk}
OUTPUT JSON ONLY:
{json_template}"""


    json_template = '''
            { "segments" :
                [
                    {
                        "start_text": "First 8-15 words of the opening sentence, copied exactly",
                        "end_text": "Last 8-15 words of the closing sentence, copied exactly",
                        "start_time_ref": "Value of closest (XXs) tag",
                        "end_time_ref": "Value of closest (XXs) tag at the END of the segment",
                        "hook_line": "The exact opening sentence of the cut, copied from the transcript",
                        "title": "Short headline, max 70 chars, NO hashtags, same language as transcript",
                        "hashtags": "#tag1 #tag2 #tag3",
                        "reasoning": "Why this cut works, in the same language as the transcript",
                        "emotion": "laughter|shock|emotion|conflict|revelation|inspiration",
                        "score": "Integer 0-100, honest and varied (90+ only for exceptional cuts)"
                    }
                ]
            }
        '''

    # Chunking Inteligente e Adaptativo
    content_len = len(content)

    # Se estiver usando Gemini e o transcript tiver ate 350.000 caracteres (~4 a 5 horas de audio),
    # processa tudo em 1 unico bloco! Isso evita cortes fatiados no meio de historias e garante contexto completo.
    if ai_mode == "gemini" and content_len <= 350000 and (not chunk_size_arg or int(chunk_size_arg) >= 200000):
        chunk_size = content_len
        overlap_size = 0
        chunks = [content]
        print(f"[INFO] Gemini (Contexto Amplo): Analisando video completo em chamada unica ({content_len} caracteres).")
    else:
        chunk_size = int(current_chunk_size)
        # Overlap generoso (minimo de 4.000 caracteres ou 20%) para que nenhuma historia de 60s a 120s fique cortada na borda
        overlap_size = max(4000, int(chunk_size * 0.20))
        chunks = []
        start = 0
        print(f"[DEBUG] Chunking content (Tamanho: {content_len}) com Chunk Size: {chunk_size} e Overlap: {overlap_size}")

        while start < content_len:
            end = min(start + chunk_size, content_len)
            if end < content_len:
                last_space = content.rfind(' ', start, end)
                if last_space != -1 and last_space > start:
                    end = last_space
            chunk_text = content[start:end]
            if chunk_text.strip():
                chunks.append(chunk_text)
            if end >= content_len:
                break
            next_start = max(start + 1, end - overlap_size)
            safe_space = content.rfind(' ', start, next_start)
            if safe_space != -1:
                start = safe_space + 1
            else:
                start = next_start

    # Pede mais candidatos do que o cliente quer receber. Assim, sobreposicoes,
    # duplicatas e trechos fracos podem ser descartados sem faltar corte no final.
    ask_amount = max(quantidade_de_virals + 3, int(quantidade_de_virals * 1.6) + 1)
    if viral_mode:
        virality_instruction = f"""analyze the segment for potential virality and identify {ask_amount} candidate viral segments from the transcript (aiming for at least {quantidade_de_virals} top quality cuts)"""
    else:
        virality_instruction = f"""analyze the segment for potential virality and identify {ask_amount} the best parts based on the list of themes {themes}."""

    output_texts = []
    for i, chunk in enumerate(chunks):
        context_instruction = ""
        if len(chunks) > 1:
            context_instruction = f"Part {i+1} of {len(chunks)}. "
        
        try:
            prompt = system_prompt_template.format(
                context_instruction=context_instruction,
                virality_instruction=virality_instruction,
                min_duration=tempo_minimo,
                max_duration=tempo_maximo,
                transcript_chunk=chunk,
                json_template=json_template,
                amount=ask_amount,
                keep=quantidade_de_virals
            )
        except KeyError as e:
            prompt = system_prompt_template
            prompt = prompt.replace("{context_instruction}", context_instruction)
            prompt = prompt.replace("{virality_instruction}", virality_instruction)
            prompt = prompt.replace("{min_duration}", str(tempo_minimo))
            prompt = prompt.replace("{max_duration}", str(tempo_maximo))
            prompt = prompt.replace("{transcript_chunk}", chunk)
            prompt = prompt.replace("{json_template}", json_template)
            prompt = prompt.replace("{amount}", str(ask_amount))
            prompt = prompt.replace("{keep}", str(quantidade_de_virals))

        output_texts.append(prompt)

    try:
        full_prompt_path = os.path.join(project_folder, "prompt_full.txt")
        full_prompt = system_prompt_template
        full_prompt = full_prompt.replace("{context_instruction}", "Full Video Transcript Analysis")
        full_prompt = full_prompt.replace("{virality_instruction}", virality_instruction)
        full_prompt = full_prompt.replace("{min_duration}", str(tempo_minimo))
        full_prompt = full_prompt.replace("{max_duration}", str(tempo_maximo))
        full_prompt = full_prompt.replace("{transcript_chunk}", content) 
        full_prompt = full_prompt.replace("{json_template}", json_template)
        full_prompt = full_prompt.replace("{amount}", str(ask_amount))
        full_prompt = full_prompt.replace("{keep}", str(quantidade_de_virals))
        
        with open(full_prompt_path, "w", encoding="utf-8") as f:
            f.write(full_prompt)
    except Exception as e:
        print(f"[WARN] Could not save prompt_full.txt: {e}")

    all_raw_segments = []

    print(f"Processando {len(output_texts)} chunks usando modo: {ai_mode.upper()}")

    local_llm_instance = None
    if ai_mode == "local":
        if not HAS_LLAMA_CPP:
            print("Error: llama-cpp-python not installed. Please install it to use Local mode.")
            return {"segments": []}
            
        models_dir = os.path.join(base_dir, 'models')
        model_path = os.path.join(models_dir, model_name)
        if not os.path.exists(model_path):
             if os.path.exists(model_name):
                 model_path = model_name
             else:
                 print(f"Error: Model not found at {model_path}")
                 return {"segments": []}
        
        print(f"[INFO] Loading Local Model: {os.path.basename(model_path)} (This may take a while)...")
        try:
            local_llm_instance = Llama(
                model_path=model_path,
                n_gpu_layers=-1, 
                n_ctx=8192,
                verbose=False
            )
        except Exception as e:
            print(f"Failed to load model: {e}")
            return {"segments": []}

    for i, prompt in enumerate(output_texts):
        response_text = ""
        manual_prompt_path = os.path.join(project_folder, f"prompt_part_{i+1}.txt")
        try:
            with open(manual_prompt_path, "w", encoding="utf-8") as f:
                f.write(prompt)
        except Exception as e:
            print(f"[ERRO] Falha ao salvar prompt.txt: {e}")
        
        if ai_mode == "manual":
            print(f"\n[INFO] O prompt foi salvo em: {manual_prompt_path}")
            print("\n" + "="*60)
            print(f"CHUNK {i+1}/{len(output_texts)}")
            print("="*60)
            print("COPIE O PROMPT ABAIXO (OU DO ARQUIVO GERADO) E COLE NA SUA IA PREFERIDA:")
            print("-" * 20)
            print(prompt)
            print("-" * 20)
            print("="*60)
            print("Cole o JSON de resposta abaixo e pressione ENTER.")
            print("Dica: Se o JSON tiver múltiplas linhas, tente colar tudo de uma vez ou minificado.")
            print("Se preferir, digite 'file' para ler de um arquivo 'tmp/response.json'.")
            
            user_input = input("JSON ou 'file': ")
            
            if user_input.lower() == 'file':
                try:
                    response_json_path = os.path.join(project_folder, 'response.json')
                    with open(response_json_path, 'r', encoding='utf-8') as rf:
                        response_text = rf.read()
                except FileNotFoundError:
                    print(f"Arquivo {response_json_path} não encontrado.")
            else:
                response_text = user_input
                if response_text.strip().startswith("{") and not response_text.strip().endswith("}"):
                    print("Parece incompleto. Cole o resto e dê Enter (ou Ctrl+C para cancelar):")
                    try:
                        rest = sys.stdin.read() 
                        response_text += rest
                    except:
                        pass

        elif ai_mode == "gemini":
            print(f"Enviando chunk {i+1} para o Gemini (Model: {model_name})...")
            response_text = call_gemini(prompt, api_key, model_name=model_name)
        elif ai_mode == "g4f":
            print(f"Enviando chunk {i+1} para o G4F (Model: {model_name})...")
            response_text = call_g4f(prompt, model_name=model_name)
        elif ai_mode == "local" and local_llm_instance:
            print(f"Processing chunk {i+1} with Local LLM...")
            try:
                output = local_llm_instance.create_chat_completion(
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that outputs only JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=4096,
                    temperature=0.7
                )
                response_text = output['choices'][0]['message']['content']
            except Exception as e:
                print(f"Error evaluating local model: {e}")
                response_text = "{}"

        # --- Save RAW Response for Debugging ---
        try:
            raw_response_path = os.path.join(project_folder, f"response_raw_part_{i+1}.txt")
            with open(raw_response_path, "w", encoding="utf-8") as f:
                f.write(response_text)
            print(f"[DEBUG] Raw response saved to: {raw_response_path}")
        except Exception as e:
            print(f"[WARN] Failed to save raw response: {e}")

        # Processar resposta
        try:
            data = clean_json_response(response_text)
            chunk_segments = data.get("segments", [])
            print(f"Encontrados {len(chunk_segments)} segmentos neste chunk.")
            all_raw_segments.extend(chunk_segments)
        except json.JSONDecodeError:
            print(f"Erro: Resposta inválida.")
        except Exception as e:
            print(f"Erro desconhecido ao processar chunk: {e}")

    # MODO DE RESGATE ADAPTATIVO: se nenhum segmento foi encontrado pelos chunks normais
    if not all_raw_segments:
        print("\n" + "="*60)
        print("[MODO DE RESGATE] Nenhum corte detectado nos chunks iniciais.")
        print("[MODO DE RESGATE] Ativando analise adaptativa de alta sensibilidade...")
        print("="*60 + "\n")
        
        # Usa um trecho representativo (ate 180.000 caracteres)
        rescue_chunk = content[:180000] if len(content) > 180000 else content
        
        rescue_prompt = f"""You are a senior short-form editor.
Analyze this transcript with timestamps (XXs) and identify {ask_amount} candidate moments that work as complete, standalone stories (the best {quantidade_de_virals} will be kept).
Each segment must be between {tempo_minimo}s and {tempo_maximo}s.
CRITICAL: Do NOT return an empty list. If there is no explosive moment, pick the clearest story, insight or argument.
Start on the first word of a complete sentence that names its subject, and end on the last word of a sentence that delivers the payoff. Never start or end mid-sentence.
start_text must be the first 8-15 words of the opening sentence, copied exactly. end_text must be the last 8-15 words of the closing sentence, copied exactly.
hook_line must be the exact opening sentence of the cut, copied from the transcript, not a headline.
Output title, hook_line and reasoning in the same language as the transcript.

TRANSCRIPT:
{rescue_chunk}

OUTPUT VALID JSON ONLY:
{{
  "segments": [
    {{
      "start_time_ref": "(XXs)",
      "end_time_ref": "(XXs)",
      "start_text": "First 8-15 words of the opening sentence, copied exactly",
      "end_text": "Last 8-15 words of the closing sentence, copied exactly",
      "hook_line": "Exact opening sentence, copied from the transcript",
      "title": "Short headline, max 70 chars, no hashtags",
      "hashtags": "#tag1 #tag2 #tag3",
      "reasoning": "Why this cut works",
      "score": "Integer 0-100, honest and varied"
    }}
  ]
}}"""
        rescue_resp = ""
        try:
            if ai_mode == "gemini":
                rescue_resp = call_gemini(rescue_prompt, api_key, model_name=model_name)
            elif ai_mode == "g4f":
                rescue_resp = call_g4f(rescue_prompt, model_name=model_name)
            elif ai_mode == "local" and local_llm_instance:
                out = local_llm_instance.create_chat_completion(
                    messages=[{"role": "user", "content": rescue_prompt}],
                    max_tokens=4096,
                    temperature=0.7
                )
                rescue_resp = out['choices'][0]['message']['content']
        except Exception as e_res:
            print(f"[MODO DE RESGATE] Erro na chamada da IA: {e_res}")

        if rescue_resp:
            rescue_data = clean_json_response(rescue_resp)
            rescued_segs = rescue_data.get("segments", [])
            if rescued_segs:
                print(f"[MODO DE RESGATE] Sucesso! Recuperados {len(rescued_segs)} corte(s)!")
                all_raw_segments.extend(rescued_segs)

    # Se a IA não retornou nada, NÃO gera cortes aleatórios.
    # O fallback antigo cortava o vídeo em pontos fixos e entregava conteúdo desconexo.
    if not all_raw_segments:
        print("\n" + "=" * 60)
        print("[ERRO] A IA nao retornou nenhum corte valido.")
        print("[ERRO] Nenhum corte sera gerado para nao entregar videos desconexos.")
        if LAST_AI_ERROR:
            print(f"[ERRO IA] {LAST_AI_ERROR}")
        print("[DICA] Verifique a chave e o modelo da IA (Gemini/G4F) e tente novamente.")
        print("=" * 60 + "\n")
        return {"segments": []}

    # Call the alignment / processing logic
    return process_segments(
        all_raw_segments, 
        transcript_segments, 
        tempo_minimo, 
        tempo_maximo, 
        output_count=quantidade_de_virals
    )
