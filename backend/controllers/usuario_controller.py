from flask import Blueprint, request, jsonify, session

from models.usuario_model import cadastrar_usuario
from models.usuario_model import buscar_usuario_email
from models.usuario_model import buscar_usuario_id
from models.usuario_model import conferir_senha
from models.usuario_model import excluir_usuario

from models.log_model import registrar_log


usuario_bp = Blueprint("usuarios", __name__)


@usuario_bp.route("/usuarios/cadastro", methods=["POST"])
def cadastrar():
    dados = request.json

    nome = dados.get("nome")
    email = dados.get("email")
    senha = dados.get("senha")
    confirmar_senha = dados.get("confirmar_senha")
    identificador = dados.get("identificador_institucional")
    aceitou_termos = dados.get("aceitou_termos")

    if not nome or not email or not senha:
        return jsonify({
            "erro": "Preencha os campos obrigatorios"
        }), 400

    if senha != confirmar_senha:
        return jsonify({
            "erro": "As senhas nao conferem"
        }), 400

    if not aceitou_termos:
        return jsonify({
            "erro": "Voce precisa aceitar os termos"
        }), 400

    usuario_existente = buscar_usuario_email(email)

    if usuario_existente:
        return jsonify({
            "erro": "Esse email ja esta cadastrado"
        }), 400

    cadastrar_usuario(
        nome,
        email,
        senha,
        "professor",
        identificador,
        True
    )

    return jsonify({
        "mensagem": "Usuario cadastrado com sucesso"
    })


@usuario_bp.route("/login", methods=["POST"])
def login():
    dados = request.json

    email = dados.get("email")
    senha = dados.get("senha")

    if not email or not senha:
        return jsonify({
            "erro": "Informe email e senha"
        }), 400

    usuario = buscar_usuario_email(email)

    if not usuario:
        return jsonify({
            "erro": "Email ou senha incorretos"
        }), 401

    senha_certa = conferir_senha(senha, usuario[3])

    if not senha_certa:
        return jsonify({
            "erro": "Email ou senha incorretos"
        }), 401

    session["usuario_id"] = usuario[0]
    session["nome"] = usuario[1]
    session["perfil"] = usuario[4]

    registrar_log(
        usuario[0],
        "LOGIN",
        "Usuario realizou login no sistema"
    )

    print("usuario logado:", usuario[1], usuario[4])

    return jsonify({
        "mensagem": "Login realizado",
        "usuario": {
            "id": usuario[0],
            "nome": usuario[1],
            "email": usuario[2],
            "perfil": usuario[4]
        }
    })


@usuario_bp.route("/usuario-logado", methods=["GET"])
def usuario_logado():

    if "usuario_id" not in session:
        return jsonify({
            "erro": "Usuario nao esta logado"
        }), 401

    return jsonify({
        "id": session["usuario_id"],
        "nome": session["nome"],
        "perfil": session["perfil"]
    })


@usuario_bp.route("/meus-dados", methods=["GET"])
def meus_dados():

    if "usuario_id" not in session:
        return jsonify({
            "erro": "Voce precisa estar logado"
        }), 401

    usuario = buscar_usuario_id(session["usuario_id"])

    if not usuario:
        return jsonify({
            "erro": "Usuario nao encontrado"
        }), 404

    return jsonify({
        "id": usuario[0],
        "nome": usuario[1],
        "email": usuario[2],
        "perfil": usuario[4],
        "identificador_institucional": usuario[5],
        "aceitou_termos": usuario[6],
        "data_aceite": str(usuario[7]) if usuario[7] else None
    })


@usuario_bp.route("/minha-conta", methods=["DELETE"])
def excluir_minha_conta():

    if "usuario_id" not in session:
        return jsonify({
            "erro": "Voce precisa estar logado"
        }), 401

    # coordenador nao pode apagar a propria conta por essa rota
    if session["perfil"] == "coordenador":
        return jsonify({
            "erro": "A conta do coordenador nao pode ser excluida por essa opcao"
        }), 403

    dados = request.json
    senha = dados.get("senha")

    if not senha:
        return jsonify({
            "erro": "Digite sua senha para confirmar a exclusao"
        }), 400

    usuario = buscar_usuario_id(session["usuario_id"])

    if not usuario:
        return jsonify({
            "erro": "Usuario nao encontrado"
        }), 404

    senha_certa = conferir_senha(senha, usuario[3])

    if not senha_certa:
        return jsonify({
            "erro": "Senha incorreta"
        }), 401

    usuario_id = usuario[0]

    # registra a acao antes da exclusao
    registrar_log(
        usuario_id,
        "EXCLUSAO_CONTA",
        "Usuario solicitou a exclusao da propria conta"
    )

    excluir_usuario(usuario_id)

    session.clear()

    return jsonify({
        "mensagem": "Conta excluida com sucesso"
    })


@usuario_bp.route("/logout", methods=["POST"])
def logout():

    if "usuario_id" in session:
        usuario_id = session["usuario_id"]

        registrar_log(
            usuario_id,
            "LOGOUT",
            "Usuario saiu do sistema"
        )

    session.clear()

    return jsonify({
        "mensagem": "Logout realizado"
    })