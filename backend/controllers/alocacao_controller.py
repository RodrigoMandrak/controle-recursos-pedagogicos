from flask import Blueprint, request, jsonify, session

from models.alocacao_model import buscar_recursos
from models.alocacao_model import salvar_alocacao
from models.alocacao_model import buscar_alocacoes
from models.alocacao_model import buscar_alocacao
from models.alocacao_model import alterar_alocacao
from models.alocacao_model import cancelar_alocacao
from models.alocacao_model import validar_conflitos
from models.alocacao_model import buscar_usuario_atividade
from models.log_model import registrar_log


alocacao_bp = Blueprint("alocacoes", __name__)


@alocacao_bp.route("/recursos", methods=["GET"])
def listar_recursos():

    if "usuario_id" not in session:
        return jsonify({
            "erro": "Voce precisa estar logado"
        }), 401

    recursos = buscar_recursos()

    return jsonify(recursos)


@alocacao_bp.route("/alocacoes", methods=["POST"])
def alocar_recurso():

    if "usuario_id" not in session:
        return jsonify({
            "erro": "Voce precisa estar logado"
        }), 401

    dados = request.json

    atividade = dados.get("atividade_id")
    recurso = dados.get("recurso_id")

    if not atividade or not recurso:
        return jsonify({
            "erro": "Escolha uma atividade e um recurso"
        }), 400

    atividade_usuario = buscar_usuario_atividade(atividade)

    if not atividade_usuario:
        return jsonify({
            "erro": "Atividade nao encontrada"
        }), 404

    dono_atividade = atividade_usuario[0]

    if session["perfil"] != "coordenador":
        if dono_atividade != session["usuario_id"]:
            return jsonify({
                "erro": "Voce nao tem permissao para essa atividade"
            }), 403

    print("tentando alocar:", atividade, recurso)

    erro = validar_conflitos(atividade, recurso)

    if erro:
        return jsonify({
            "erro": erro
        }), 400

    salvar_alocacao(atividade, recurso)

    registrar_log(
        session["usuario_id"],
        "ALOCACAO_RECURSO",
        f"Recurso {recurso} alocado na atividade {atividade}"
    )

    print("alocacao salva")

    return jsonify({
        "mensagem": "Recurso alocado"
    })


@alocacao_bp.route("/alocacoes", methods=["GET"])
def listar_alocacoes():

    if "usuario_id" not in session:
        return jsonify({
            "erro": "Voce precisa estar logado"
        }), 401

    dados = buscar_alocacoes(
        session["usuario_id"],
        session["perfil"]
    )

    return jsonify(dados)


@alocacao_bp.route("/alocacoes/<int:id_alocacao>", methods=["PUT"])
def editar_alocacao(id_alocacao):

    if "usuario_id" not in session:
        return jsonify({
            "erro": "Voce precisa estar logado"
        }), 401

    dados = request.json

    recurso = dados.get("recurso_id")

    if not recurso:
        return jsonify({
            "erro": "Escolha um recurso"
        }), 400

    alocacao = buscar_alocacao(id_alocacao)

    if not alocacao:
        return jsonify({
            "erro": "Alocacao nao encontrada"
        }), 404

    atividade = alocacao[0]
    recurso_atual = alocacao[1]
    dono_atividade = alocacao[2]

    if session["perfil"] != "coordenador":
        if dono_atividade != session["usuario_id"]:
            return jsonify({
                "erro": "Voce nao tem permissao para alterar essa alocacao"
            }), 403

    if int(recurso) == recurso_atual:
        return jsonify({
            "erro": "Escolha um recurso diferente"
        }), 400

    erro = validar_conflitos(atividade, recurso)

    if erro:
        return jsonify({
            "erro": erro
        }), 400

    alterar_alocacao(id_alocacao, recurso)

    registrar_log(
        session["usuario_id"],
        "ALTERACAO_ALOCACAO",
        f"Alocacao {id_alocacao} alterada do recurso {recurso_atual} para {recurso}"
    )

    return jsonify({
        "mensagem": "Alocacao alterada"
    })


@alocacao_bp.route("/alocacoes/<int:id_alocacao>", methods=["DELETE"])
def excluir_alocacao(id_alocacao):

    if "usuario_id" not in session:
        return jsonify({
            "erro": "Voce precisa estar logado"
        }), 401

    alocacao = buscar_alocacao(id_alocacao)

    if not alocacao:
        return jsonify({
            "erro": "Alocacao nao encontrada"
        }), 404

    atividade = alocacao[0]
    recurso = alocacao[1]
    dono_atividade = alocacao[2]

    if session["perfil"] != "coordenador":
        if dono_atividade != session["usuario_id"]:
            return jsonify({
                "erro": "Voce nao tem permissao para cancelar essa alocacao"
            }), 403

    cancelar_alocacao(id_alocacao)

    registrar_log(
        session["usuario_id"],
        "CANCELAMENTO_ALOCACAO",
        f"Alocacao {id_alocacao} da atividade {atividade} e recurso {recurso} foi cancelada"
    )

    return jsonify({
        "mensagem": "Alocacao cancelada"
    })