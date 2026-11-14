from flask import Blueprint, jsonify, request, session

from models.solicitacao_model import (
    buscar_solicitacoes,
    aprovar_solicitacao,
    recusar_solicitacao
)
from models.log_model import registrar_log

solicitacao_bp = Blueprint("solicitacao", __name__)


def somente_coordenador():
    if "usuario_id" not in session:
        return jsonify({"erro": "Voce precisa estar logado"}), 401

    if session.get("perfil") != "coordenador":
        return jsonify({"erro": "Somente o coordenador pode aprovar cadastros"}), 403

    return None


@solicitacao_bp.route("/solicitacoes", methods=["GET"])
def listar_solicitacoes():
    bloqueio = somente_coordenador()
    if bloqueio:
        return bloqueio

    # /solicitacoes?email=mariana -> so os pre-cadastros com esse e-mail
    email = request.args.get("email", "").strip().lower()[:150]

    return jsonify(buscar_solicitacoes(email))


@solicitacao_bp.route("/solicitacoes/<int:usuario_id>/aprovar", methods=["POST"])
def aprovar(usuario_id):
    bloqueio = somente_coordenador()
    if bloqueio:
        return bloqueio

    nome = aprovar_solicitacao(usuario_id)

    if not nome:
        return jsonify({"erro": "Solicitacao nao encontrada"}), 404

    registrar_log(session["usuario_id"], "APROVACAO_CADASTRO",
                  f"Cadastro de {nome} aprovado como professor")

    return jsonify({"mensagem": f"{nome} aprovado. Ja aparece na lista de professores"})


@solicitacao_bp.route("/solicitacoes/<int:usuario_id>", methods=["DELETE"])
def recusar(usuario_id):
    bloqueio = somente_coordenador()
    if bloqueio:
        return bloqueio

    email = recusar_solicitacao(usuario_id)

    if not email:
        return jsonify({"erro": "Solicitacao nao encontrada"}), 404

    registrar_log(session["usuario_id"], "RECUSA_CADASTRO", f"Cadastro de {email} recusado")

    return jsonify({"mensagem": "Cadastro recusado"})
