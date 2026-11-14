from flask import Blueprint, request, jsonify, session

from models.atividade_model import salvar_atividade
from models.atividade_model import buscar_atividades
from models.atividade_model import buscar_disciplinas
from models.atividade_model import buscar_turmas
from models.atividade_model import buscar_professores
from models.atividade_model import buscar_professor_do_usuario
from models.atividade_model import buscar_atividade
from models.atividade_model import procurar_conflito_atividade
from models.atividade_model import recursos_sem_vaga
from models.atividade_model import alterar_atividade
from models.atividade_model import cancelar_atividade
from models.atividade_model import descrever_atividade
from models.academico_model import itens_ativos
from models.log_model import registrar_log

from validacoes import converter_data
from validacoes import data_passada
from validacoes import horario_valido
from validacoes import texto_no_limite
from validacoes import TAMANHO_MAXIMO_DESCRICAO


atividade_bp = Blueprint("atividades", __name__)

MENSAGEM_CONFLITO = {
    "professor": "Esse professor ja tem outra atividade nesse horario",
    "turma": "Essa turma ja tem outra atividade nesse horario",
}


def ler_atividade(dados, id_atividade=None):
    # confere os dados da atividade (cadastro e edicao usam as mesmas regras).
    # Devolve (campos, None) quando esta tudo certo, ou (None, (mensagem, status))
    disciplina = dados.get("disciplina_id")
    turma = dados.get("turma_id")
    professor = dados.get("professor_id")
    descricao = dados.get("descricao")
    data = dados.get("data")
    inicio = dados.get("hora_inicio")
    fim = dados.get("hora_fim")

    # o professor so cadastra atividade no proprio nome
    if session.get("perfil") != "coordenador":
        meu_professor = buscar_professor_do_usuario(session["usuario_id"])
        if meu_professor:
            professor = meu_professor

    if not disciplina or not turma or not professor:
        return None, ("Preencha todos os dados", 400)

    if not data or not inicio or not fim:
        return None, ("Preencha a data e o horario", 400)

    data_convertida = converter_data(data)

    if not data_convertida:
        return None, ("Data invalida", 400)

    if data_passada(data_convertida):
        return None, ("Nao e possivel cadastrar atividade em data passada", 400)

    if not horario_valido(inicio) or not horario_valido(fim):
        return None, ("Horario invalido", 400)

    if fim <= inicio:
        return None, ("Horario final invalido", 400)

    if not texto_no_limite(descricao, TAMANHO_MAXIMO_DESCRICAO):
        return None, ("A descricao deve ter no maximo 500 caracteres", 400)

    # disciplina, turma ou professor que foi excluido nao pode ser usado
    if not itens_ativos(disciplina, turma, professor):
        return None, ("Disciplina, turma ou professor nao encontrado. Atualize a pagina", 400)

    conflito = procurar_conflito_atividade(professor, turma, data, inicio, fim, id_atividade)

    if conflito:
        registrar_log(
            session["usuario_id"],
            "CONFLITO_BLOQUEADO",
            f"{MENSAGEM_CONFLITO[conflito]} ({data} {inicio}-{fim})"
        )
        return None, (MENSAGEM_CONFLITO[conflito], 400)

    return (disciplina, turma, professor, descricao, data, inicio, fim), None


def pode_mexer(id_atividade):
    # devolve (atividade, None) ou (None, resposta de erro)
    atividade = buscar_atividade(id_atividade)

    if not atividade:
        return None, (jsonify({"erro": "Atividade nao encontrada"}), 404)

    if session.get("perfil") != "coordenador" and atividade[0] != session["usuario_id"]:
        return None, (jsonify({"erro": "Voce nao tem permissao para essa atividade"}), 403)

    # o que ja aconteceu (ou ja comecou) fica no historico
    if atividade[4]:
        return None, (jsonify({"erro": "Essa atividade ja aconteceu e nao pode mais ser alterada"}), 400)

    return atividade, None


@atividade_bp.route("/atividades", methods=["POST"])
def cadastrar():

    if "usuario_id" not in session:
        return jsonify({
            "erro": "Voce precisa estar logado"
        }), 401

    campos, erro = ler_atividade(request.json or {})

    if erro:
        return jsonify({"erro": erro[0]}), erro[1]

    novo_id = salvar_atividade(*campos, session["usuario_id"])

    registrar_log(
        session["usuario_id"],
        "CADASTRO_ATIVIDADE",
        descrever_atividade(novo_id)
    )

    return jsonify({
        "mensagem": "Atividade cadastrada"
    })


@atividade_bp.route("/atividades/<int:id_atividade>", methods=["PUT"])
def editar(id_atividade):

    if "usuario_id" not in session:
        return jsonify({"erro": "Voce precisa estar logado"}), 401

    _, bloqueio = pode_mexer(id_atividade)
    if bloqueio:
        return bloqueio

    campos, erro = ler_atividade(request.json or {}, id_atividade)

    if erro:
        return jsonify({"erro": erro[0]}), erro[1]

    # os recursos que ja estao na atividade precisam caber no horario novo
    sem_vaga = recursos_sem_vaga(id_atividade, campos[4], campos[5], campos[6])

    if sem_vaga:
        registrar_log(
            session["usuario_id"],
            "CONFLITO_BLOQUEADO",
            f"Edicao de {descrever_atividade(id_atividade)}: sem vaga para {', '.join(sem_vaga)} no novo horario"
        )
        return jsonify({
            "erro": "No novo horario nao ha vaga para: " + ", ".join(sem_vaga)
                    + ". Troque ou cancele esses recursos antes"
        }), 400

    antes = descrever_atividade(id_atividade)
    alterar_atividade(id_atividade, *campos)

    registrar_log(
        session["usuario_id"],
        "ALTERACAO_ATIVIDADE",
        f"{antes} -> {descrever_atividade(id_atividade)}"
    )

    return jsonify({"mensagem": "Atividade alterada"})


@atividade_bp.route("/atividades/<int:id_atividade>", methods=["DELETE"])
def cancelar(id_atividade):

    if "usuario_id" not in session:
        return jsonify({"erro": "Voce precisa estar logado"}), 401

    _, bloqueio = pode_mexer(id_atividade)
    if bloqueio:
        return bloqueio

    descricao = descrever_atividade(id_atividade)
    cancelar_atividade(id_atividade)

    registrar_log(
        session["usuario_id"],
        "CANCELAMENTO_ATIVIDADE",
        f"{descricao} cancelada (recursos liberados)"
    )

    return jsonify({"mensagem": "Atividade cancelada e recursos liberados"})


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


@atividade_bp.route("/meu-professor", methods=["GET"])
def meu_professor():
    # usado pela tela para ja deixar o professor logado selecionado
    if "usuario_id" not in session:
        return jsonify({"erro": "Voce precisa estar logado"}), 401

    return jsonify({"professor_id": buscar_professor_do_usuario(session["usuario_id"])})


@atividade_bp.route("/professores", methods=["GET"])
def listar_professores():
    dados = buscar_professores()

    return jsonify(dados)