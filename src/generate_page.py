"""Gera docs/index.html a partir do state.json."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
STATE_FILE = ROOT / "state.json"
OUT_FILE = ROOT / "docs" / "index.html"

STATUS_LABEL = {
    "novo": ("🆕", "Novo", "#2563eb"),
    "notificado": ("🔔", "Notificado", "#7c3aed"),
    "aguardando_resultado": ("⏳", "Aguardando Resultado", "#d97706"),
    "ignorado": ("🚫", "Ignorado", "#6b7280"),
}

MONITOR_STATUS_LABEL = {
    "aguardando_resultado": ("⏳", "Aguardando Resultado", "#d97706"),
    "monitorando": ("👁️", "Monitorando", "#059669"),
}


def fmt_date(raw: str | dict | None) -> str:
    if not raw:
        return "—"
    if isinstance(raw, dict):
        raw = raw.get("date", "")
    try:
        d = datetime.fromisoformat(str(raw).split(".")[0])
        return d.strftime("%d/%m/%Y")
    except Exception:
        return str(raw)[:10]


def fmt_last_run(raw: str) -> str:
    try:
        d = datetime.fromisoformat(raw)
        return d.strftime("%d/%m/%Y às %H:%M")
    except Exception:
        return raw


def edital_card(edital_id: str, e: dict) -> str:
    status = e.get("status", "novo")
    icon, label, color = STATUS_LABEL.get(status, ("•", status, "#6b7280"))
    titulo = e.get("titulo", "Sem título")
    fonte = e.get("fonte", "")
    url = e.get("url", "#")
    prazo = fmt_date(e.get("prazo"))
    encontrado = fmt_date(e.get("encontrado_em"))
    notas = e.get("notas", "")

    notas_html = f'<p class="notas">📝 {notas}</p>' if notas else ""

    return f"""
    <div class="card" style="--accent:{color}">
      <div class="card-header">
        <span class="badge" style="background:{color}">{icon} {label}</span>
        <span class="fonte">{fonte}</span>
      </div>
      <a class="titulo" href="{url}" target="_blank" rel="noopener">{titulo}</a>
      <div class="meta">
        <span>📅 Prazo: <strong>{prazo}</strong></span>
        <span>🔍 Encontrado: {encontrado}</span>
      </div>
      {notas_html}
    </div>"""


def monitor_card(url: str, m: dict) -> str:
    status = m.get("status", "monitorando")
    icon, label, color = MONITOR_STATUS_LABEL.get(status, ("👁️", status, "#059669"))
    titulo = m.get("titulo", url)
    fonte = m.get("fonte", "")
    adicionado = fmt_date(m.get("adicionado_em"))

    return f"""
    <div class="card" style="--accent:{color}">
      <div class="card-header">
        <span class="badge" style="background:{color}">{icon} {label}</span>
        <span class="fonte">{fonte}</span>
      </div>
      <a class="titulo" href="{url}" target="_blank" rel="noopener">{titulo}</a>
      <div class="meta">
        <span>🔍 Adicionado: {adicionado}</span>
      </div>
    </div>"""


def render(state: dict) -> str:
    editais = state.get("editais", {})
    monitoramentos = state.get("monitoramentos", {})
    erros = state.get("erros_ultima_execucao", [])
    last_run = fmt_last_run(state.get("last_run", ""))

    # Agrupar editais por status
    order = ["aguardando_resultado", "novo", "notificado", "ignorado"]
    grupos: dict[str, list] = {s: [] for s in order}
    for eid, e in editais.items():
        s = e.get("status", "novo")
        grupos.setdefault(s, []).append((eid, e))

    # Seção de editais por grupo
    sections_html = ""
    for status in order:
        items = grupos.get(status, [])
        if not items:
            continue
        icon, label, color = STATUS_LABEL.get(status, ("•", status, "#6b7280"))
        cards = "".join(edital_card(eid, e) for eid, e in items)
        sections_html += f"""
        <section>
          <h2 style="color:{color}">{icon} {label} <span class="count">({len(items)})</span></h2>
          <div class="grid">{cards}</div>
        </section>"""

    # Seção monitoramentos
    monitor_html = ""
    if monitoramentos:
        cards = "".join(monitor_card(url, m) for url, m in monitoramentos.items())
        monitor_html = f"""
        <section>
          <h2 style="color:#059669">👁️ Monitoramentos <span class="count">({len(monitoramentos)})</span></h2>
          <div class="grid">{cards}</div>
        </section>"""

    # Seção erros
    erros_html = ""
    if erros:
        items_html = "".join(
            f'<li><strong>{e["fonte"]}</strong> — {e["erro"]} <span class="ts">({e["timestamp"][:16]})</span></li>'
            for e in erros
        )
        erros_html = f"""
        <section class="erros-section">
          <h2>⚠️ Erros na última execução</h2>
          <ul class="erros-list">{items_html}</ul>
        </section>"""

    total = len(editais)
    aguardando = len(grupos.get("aguardando_resultado", []))
    novos = len(grupos.get("novo", []))

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mottriz — Monitor de Editais</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0f0f0f;
      color: #e5e5e5;
      min-height: 100vh;
    }}

    header {{
      background: linear-gradient(135deg, #1a0a2e 0%, #0f0f0f 100%);
      border-bottom: 1px solid #2a2a2a;
      padding: 2rem 1.5rem 1.5rem;
      text-align: center;
    }}

    header h1 {{
      font-size: 1.8rem;
      font-weight: 800;
      letter-spacing: -0.5px;
      color: #fff;
    }}

    header h1 span {{
      color: #a855f7;
    }}

    .subtitle {{
      color: #888;
      font-size: 0.85rem;
      margin-top: 0.4rem;
    }}

    .stats-bar {{
      display: flex;
      justify-content: center;
      gap: 1.5rem;
      margin-top: 1.2rem;
      flex-wrap: wrap;
    }}

    .stat {{
      background: #1a1a1a;
      border: 1px solid #2a2a2a;
      border-radius: 8px;
      padding: 0.5rem 1.2rem;
      font-size: 0.85rem;
      color: #aaa;
    }}

    .stat strong {{
      color: #fff;
      font-size: 1.1rem;
      display: block;
    }}

    main {{
      max-width: 960px;
      margin: 2rem auto;
      padding: 0 1rem;
    }}

    section {{
      margin-bottom: 2.5rem;
    }}

    h2 {{
      font-size: 1rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 1rem;
      padding-bottom: 0.5rem;
      border-bottom: 1px solid #2a2a2a;
    }}

    .count {{
      font-weight: 400;
      opacity: 0.6;
      font-size: 0.85rem;
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1rem;
    }}

    .card {{
      background: #1a1a1a;
      border: 1px solid #2a2a2a;
      border-left: 3px solid var(--accent);
      border-radius: 8px;
      padding: 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
      transition: border-color 0.2s;
    }}

    .card:hover {{
      border-color: var(--accent);
    }}

    .card-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
    }}

    .badge {{
      font-size: 0.7rem;
      font-weight: 700;
      padding: 0.2rem 0.6rem;
      border-radius: 999px;
      color: #fff;
      white-space: nowrap;
    }}

    .fonte {{
      font-size: 0.75rem;
      color: #888;
      text-align: right;
    }}

    .titulo {{
      font-size: 0.9rem;
      font-weight: 600;
      color: #e5e5e5;
      text-decoration: none;
      line-height: 1.4;
    }}

    .titulo:hover {{
      color: #a855f7;
      text-decoration: underline;
    }}

    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      font-size: 0.75rem;
      color: #888;
    }}

    .notas {{
      font-size: 0.78rem;
      color: #aaa;
      font-style: italic;
      border-top: 1px solid #2a2a2a;
      padding-top: 0.5rem;
    }}

    .erros-section h2 {{
      color: #f59e0b;
    }}

    .erros-list {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }}

    .erros-list li {{
      background: #1a1a1a;
      border: 1px solid #2a2a2a;
      border-left: 3px solid #f59e0b;
      border-radius: 6px;
      padding: 0.6rem 0.8rem;
      font-size: 0.82rem;
      color: #ccc;
    }}

    .ts {{
      color: #666;
      font-size: 0.75rem;
    }}

    footer {{
      text-align: center;
      padding: 2rem;
      font-size: 0.75rem;
      color: #444;
      border-top: 1px solid #1a1a1a;
    }}

    @media (max-width: 480px) {{
      header h1 {{ font-size: 1.4rem; }}
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>🎸 <span>Mottriz</span> — Monitor de Editais</h1>
    <p class="subtitle">Última execução: {last_run}</p>
    <div class="stats-bar">
      <div class="stat"><strong>{total}</strong>total</div>
      <div class="stat"><strong>{aguardando}</strong>aguardando resultado</div>
      <div class="stat"><strong>{novos}</strong>novos hoje</div>
      <div class="stat"><strong>{len(monitoramentos)}</strong>monitoramentos</div>
    </div>
  </header>

  <main>
    {sections_html}
    {monitor_html}
    {erros_html}
  </main>

  <footer>
    Gerado automaticamente pelo Mottriz Edital Watcher · {last_run}
  </footer>
</body>
</html>"""


def main():
    if not STATE_FILE.exists():
        print("state.json não encontrado.")
        return

    with open(STATE_FILE, encoding="utf-8") as f:
        state = json.load(f)

    OUT_FILE.parent.mkdir(exist_ok=True)
    html = render(state)
    OUT_FILE.write_text(html, encoding="utf-8")
    print(f"Página gerada: {OUT_FILE}")


if __name__ == "__main__":
    main()
