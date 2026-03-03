import os
import sys

# webui/header.py — Forja Viral (client-facing header)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKING_DIR = os.path.dirname(CURRENT_DIR)
if WORKING_DIR not in sys.path:
    sys.path.append(WORKING_DIR)

from i18n.i18n import I18nAuto
i18n = I18nAuto()

# Keep badges var for compatibility (some app.py tries gr.HTML(header.badges))
badges = ""

description = r"""
<style>
  :root{
    --fv-bg:#0f1115;
    --fv-panel:rgba(255,255,255,.04);
    --fv-border:rgba(255,255,255,.10);
    --fv-text:rgba(255,255,255,.96);
    --fv-muted:rgba(255,255,255,.72);
    --fv-brand1:#ff5c00;
    --fv-brand2:#ff004c;
  }

  .fv-hero{
    margin: 10px 0 14px 0;
    padding: 16px 16px;
    border-radius: 18px;
    border: 1px solid var(--fv-border);
    background: linear-gradient(135deg, rgba(255,92,0,.14), rgba(255,0,76,.12));
    box-shadow: 0 14px 36px rgba(0,0,0,.35);
  }

  .fv-row{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap: 12px;
    flex-wrap: wrap;
  }

  .fv-left{
    display:flex;
    align-items:center;
    gap: 12px;
    min-width: 280px;
    flex: 1 1 auto;
  }

  .fv-mark{
    width: 42px;
    height: 42px;
    border-radius: 14px;
    background: linear-gradient(135deg, var(--fv-brand1), var(--fv-brand2));
    border: 1px solid rgba(255,255,255,.14);
    display:flex;
    align-items:center;
    justify-content:center;
    color:#fff;
    font-weight: 900;
    letter-spacing: .6px;
    user-select:none;
    flex: 0 0 auto;
  }

  .fv-title{
    min-width:0;
  }

  .fv-title h1{
    margin:0;
    font-size: 18px;
    font-weight: 900;
    letter-spacing: .9px;
    color: var(--fv-text);
    line-height: 1.15;
  }

  .fv-title p{
    margin: 6px 0 0 0;
    font-size: 13px;
    color: var(--fv-muted);
    max-width: 860px;
  }

  .fv-badges{
    display:flex;
    gap: 10px;
    flex-wrap: wrap;
    justify-content:flex-end;
    flex: 0 0 auto;
  }

  .fv-badge{
    display:inline-flex;
    align-items:center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,.10);
    background: rgba(0,0,0,.18);
    color: rgba(255,255,255,.90);
    font-size: 12px;
    font-weight: 800;
    letter-spacing: .2px;
    white-space: nowrap;
  }

  .fv-dot{
    width: 7px;
    height: 7px;
    border-radius: 999px;
    background: rgba(255,255,255,.92);
    box-shadow: 0 0 0 3px rgba(255,255,255,.10);
  }
</style>

<div class="fv-hero">
  <div class="fv-row">
    <div class="fv-left">
      <div class="fv-mark">FV</div>
      <div class="fv-title">
        <h1>FORJA VIRAL</h1>
        <p>Transforme vídeos longos em cortes prontos para postar — com legenda e seleção inteligente.</p>
      </div>
    </div>

    <div class="fv-badges" aria-label="benefícios">
      <span class="fv-badge"><span class="fv-dot"></span> Cortes com score</span>
      <span class="fv-badge"><span class="fv-dot"></span> Legendas prontas</span>
      <span class="fv-badge"><span class="fv-dot"></span> Export Premiere</span>
    </div>
  </div>
</div>
"""
