from flask import Blueprint, request, jsonify, session

from models.feriado_model import verificar_feriado
from models.log_model import registrar_log


feriado_bp = Blueprint("feriados", __name__)


@feriado_bp.route("/verificar-feriado", methods=["GET"])
def consultar_feriado():

    if "usuario_id" not in session:
        return jsonify({
            "erro": "Voce precisa estar logado"
        }), 401

    usuario_id = session.get("usuario_id")
    data = request.args.get("data")

    if not data:
        return jsonify({
            "erro": "Informe uma data"
        }), 400

    resultado = verificar_feriado(data)

    if resultado.get("erro_data"):
        registrar_log(
            usuario_id,
            "CONSULTA_FERIADO_INVALIDA",
            f"Data informada: {data}"
        )

        return jsonify({
            "erro": resultado.get("mensagem", "Data invalida")
        }), 400

    if resultado.get("erro_api"):
        registrar_log(
            usuario_id,
            "ERRO_API_FERIADOS",
            f"Falha na BrasilAPI ao consultar a data {data}"
        )

        return jsonify({
            "erro": "Servico de feriados indisponivel no momento. Tente novamente mais tarde."
        }), 503

    if resultado.get("feriado"):
        detalhes = (
            f"Data: {data} - feriado: {resultado.get('nome')} "
            f"- origem: {resultado.get('origem')}"
        )
    else:
        detalhes = (
            f"Data: {data} - nao e feriado "
            f"- origem: {resultado.get('origem')}"
        )

    registrar_log(
        usuario_id,
        "CONSULTA_FERIADO",
        detalhes
    )

    return jsonify(resultado), 200
