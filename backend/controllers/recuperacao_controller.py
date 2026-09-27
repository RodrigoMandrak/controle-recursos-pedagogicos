import os
import smtplib

from email.message import EmailMessage
from flask import Blueprint, request, jsonify

from models.usuario_model import buscar_usuario_email, atualizar_senha
from models.recuperacao_model import (
    criar_token_recuperacao,
    buscar_token_valido,
    marcar_token_utilizado
)
from models.log_model import registrar_log


recuperacao_bp = Blueprint("recuperacao", __name__)


def enviar_email_recuperacao(destino, nome, link):
    remetente = os.getenv("EMAIL_REMETENTE")
    senha_app = os.getenv("EMAIL_SENHA_APP")

    mensagem = EmailMessage()

    mensagem["Subject"] = "Recuperação de senha - Agenda Pedagógica"
    mensagem["From"] = remetente
    mensagem["To"] = destino

    mensagem.set_content(
        f"""Olá, {nome}.

Recebemos uma solicitação para redefinir sua senha.

Acesse o link abaixo:

{link}

Este link é válido por 15 minutos e poderá ser usado apenas uma vez.

Se você não solicitou a recuperação, ignore este e-mail.
"""
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
        servidor.login(remetente, senha_app)
        servidor.send_message(mensagem)


@recuperacao_bp.route("/esqueci-senha", methods=["POST"])
def esqueci_senha():
    dados = request.get_json() or {}

    email = dados.get("email", "").strip().lower()

    if not email:
        return jsonify({
            "erro": "Informe o e-mail"
        }), 400

    usuario = buscar_usuario_email(email)

    # resposta propositalmente genérica
    # não informa se o e-mail existe ou não
    mensagem = (
        "Se o e-mail estiver cadastrado, "
        "você receberá um link para redefinir sua senha."
    )

    if not usuario:
        return jsonify({
            "mensagem": mensagem
        }), 200

    usuario_id = usuario[0]
    nome = usuario[1]

    token = criar_token_recuperacao(usuario_id)

    frontend_url = os.getenv(
        "FRONTEND_URL",
        "http://localhost:8080"
    )

    link = f"{frontend_url}/?redefinir={token}"

    try:
        enviar_email_recuperacao(
            email,
            nome,
            link
        )

        registrar_log(
            usuario_id,
            "SOLICITACAO_RECUPERACAO_SENHA",
            "Link temporario de recuperacao enviado"
        )

    except Exception as erro:
        print("Erro ao enviar email:", erro)

        return jsonify({
            "erro": "Nao foi possivel enviar o email de recuperacao"
        }), 500

    return jsonify({
        "mensagem": mensagem
    }), 200


@recuperacao_bp.route("/redefinir-senha", methods=["POST"])
def redefinir_senha():
    dados = request.get_json() or {}

    token = dados.get("token", "")
    senha = dados.get("senha", "")
    confirmar_senha = dados.get("confirmar_senha", "")

    if not token:
        return jsonify({
            "erro": "Token nao informado"
        }), 400

    if not senha or not confirmar_senha:
        return jsonify({
            "erro": "Preencha a nova senha"
        }), 400

    if senha != confirmar_senha:
        return jsonify({
            "erro": "As senhas nao conferem"
        }), 400

    if len(senha) < 8:
        return jsonify({
            "erro": "A senha deve ter pelo menos 8 caracteres"
        }), 400

    token_valido = buscar_token_valido(token)

    if not token_valido:
        return jsonify({
            "erro": "Link invalido ou expirado"
        }), 400

    token_id = token_valido[0]
    usuario_id = token_valido[1]

    atualizar_senha(
        usuario_id,
        senha
    )

    marcar_token_utilizado(token_id)

    registrar_log(
        usuario_id,
        "REDEFINICAO_SENHA",
        "Senha redefinida por link temporario"
    )

    return jsonify({
        "mensagem": "Senha redefinida com sucesso"
    }), 200