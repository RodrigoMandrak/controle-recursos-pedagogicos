import secrets
import hashlib

from banco import conectar


def criar_token_recuperacao(usuario_id):
    # gera um token aleatorio que vai no link do e-mail
    token = secrets.token_urlsafe(32)

    # no banco fica somente o hash do token
    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    banco = conectar()
    cursor = banco.cursor()

    # invalida tokens antigos ainda nao utilizados desse usuario
    cursor.execute("""
        UPDATE recuperacao_senha
        SET utilizado = TRUE
        WHERE usuario_id = %s
        AND utilizado = FALSE
    """, (usuario_id,))

    # cria um novo token com validade de 15 minutos
    cursor.execute("""
        INSERT INTO recuperacao_senha
        (usuario_id, token_hash, expira_em)
        VALUES (
            %s,
            %s,
            CURRENT_TIMESTAMP + INTERVAL '15 minutes'
        )
    """, (
        usuario_id,
        token_hash
    ))

    banco.commit()

    cursor.close()
    banco.close()

    # retorna o token verdadeiro somente para montar o link
    return token


def buscar_token_valido(token):
    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT id, usuario_id
        FROM recuperacao_senha
        WHERE token_hash = %s
        AND utilizado = FALSE
        AND expira_em > CURRENT_TIMESTAMP
        ORDER BY id DESC
        LIMIT 1
    """, (token_hash,))

    dados = cursor.fetchone()

    cursor.close()
    banco.close()

    return dados


def marcar_token_utilizado(token_id):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        UPDATE recuperacao_senha
        SET utilizado = TRUE
        WHERE id = %s
    """, (token_id,))

    banco.commit()

    cursor.close()
    banco.close()