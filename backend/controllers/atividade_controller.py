from flask import Blueprint, request, jsonify, session

from models.atividade_model import salvar_atividade
from models.atividade_model import buscar_atividades
from models.atividade_model import buscar_disciplinas
from models.atividade_model import buscar_turmas
from models.atividade_model import buscar_professores
from models.log_model import registrar_log


atividade_bp = Blueprint("atividades", __name__)


@atividade_bp.route("/atividades", methods=["POST"])
def cadastrar():

    if "usuario_id" not in session:
        return jsonify({
            "erro": "Voce precisa estar logado"
        }), 401

    dados = request.json

    disciplina = dados.get("disciplina_id")
    turma = dados.get("turma_id")
    professor = dados.get("professor_id")
    descricao = dados.get("descricao")
    data = dados.get("data")
    inicio = dados.get("hora_inicio")
    fim = dados.get("hora_fim")

    if not disciplina or not turma or not professor:
        return jsonify({
            "erro": "Preencha todos os dados"
        }), 400

    if not data or not inicio or not fim:
        return jsonify({
            "erro": "Preencha a data e o horario"
        }), 400

    if fim <= inicio:
        return jsonify({
            "erro": "Horario final invalido"
        }), 400

    salvar_atividade(
        disciplina,
        turma,
        professor,
        descricao,
        data,
        inicio,
        fim,
        session["usuario_id"]
    )

    registrar_log(
        session["usuario_id"],
        "CADASTRO_ATIVIDADE",
        f"Disciplina {disciplina}, turma {turma}, professor {professor}"
    )

    return jsonify({
        "mensagem": "Atividade cadastrada"
    })


@atividade_bp.route("/atividades", methods=["GET"])
def listar():

    if "usuario_id" not in session:
        return jsonify({
            "erro": "Voce precisa estar logado"
        }), 401

    atividades = buscar_atividades(
        session["usuario_id"],
        session["perfil"]
    )

    return jsonify(atividades)


@atividade_bp.route("/disciplinas", methods=["GET"])
def listar_disciplinas():
    dados = buscar_disciplinas()

    return jsonify(dados)


@atividade_bp.route("/turmas", methods=["GET"])
def listar_turmas():
    dados = buscar_turmas()

    return jsonify(dados)


@atividade_bp.route("/professores", methods=["GET"])
def listar_professores():
    dados = buscar_professores()

    return jsonify(dados)