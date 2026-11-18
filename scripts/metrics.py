"""
Métricas para a Fábrica dos Cortes.

Duas fontes de dados:
1. YouTube — via yt-dlp (sem login). Puxa views, likes, comentários, duração,
   data de publicação, título de todos os vídeos de um canal ou playlist.
2. TikTok — via CSV exportado do TikTok Analytics Studio
   (TikTok Studio -> Analytics -> Exportar Dados -> Relatório de Desempenho).

Gera um relatório HTML com:
- Ranking de vídeos por views / engajamento
- Duração ideal estimada (média dos top 10)
- Recomendações por tipo de métrica
- Horário ideal de postagem

Uso direto:
    python -m scripts.metrics --channel "URL_DO_CANAL"
    python -m scripts.metrics --tiktok-csv "caminho/do/report.csv"
    python -m scripts.metrics --channel ... --tiktok-csv ...

O módulo é tolerante a falhas: cada vídeo/linha é processado
independentemente para que um dado inválido não quebre a análise toda.
"""

from __future__ import annotations

import csv
import datetime
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional

APP_ROOT = Path(__file__).resolve().parent.parent if "__file__" in globals() else Path("")
OUTPUT_DIR = APP_ROOT / "metrics_reports"
METRICS_CONFIG = APP_ROOT / "temp_metrics_config.json"

DEFAULT_CONFIG: dict = {
    "youtube_channels": [],       # Lista de URLs de canal ou playlists
    "tiktok_csv_paths": [],       # Lista de caminhos para CSVs do TikTok
    "min_views_filter": 0,        # Ignora vídeos com menos de N views
    "days_back": 90,              # Só considera vídeos nos últimos N dias
    "top_n_videos": 20,           # Quantos vídeos mostrar no ranking
    "output_html": True,          # Gerar relatório HTML
    "output_json": True,          # Também salvar JSON
}


def load_config(path: Optional[str] = None) -> dict:
    p = Path(path) if path else METRICS_CONFIG
    cfg = dict(DEFAULT_CONFIG)
    if p.is_file():
        try:
            with open(p, "r", encoding="utf-8-sig") as f:
                cfg.update(json.load(f))
        except Exception as e:
            print(f"[Metrics] Aviso: config {p} ilegível ({e})")
    return cfg


def save_config(cfg: dict, path: Optional[str] = None) -> None:
    p = Path(path) if path else METRICS_CONFIG
    with open(p, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)


# ──────────────────────────────────────────────────────────────────────────────
# YouTube via yt-dlp
# ──────────────────────────────────────────────────────────────────────────────

def _yt_has_ytdlp() -> bool:
    try:
        import yt_dlp  # noqa
        return True
    except ImportError:
        return False


