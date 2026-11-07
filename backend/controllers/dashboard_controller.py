from flask import Blueprint, jsonify, session

from models.dashboard_model import (
    buscar_indicadores,
    buscar_recursos_mais_usados,
    buscar_atividades_por_disciplina,
    buscar_atividades_por_mes
)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard", methods=["GET"])
def mostrar_dashboard():

    if "usuario_id" not in session:
        return jsonify({
            "erro": "Voce precisa estar logado"
        }), 401

    usuario_id = session["usuario_id"]
    perfil = session["perfil"]

    return jsonify({
        "perfil": perfil,
        "indicadores": buscar_indicadores(usuario_id, perfil),
        "recursos_mais_usados": buscar_recursos_mais_usados(usuario_id, perfil),
        "por_disciplina": buscar_atividades_por_disciplina(usuario_id, perfil),
        "por_mes": buscar_atividades_por_mes(usuario_id, perfil)
    })
