from flask import Blueprint, jsonify, request, session

from models.alocacao_model import nome_recurso
from models.recurso_model import (
    buscar_recurso_por_nome,
    cadastrar_recurso,
    alterar_recurso,
    contar_alocacoes_do_recurso,
    excluir_recurso,
    buscar_proximas_reservas
)
from models.log_model import registrar_log

recurso_bp = Blueprint("recurso", __name__)

TIPOS = ["sala", "laboratorio", "equipamento", "material", "outro"]
STATUS = ["disponivel", "manutencao"]
QUANTIDADE_MAXIMA = 999


def somente_coordenador():
    # devolve a resposta de erro, ou None se pode continuar
    if "usuario_id" not in session:
        return jsonify({"erro": "Voce precisa estar logado"}), 401

    if session.get("perfil") != "coordenador":
        return jsonify({"erro": "Somente o coordenador pode cadastrar ou alterar recursos"}), 403

    return None


def ler_dados_recurso(dados):
    # valida o formulario do recurso; devolve (valores, erro)
    nome = str(dados.get("nome", "")).strip()
    tipo = str(dados.get("tipo", "")).strip().lower()
    quantidade = dados.get("quantidade")

    if len(nome) < 2 or len(nome) > 150:
        return None, "Informe um nome com 2 a 150 caracteres"

    if tipo not in TIPOS:
        return None, "Tipo invalido. Use sala, laboratorio, equipamento, material ou outro"

    try:
        quantidade = int(quantidade)
    except (TypeError, ValueError):
        return None, "Informe a quantidade disponivel"

    if quantidade < 1 or quantidade > QUANTIDADE_MAXIMA:
        return None, "A quantidade precisa ser entre 1 e 999"

    return {"nome": nome, "tipo": tipo, "quantidade": quantidade}, None


@recurso_bp.route("/recursos", methods=["POST"])
def criar_recurso():
    bloqueio = somente_coordenador()
    if bloqueio:
        return bloqueio

    valores, erro = ler_dados_recurso(request.get_json(silent=True) or {})
    if erro:
        return jsonify({"erro": erro}), 400

    if buscar_recurso_por_nome(valores["nome"]):
        return jsonify({"erro": "Ja existe um recurso com esse nome"}), 400

    novo_id = cadastrar_recurso(valores["nome"], valores["tipo"], valores["quantidade"])

    registrar_log(
        session["usuario_id"],
        "CADASTRO_RECURSO",
        f"Recurso {valores['nome']} cadastrado com {valores['quantidade']} unidade(s)"
    )

    return jsonify({"mensagem": "Recurso cadastrado com sucesso", "id": novo_id}), 201


@recurso_bp.route("/recursos/<int:id_recurso>", methods=["PUT"])
def editar_recurso(id_recurso):
    bloqueio = somente_coordenador()
    if bloqueio:
        return bloqueio

    dados = request.get_json(silent=True) or {}
    valores, erro = ler_dados_recurso(dados)
    if erro:
        return jsonify({"erro": erro}), 400

    status = str(dados.get("status", "disponivel")).strip().lower()
    if status not in STATUS:
        return jsonify({"erro": "Status invalido. Use disponivel ou manutencao"}), 400

    if buscar_recurso_por_nome(valores["nome"], id_recurso):
        return jsonify({"erro": "Ja existe um recurso com esse nome"}), 400

    if not alterar_recurso(id_recurso, valores["nome"], valores["tipo"], valores["quantidade"], status):
        return jsonify({"erro": "Recurso nao encontrado"}), 404

    registrar_log(
        session["usuario_id"],
        "ALTERACAO_RECURSO",
        f"Recurso {valores['nome']} alterado: {valores['quantidade']} unidade(s), {status}"
    )

    return jsonify({"mensagem": "Recurso atualizado com sucesso"})


@recurso_bp.route("/recursos/<int:id_recurso>", methods=["DELETE"])
def apagar_recurso(id_recurso):
    bloqueio = somente_coordenador()
    if bloqueio:
        return bloqueio

    futuras, antigas = contar_alocacoes_do_recurso(id_recurso)

    # reserva que ainda vai acontecer: excluir quebraria a aula marcada
    if futuras > 0:
        return jsonify({
            "erro": f"Esse recurso tem {futuras} reserva(s) que ainda vao acontecer. "
                    "Cancele ou troque essas reservas na aba Alocar recurso antes de excluir"
        }), 400

    nome = nome_recurso(id_recurso)

    # so tem aulas antigas: arquiva (some da lista, mas o historico continua)
    if not excluir_recurso(id_recurso, arquivar=antigas > 0):
        return jsonify({"erro": "Recurso nao encontrado"}), 404

    registrar_log(
        session["usuario_id"],
        "EXCLUSAO_RECURSO",
        f"Recurso {nome} excluido" + (" (arquivado, tinha aulas antigas)" if antigas else "")
    )

    return jsonify({"mensagem": "Recurso excluido com sucesso"})


@recurso_bp.route("/recursos/<int:id_recurso>/reservas", methods=["GET"])
def listar_proximas_reservas(id_recurso):
    # mostra em que dia e horario o recurso esta reservado
    bloqueio = somente_coordenador()
    if bloqueio:
        return bloqueio

    return jsonify(buscar_proximas_reservas(id_recurso))