def fetch_youtube_channel(channel_url: str, min_views: int = 0, days_back: int = 90,
                          cookies_file: Optional[str] = None) -> tuple[list, Optional[str]]:
    """
    Busca métricas de todos os vídeos de um canal/playlist via yt-dlp.

    Usa extração flat (metadados sem baixar). Retorna (videos, erro).
    Cada video: {title, url, views, likes, comments, duration, published}
    """
    if not _yt_has_ytdlp():
        return [], "yt-dlp não está instalado. Rode: pip install yt-dlp"

    try:
        import yt_dlp
    except ImportError as e:
        return [], f"Falha ao importar yt-dlp: {e}"

    # Se URL não for de canal/playlist, trata como vídeo único
    is_single = not re.search(r"(/channel/|/c/|/user/|/@|/playlist\?)", channel_url)

    ydl_opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "ignoreerrors": True,
        "noplaylist": False if not is_single else True,
        "youtube_include_dash_manifest": False,
        "extractor_args": {"youtube": {"player_client": ["web_safari", "mweb"]}},
    }

    # Cookies opcionais (melhora extração)
    if cookies_file and os.path.isfile(cookies_file):
        ydl_opts["cookiefile"] = str(cookies_file)

    videos: list[dict] = []
    error: Optional[str] = None

    cutoff = datetime.datetime.now() - datetime.timedelta(days=int(days_back))

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            entries = info.get("entries") or ([info] if info.get("id") else [])

            for e in entries:
                if not e:
                    continue
                video_id = e.get("id")
                if not video_id:
                    continue

                title = e.get("title") or "(sem título)"
                url = f"https://www.youtube.com/watch?v={video_id}"
                views = int(e.get("view_count") or 0)
                likes = int(e.get("like_count") or 0)
                comments = int(e.get("comment_count") or 0)

                duration = 0
                try:
                    duration = int(float(e.get("duration") or 0))
                except (ValueError, TypeError):
                    pass

                # Data de publicação
                published = None
                pub_raw = e.get("timestamp") or e.get("upload_date")
                if isinstance(pub_raw, (int, float)) and pub_raw:
                    published = datetime.datetime.fromtimestamp(pub_raw)
                elif isinstance(pub_raw, str) and len(pub_raw) == 8 and pub_raw.isdigit():
                    published = datetime.datetime.strptime(pub_raw, "%Y%m%d")

                # Filtro por data
                if published and int(days_back) > 0 and published < cutoff:
                    continue
                # Filtro por views
                if views < int(min_views):
                    continue

                videos.append({
                    "platform": "youtube",
                    "title": title,
                    "url": url,
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "duration": duration,
                    "published": published.isoformat() if published else None,
                })

    except Exception as e:
        error = f"Falha ao extrair {channel_url}: {e}"

    return videos, error


# ──────────────────────────────────────────────────────────────────────────────
# TikTok via CSV exportado
# ──────────────────────────────────────────────────────────────────────────────

# Colunas comuns nos CSVs do TikTok Analytics Studio (pt-BR e en/US)
_TIKTOK_ALIASES = {
    "views": ["views", "visualizações", "visualizacoes", "view_count", "views count", "plays"],
    "likes": ["likes", "curtidas", "like_count", "likes count"],
    "comments": ["comments", "comentários", "comentarios", "comment_count", "comments count"],
    "shares": ["shares", "compartilhamentos", "share count"],
    "saves": ["saves", "salvamentos", "bookmarks", "favorites"],
    "duration": ["duration", "duração", "duracao", "video length", "video duration"],
    "title": ["title", "título", "titulo", "video title", "post title", "description"],
    "published": ["published date", "data de publicação", "data de publicacao", "publish time",
                  "post date", "publication date", "date", "data"],
}


def _find_column(headers: list[str], names: list[str]) -> Optional[int]:
    h_lower = [str(h).strip().lower() for h in headers]
    for name in names:
        try:
            idx = h_lower.index(name.lower())
            return idx
        except ValueError:
            continue
    # Tenta correspondência parcial
    for i, h in enumerate(h_lower):
        for name in names:
            if name.lower() in h:
                return i
    return None


def _parse_int(value: Any) -> int:
    if value is None:
        return 0
    s = str(value).replace(",", "").replace(".", "").strip()
    s = re.sub(r"[^\d]", "", s)
    return int(s) if s else 0


def _parse_float(value: Any) -> float:
    if value is None:
        return 0.0
    s = str(value).replace(",", ".").replace(" ", "").strip()
    m = re.match(r"[\d\.]+", s)
    return float(m.group(0)) if m else 0.0


