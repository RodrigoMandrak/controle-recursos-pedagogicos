from flask import Blueprint, jsonify, request, session

from models import academico_model
from models.log_model import registrar_log

academico_bp = Blueprint("academico", __name__)

# nome usado nas mensagens e nos logs
NOMES = {
    "disciplinas": ("Disciplina", "DISCIPLINA", "a"),
    "turmas": ("Turma", "TURMA", "a"),
    "professores": ("Professor", "PROFESSOR", "o"),
}


def somente_coordenador():
    if "usuario_id" not in session:
        return jsonify({"erro": "Voce precisa estar logado"}), 401

    if session.get("perfil") != "coordenador":
        return jsonify({"erro": "Somente o coordenador pode cadastrar dados academicos"}), 403

    return None


def ler_nome():
    dados = request.get_json(silent=True) or {}
    nome = " ".join(str(dados.get("nome", "")).split())

    if len(nome) < 1 or len(nome) > 100:
        return None, "Informe um nome com 1 a 100 caracteres"

    return nome, None


def criar(tabela):
    bloqueio = somente_coordenador()
    if bloqueio:
        return bloqueio

    nome, erro = ler_nome()
    if erro:
        return jsonify({"erro": erro}), 400

    titulo, codigo, artigo = NOMES[tabela]

    if academico_model.nome_existe(tabela, nome):
        return jsonify({"erro": f"Ja existe {'uma' if artigo == 'a' else 'um'} {titulo.lower()} com esse nome"}), 400

    novo_id = academico_model.cadastrar(tabela, nome)
    registrar_log(session["usuario_id"], f"CADASTRO_{codigo}", f"{titulo} {nome} cadastrad{artigo}")

    return jsonify({"mensagem": f"{titulo} cadastrad{artigo} com sucesso", "id": novo_id}), 201


def editar(tabela, id_item):
    bloqueio = somente_coordenador()
    if bloqueio:
        return bloqueio

    nome, erro = ler_nome()
    if erro:
        return jsonify({"erro": erro}), 400

    titulo, codigo, artigo = NOMES[tabela]

    if academico_model.nome_existe(tabela, nome, id_item):
        return jsonify({"erro": f"Ja existe {'uma' if artigo == 'a' else 'um'} {titulo.lower()} com esse nome"}), 400

    nome_antigo = academico_model.buscar_nome(tabela, id_item)

    if not academico_model.renomear(tabela, id_item, nome):
        return jsonify({"erro": f"{titulo} nao encontrad{artigo}"}), 404

    registrar_log(session["usuario_id"], f"ALTERACAO_{codigo}",
                  f"{titulo} {nome_antigo or id_item} renomead{artigo} para {nome}")

    return jsonify({"mensagem": f"{titulo} atualizad{artigo} com sucesso"})


def apagar(tabela, id_item):
    bloqueio = somente_coordenador()
    if bloqueio:
        return bloqueio

    titulo, codigo, artigo = NOMES[tabela]

    if tabela == "professores" and academico_model.professor_tem_conta(id_item):
        return jsonify({
            "erro": "Esse professor tem uma conta de acesso ao sistema. "
                    "Ele continua na lista enquanto a conta existir"
        }), 400

    futuras, antigas = academico_model.contar_atividades(tabela, id_item)

    # atividade que ainda vai acontecer depende dele
    if futuras > 0:
        return jsonify({
            "erro": f"Ess{'a' if artigo == 'a' else 'e'} {titulo.lower()} tem {futuras} atividade(s) que ainda vao "
                    "acontecer. Cancele ou altere essas atividades antes"
        }), 400

    nome = academico_model.buscar_nome(tabela, id_item) or id_item

    # so aulas antigas: arquiva (exclusao logica) para o historico continuar certo
    if not academico_model.excluir(tabela, id_item, arquivar=antigas > 0):
        return jsonify({"erro": f"{titulo} nao encontrad{artigo}"}), 404

    registrar_log(session["usuario_id"], f"EXCLUSAO_{codigo}",
                  f"{titulo} {nome} excluid{artigo}" + (" (arquivad" + artigo + ", tinha aulas antigas)" if antigas else ""))

    return jsonify({"mensagem": f"{titulo} excluid{artigo} com sucesso"})


# uma rota de cada para disciplinas, turmas e professores
for _tabela in academico_model.TABELAS:
    academico_bp.add_url_rule(f"/{_tabela}", f"criar_{_tabela}",
                              lambda t=_tabela: criar(t), methods=["POST"])
    academico_bp.add_url_rule(f"/{_tabela}/<int:id_item>", f"editar_{_tabela}",
                              lambda id_item, t=_tabela: editar(t, id_item), methods=["PUT"])
    academico_bp.add_url_rule(f"/{_tabela}/<int:id_item>", f"apagar_{_tabela}",
                              lambda id_item, t=_tabela: apagar(t, id_item), methods=["DELETE"])
