from flask import Blueprint, request, jsonify

from models.alocacao_model import buscar_recursos
from models.alocacao_model import salvar_alocacao
from models.alocacao_model import buscar_alocacoes

from services.conflito_service import validar_conflitos


alocacao_bp = Blueprint("alocacoes", __name__)


@alocacao_bp.route("/recursos", methods=["GET"])
def listar_recursos():
    recursos = buscar_recursos()

    return jsonify(recursos)


@alocacao_bp.route("/alocacoes", methods=["POST"])
def alocar_recurso():
    dados = request.json

    atividade = dados.get("atividade_id")
    recurso = dados.get("recurso_id")

    # conferindo se veio os dois campos
    if not atividade or not recurso:
        return jsonify({
            "erro": "Escolha uma atividade e um recurso"
        }), 400

    print("tentando alocar:", atividade, recurso)

    # antes de salvar passa pela parte de conflito do rapha
    erro = validar_conflitos(atividade, recurso)

    if erro:
        return jsonify({
            "erro": erro
        }), 400

    # se nao deu conflito salva normalmente
    salvar_alocacao(atividade, recurso)

    print("alocacao salva")

    return jsonify({
        "mensagem": "Recurso alocado"
    })


@alocacao_bp.route("/alocacoes", methods=["GET"])
def listar_alocacoes():
    dados = buscar_alocacoes()

    return jsonify(dados)