def _parse_duration_hms(value: Any) -> int:
    """Converte '0:15', '1:02:03', '00.12' etc em segundos."""
    s = str(value).strip()
    if not s:
        return 0
    m = re.match(r"(\d+):(\d+)(?::(\d+))?", s)
    if m:
        # Sem ":" → MM:SS (m.group(3) é None)
        if m.group(3) is None:
            # "0:38" → 0min 38sec
            mm = int(m.group(1))
            ss = int(m.group(2))
        else:
            # "1:02:03" → 1h 2min 3sec
            h = int(m.group(1))
            mm = int(m.group(2))
            ss = int(m.group(3))
            return h * 3600 + mm * 60 + ss
        return mm * 60 + ss
    # "12.34" segundos
    m2 = re.match(r"(\d+)\.(\d+)", s)
    if m2:
        return int(m2.group(1))
    # só número → trata como segundos
    m3 = re.match(r"\d+", s)
    return int(m3.group(0)) if m3 else 0


def _parse_date(value: Any) -> Optional[datetime.datetime]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    formats = [
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
        "%m/%d/%Y %H:%M:%S", "%m/%d/%Y", "%Y/%m/%d", "%Y/%m/%d %H:%M",
    ]
    for fmt in formats:
        try:
            return datetime.datetime.strptime(s, fmt)
        except ValueError:
            continue
    # Timestamp numérico
    try:
        f = float(s)
        if f > 1e12:
            return datetime.datetime.fromtimestamp(f / 1000)
        if f > 1e9:
            return datetime.datetime.fromtimestamp(f)
    except ValueError:
        pass
    return None


def parse_tiktok_csv(csv_path: str) -> tuple[list, Optional[str]]:
    """Lê um CSV exportado do TikTok Analytics e retorna lista de vídeos."""
    if not os.path.isfile(csv_path):
        return [], f"CSV não encontrado: {csv_path}"

    videos: list[dict] = []
    error: Optional[str] = None

    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)
    except UnicodeDecodeError:
        try:
            with open(csv_path, newline="", encoding="latin-1") as f:
                reader = csv.reader(f)
                rows = list(reader)
        except Exception as e:
            return [], f"Falha ao ler CSV: {e}"
    except Exception as e:
        return [], f"Falha ao ler CSV: {e}"

    if not rows:
        return [], "CSV vazio"

    headers = rows[0]
    # Se o CSV tiver múltiplas linhas de cabeçalho (TikTok costuma ter), procura
    # a linha que contém colunas tipo 'Views'
    header_row = 0
    for i, row in enumerate(rows[:10]):
        joined = " ".join(str(c) for c in row).lower()
        if any(a in joined for a in ["views", "visualiza", "likes", "curtidas"]):
            header_row = i
            break

    headers = rows[header_row]
    data_rows = rows[header_row + 1:]

    col_views = _find_column(headers, _TIKTOK_ALIASES["views"])
    col_likes = _find_column(headers, _TIKTOK_ALIASES["likes"])
    col_comments = _find_column(headers, _TIKTOK_ALIASES["comments"])
    col_shares = _find_column(headers, _TIKTOK_ALIASES["shares"])
    col_saves = _find_column(headers, _TIKTOK_ALIASES["saves"])
    col_duration = _find_column(headers, _TIKTOK_ALIASES["duration"])
    col_title = _find_column(headers, _TIKTOK_ALIASES["title"])
    col_published = _find_column(headers, _TIKTOK_ALIASES["published"])

    if col_views is None:
        return [], "CSV do TikTok não tem coluna de Views reconhecível"

    for row in data_rows:
        if not row or not any(str(c).strip() for c in row):
            continue

        def _cell(idx: Optional[int]) -> str:
            if idx is None or idx >= len(row):
                return ""
            return row[idx].strip()

        published = _parse_date(_cell(col_published))
        videos.append({
            "platform": "tiktok",
            "title": _cell(col_title) or "(vídeo)",
            "url": "",
            "views": _parse_int(_cell(col_views)),
            "likes": _parse_int(_cell(col_likes)),
            "comments": _parse_int(_cell(col_comments)),
            "shares": _parse_int(_cell(col_shares)),
            "saves": _parse_int(_cell(col_saves)),
            "duration": _parse_duration_hms(_cell(col_duration)),
            "published": published.isoformat() if published else None,
        })

    return videos, error


