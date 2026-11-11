from flask import Blueprint, jsonify, request, session

from models.dashboard_model import (
    buscar_indicadores,
    buscar_recursos_mais_usados,
    buscar_atividades_por_disciplina,
    buscar_atividades_por_mes
)
from validacoes import converter_data

dashboard_bp = Blueprint("dashboard", __name__)

# limite para o grafico por mes nao ficar gigante
MAXIMO_MESES = 24


def ler_filtros():
    # le os filtros da URL: /dashboard?inicio=2026-09-01&fim=2026-11-30&disciplina=2
    # devolve (filtros, erro)
    texto_inicio = request.args.get("inicio", "").strip()
    texto_fim = request.args.get("fim", "").strip()
    texto_disciplina = request.args.get("disciplina", "").strip()

    filtros = {"inicio": None, "fim": None, "disciplina": None}

    if texto_inicio:
        filtros["inicio"] = converter_data(texto_inicio)
        if filtros["inicio"] is None:
            return None, "Data inicial invalida"

    if texto_fim:
        filtros["fim"] = converter_data(texto_fim)
        if filtros["fim"] is None:
            return None, "Data final invalida"

    if filtros["inicio"] and filtros["fim"]:
        if filtros["fim"] < filtros["inicio"]:
            return None, "A data final precisa ser depois da data inicial"

        meses = (filtros["fim"].year - filtros["inicio"].year) * 12 + filtros["fim"].month - filtros["inicio"].month
        if meses >= MAXIMO_MESES:
            return None, "Escolha um periodo de no maximo 24 meses"

    if texto_disciplina:
        if not texto_disciplina.isdigit() or int(texto_disciplina) <= 0:
            return None, "Disciplina invalida"
        filtros["disciplina"] = int(texto_disciplina)

    return filtros, None


@dashboard_bp.route("/dashboard", methods=["GET"])
def mostrar_dashboard():

    if "usuario_id" not in session:
        return jsonify({
            "erro": "Voce precisa estar logado"
        }), 401

    filtros, erro = ler_filtros()

    if erro:
        return jsonify({
            "erro": erro
        }), 400

    usuario_id = session["usuario_id"]
    perfil = session["perfil"]

    return jsonify({
        "perfil": perfil,
        "filtros": {
            "inicio": filtros["inicio"].isoformat() if filtros["inicio"] else None,
            "fim": filtros["fim"].isoformat() if filtros["fim"] else None,
            "disciplina": filtros["disciplina"]
        },
        "indicadores": buscar_indicadores(usuario_id, perfil, filtros),
        "recursos_mais_usados": buscar_recursos_mais_usados(usuario_id, perfil, filtros),
        "por_disciplina": buscar_atividades_por_disciplina(usuario_id, perfil, filtros),
        "por_mes": buscar_atividades_por_mes(usuario_id, perfil, filtros)
    })
