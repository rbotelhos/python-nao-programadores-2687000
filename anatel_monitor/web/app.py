"""
Interface web do Robô de Monitoramento Anatel.

Rotas:
  GET  /                 — dashboard principal
  GET  /api/consultas    — JSON com filtros (q, tipo, status, ano)
  GET  /api/stats        — JSON de estatísticas para gráficos
  GET  /exportar.csv     — exporta todas as consultas em CSV
"""

import csv
import io
import logging
from datetime import datetime

from flask import Flask, jsonify, render_template, request, Response

from ..database import (
    inicializar_banco,
    listar_para_web,
    anos_com_consultas,
    estatisticas,
)

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["JSON_ENSURE_ASCII"] = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ano_atual() -> int:
    return datetime.now().year


def _build_sections(consultas: list[dict]) -> dict:
    """Divide consultas nas seções do dashboard."""
    ano = _ano_atual()
    abertas_atual, abertas_anterior, encerradas, urgentes = [], [], [], []

    for c in consultas:
        if c["urgente"] and c["status"] == "Aberta":
            urgentes.append(c)

        ano_ref = int(c["ano_abertura"] or c["ano_encerramento"] or 0)

        if c["status"] == "Aberta":
            if ano_ref == ano or ano_ref == 0:
                abertas_atual.append(c)
            elif ano_ref == ano - 1:
                abertas_anterior.append(c)
            else:
                abertas_atual.append(c)      # anos muito antigos ainda abertas → atual
        else:
            encerradas.append(c)

    return {
        "urgentes": urgentes,
        "abertas_atual": abertas_atual,
        "abertas_anterior": abertas_anterior,
        "encerradas": encerradas,
    }


# ---------------------------------------------------------------------------
# Rotas principais
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    inicializar_banco()
    ano = _ano_atual()
    todas = listar_para_web()
    stats = estatisticas()
    anos = anos_com_consultas() or [ano, ano - 1]
    sections = _build_sections(todas)

    return render_template(
        "index.html",
        ano_atual=ano,
        ano_anterior=ano - 1,
        stats=stats,
        anos=anos,
        **sections,
    )


# ---------------------------------------------------------------------------
# API JSON
# ---------------------------------------------------------------------------

@app.route("/api/consultas")
def api_consultas():
    q = request.args.get("q", "").strip()
    tipo = request.args.get("tipo") or None
    status = request.args.get("status") or None
    ano_str = request.args.get("ano")
    ano = int(ano_str) if ano_str and ano_str.isdigit() else None

    consultas = listar_para_web(q=q, tipo=tipo, status=status, ano=ano)
    return jsonify(consultas)


@app.route("/api/stats")
def api_stats():
    inicializar_banco()
    todas = listar_para_web()
    ano = _ano_atual()

    # Contagens por ano
    por_ano: dict[str, int] = {}
    por_tipo_ano: dict[str, dict] = {}
    for c in todas:
        a = c["ano_abertura"] or c["ano_encerramento"] or "?"
        por_ano[a] = por_ano.get(a, 0) + 1
        tipo_curto = "CP" if "Pública" in c["tipo"] else "TS"
        por_tipo_ano.setdefault(a, {"CP": 0, "TS": 0})
        por_tipo_ano[a][tipo_curto] += 1

    anos_ord = sorted(por_ano.keys(), reverse=True)[:5]

    stats = estatisticas()
    return jsonify({
        "totais": stats,
        "por_ano": {a: por_ano[a] for a in anos_ord},
        "por_tipo_ano": {a: por_tipo_ano.get(a, {"CP": 0, "TS": 0}) for a in anos_ord},
    })


# ---------------------------------------------------------------------------
# Exportação CSV
# ---------------------------------------------------------------------------

@app.route("/exportar.csv")
def exportar_csv():
    todas = listar_para_web(
        q=request.args.get("q", ""),
        tipo=request.args.get("tipo") or None,
        status=request.args.get("status") or None,
    )

    campos = [
        "codigo", "tipo", "numero", "titulo", "objeto", "descricao",
        "questionamentos", "data_abertura", "data_encerramento",
        "prazo_resposta", "data_publicacao_dou", "status", "adiada",
        "orgao_responsavel", "numero_contribuicoes", "link", "fonte",
        "data_descoberta",
    ]

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=campos, extrasaction="ignore")
    writer.writeheader()
    for c in todas:
        c["adiada"] = "Sim" if c["adiada"] else "Não"
        writer.writerow(c)

    return Response(
        buf.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                f"attachment; filename=anatel_consultas_{datetime.now().strftime('%Y%m%d')}.csv"
            )
        },
    )


# ---------------------------------------------------------------------------
# Inicialização
# ---------------------------------------------------------------------------

def criar_app(debug: bool = False) -> Flask:
    app.debug = debug
    inicializar_banco()
    return app