# ──────────────────────────────────────────────────────────────────────────────
# Análise e relatório
# ──────────────────────────────────────────────────────────────────────────────

def _engagement_rate(v: dict) -> float:
    """Taxa de engajamento: (likes + comments + shares) / views."""
    views = v.get("views", 0)
    if views <= 0:
        return 0.0
    return (v.get("likes", 0) + v.get("comments", 0) + v.get("shares", 0)) / views


def analyze(videos: list[dict], top_n: int = 20) -> dict:
    """Analisa métricas e gera recomendações."""
    videos = [v for v in videos if v.get("views", 0) > 0]
    if not videos:
        return {"ok": False, "reason": "Nenhum vídeo com views > 0"}

    videos_sorted = sorted(videos, key=lambda v: v["views"], reverse=True)
    by_engagement = sorted(videos, key=_engagement_rate, reverse=True)
    top = videos_sorted[:max(1, top_n)]

    # Engajamento médio global
    avg_engagement = sum(_engagement_rate(v) for v in videos) / len(videos)

    # Duração ideal: média das durações dos top-10 por views
    durations = [v["duration"] for v in top[:10] if v["duration"] > 0]
    ideal_duration = sum(durations) / len(durations) if durations else None

    # Horário ideal: agrupa por hora de publicação dos top vídeos
    hour_counts: dict[int, int] = {}
    top_with_time = []
    for v in videos_sorted[:50]:
        if v.get("published"):
            # Pegamos a hora da publicação de forma mockável no relatório
            pass
        top_with_time.append(v)

    # Recomendações simples
    recs: list[str] = []
    top_views = top[0]["views"] if top else 1
    for v in videos[:20]:
        if v["views"] > 0 and v["views"] / top_views < 0.1:
            recs.append(f"'{v['title'][:40]}' está muito abaixo do seu melhor: {v['views']} vs {top_views} views.")
            break

    if avg_engagement < 0.03:
        recs.append("Engajamento médio abaixo de 3%: aposte em legendas mais chamativas e gancho nos primeiros 3 segundos.")
    else:
        recs.append(f"Engajamento médio sólido ({avg_engagement:.1%}): continue investindo em cortes com gancho forte.")

    if ideal_duration:
        if ideal_duration < 45:
            recs.append(f"Duração ideal estimada: ~{ideal_duration:.0f}s (conteúdo curto performa melhor no seu perfil).")
        else:
            recs.append(f"Duração ideal estimada: ~{ideal_duration:.0f}s (público consome conteúdos mais longos).")

    return {
        "ok": True,
        "total_videos": len(videos),
        "total_views": sum(v["views"] for v in videos),
        "avg_engagement": avg_engagement,
        "ideal_duration": ideal_duration,
        "top_by_views": top,
        "top_by_engagement": by_engagement[:top_n],
        "lowest": videos_sorted[-5:],
        "recommendations": recs,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Relatório HTML
# ──────────────────────────────────────────────────────────────────────────────

def _fmt_num(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1e6:.1f}M"
    if n >= 1_000:
        return f"{n/1e3:.1f}K"
    return str(n)


def _fmt_duration(sec: int) -> str:
    if not sec or sec <= 0:
        return "-"
    return f"{sec//60}:{sec%60:02d}"


def generate_html(report: dict, source_desc: str = "") -> str:
    """Gera o relatório HTML completo."""
    from html import escape

    status = report.get("ok")
    if not status:
        return f"<div class='metrics-error'>Sem dados suficientes: {escape(str(report.get('reason', '')))}</div>"

    rows = ""
    for i, v in enumerate(report["top_by_views"], start=1):
        title = escape(v.get("title", ""))[:60]
        engagement = _engagement_rate(v) * 100
        rows += (
            f"<tr><td>{i}</td><td>{title}</td>"
            f"<td>{_fmt_num(v.get('views',0))}</td>"
            f"<td>{_fmt_num(v.get('likes',0))}</td>"
            f"<td>{_fmt_num(v.get('comments',0))}</td>"
            f"<td>{engagement:.1f}%</td>"
            f"<td>{_fmt_duration(v.get('duration',0))}</td></tr>"
        )

    total_views = _fmt_num(report["total_views"])
    avg_eng = report["avg_engagement"] * 100
    total = report["total_videos"]

    rec_li = "".join(
        f"<li>{escape(str(r))}</li>" for r in report.get("recommendations", [])
    )

    hour_html = ""
    # Topo por posição do relatório (simula heatmap simples)
    top_hourly = {}
    for v in report["top_by_views"][:30]:
        pub = v.get("published")
        if not pub:
            continue
        try:
            hour = datetime.datetime.fromisoformat(pub).hour
        except Exception:
            continue
        top_hourly[hour] = top_hourly.get(hour, 0) + 1
    if top_hourly:
        best_hour = max(top_hourly, key=top_hourly.get)
        hour_html = (
            f"<div class='m-card'><h3>Horário de postagem</h3>"
            f"<p>Seus vídeos de maior sucesso tendem a ser publicados por volta das "
            f"<b>{best_hour:02d}:00</b>. Considere agendar os cortes para esse horário.</p></div>"
        )

    best_duration_html = ""
    if report.get("ideal_duration"):
        best_duration_html = (
            f"<div class='m-card'><h3>Duração ideal</h3>"
            f"<p>A duração média dos seus cortes de destaque é de "
            f"<b>{_fmt_duration(int(report['ideal_duration']))}</b>. "
            f"Crie cortes nessa faixa para manter a retenção.</p></div>"
        )

    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Relatório de Métricas — Fábrica dos Cortes</title>
<style>
:root {{ color-scheme: light; }}
* {{ box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', system-ui, sans-serif; background:#f5f5f0; color:#1a1a1a; margin:0; padding:24px; }}
.wrap {{ max-width: 1000px; margin: 0 auto; }}
h1 {{ font-size: 1.5rem; margin: 0 0 4px; }}
.sub {{ color: #666; margin-bottom: 16px; }}
.grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(200px,1fr)); gap:12px; margin:16px 0; }}
.m-card {{ background:#fff; border:1px solid #e2e2dd; border-radius:12px; padding:16px; }}
.metric {{ font-size: 1.6rem; font-weight:700; }}
.metric-label {{ color:#666; font-size:.85rem; }}
table {{ width:100%; border-collapse: collapse; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,.05); }}
th,td {{ padding:10px 12px; text-align:left; border-bottom:1px solid #eee; font-size:.9rem; }}
th {{ background:#fafaf7; color:#555; font-weight:600; }}
td {{ white-space: nowrap; overflow:hidden; text-overflow:ellipsis; max-width:280px; }}
.recs {{ background:#fff7ed; border:1px solid #fed7aa; border-radius:12px; padding:16px; margin-top:16px; }}
.recs h3 {{ margin-top:0; }}
.recs li {{ margin-bottom:8px; line-height:1.5; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>📊 Relatório de Métricas</h1>
  <div class="sub">{escape(source_desc)}</div>

  <div class="grid">
    <div class="m-card"><div class="metric">{_fmt_num(report['total_views'])}</div><div class="metric-label">Views totais</div></div>
    <div class="m-card"><div class="metric">{total}</div><div class="metric-label">Vídeos analisados</div></div>
    <div class="m-card"><div class="metric">{avg_eng:.1f}%</div><div class="metric-label">Engajamento médio</div></div>
    <div class="m-card"><div class="metric">{_fmt_duration(int(report['ideal_duration'])) if report.get('ideal_duration') else '-'}</div><div class="metric-label">Duração ideal</div></div>
  </div>

  <div style="display:flex; gap:12px; flex-wrap:wrap; margin-bottom:16px;">
    {best_duration_html}
    {hour_html}
  </div>

  <h2>Top vídeos por views</h2>
  <table>
    <thead><tr><th>#</th><th>Título</th><th>Views</th><th>Likes</th><th>Comentários</th><th>Engaj.</th><th>Duração</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>

  <div class="recs">
    <h3>💡 Recomendações</h3>
    <ul>{rec_li}</ul>
  </div>
</div>
</body>
</html>
"""


# ──────────────────────────────────────────────────────────────────────────────
# Orquestração
# ──────────────────────────────────────────────────────────────────────────────

def run_metrics(
    channels: Optional[list] = None,
    tiktok_csvs: Optional[list] = None,
    config: Optional[dict] = None,
    cookies_file: Optional[str] = None,
) -> tuple[Optional[str], str]:
    """
    Executa a coleta de métricas e gera o relatório.

    Returns:
        (html_path, status_message)
    """
    if config is None:
        config = load_config()

    channels = channels if channels is not None else config.get("youtube_channels", [])
    tiktok_csvs = tiktok_csvs if tiktok_csvs is not None else config.get("tiktok_csv_paths", [])
    min_views = int(config.get("min_views_filter", 0))
    days_back = int(config.get("days_back", 90))
    top_n = int(config.get("top_n_videos", 20))

    all_videos: list = []
    errors: list[str] = []

    # YouTube
    for ch in channels:
        vids, err = fetch_youtube_channel(ch, min_views, days_back, cookies_file)
        if vids:
            all_videos.extend(vids)
        if err:
            errors.append(err)

    # TikTok
    for csv_path in tiktok_csvs:
        vids, err = parse_tiktok_csv(csv_path)
        if vids:
            all_videos.extend(vids)
        if err:
            errors.append(err)

    if not all_videos:
        msg = "Nenhum dado coletado."
        if errors:
            msg += " Erros: " + "; ".join(errors)
        return None, msg

    report = analyze(all_videos, top_n=top_n)

    OUT = OUTPUT_DIR / "metrics_report.html"
    try:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        source_desc = f"{len(channels)} canais YouTube · {len(tiktok_csvs)} export CSV TikTok"
        html = generate_html(report, source_desc)
        with open(OUT, "w", encoding="utf-8") as f:
            f.write(html)

        if config.get("output_json", True):
            json_path = OUTPUT_DIR / "metrics_data.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump({"report": report, "videos": all_videos}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        return None, f"Falha ao gerar relatório: {e}"

    status = f"✅ Analisados {report.get('total_videos', len(all_videos))} vídeos "
    status += f"({_fmt_num(report.get('total_views', 0))} views totais)."
    if errors:
        status += " Avisos: " + "; ".join(errors[:3])

    return str(OUT), status


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Fábrica dos Cortes — Métricas TikTok/YouTube"
    )
    parser.add_argument("--channel", "-c", action="append", help="URL de canal/playlist do YouTube")
    parser.add_argument("--tiktok-csv", "-t", action="append", help="Caminho para CSV do TikTok Analytics")
    parser.add_argument("--min-views", type=int, default=0)
    parser.add_argument("--days-back", type=int, default=90)
    parser.add_argument("--top-n", type=int, default=20)
    args = parser.parse_args()

    cfg = load_config()
    if args.min_views:
        cfg["min_views_filter"] = args.min_views
    if args.days_back:
        cfg["days_back"] = args.days_back
    if args.top_n:
        cfg["top_n_videos"] = args.top_n

    channels = args.channel or cfg.get("youtube_channels", [])
    tiktok_csvs = args.tiktok_csv or cfg.get("tiktok_csv_paths", [])

    html_path, status = run_metrics(channels, tiktok_csvs, cfg)
    print(status)
    if html_path:
        print(f"Relatório: {html_path}")


if __name__ == "__main__":
    main()
