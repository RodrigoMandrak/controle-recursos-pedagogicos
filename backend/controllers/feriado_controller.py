from flask import Blueprint, request, jsonify, session

from models.feriado_model import verificar_feriado


feriado_bp = Blueprint("feriados", __name__)


@feriado_bp.route("/verificar-feriado", methods=["GET"])
def consultar_feriado():

    if "usuario_id" not in session:
        return jsonify({
            "erro": "Voce precisa estar logado"
        }), 401

    data = request.args.get("data")

    if not data:
        return jsonify({
            "erro": "Informe uma data"
        }), 400

    resultado = verificar_feriado(data)

    if resultado.get("erro_api"):
        return jsonify({
            "erro": "Nao foi possivel consultar os feriados"
        }), 503

    return jsonify(resultado)