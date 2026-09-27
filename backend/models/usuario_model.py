from banco import conectar
from werkzeug.security import generate_password_hash, check_password_hash


def cadastrar_usuario(nome, email, senha, perfil, identificador=None, aceitou_termos=False):
    banco = conectar()
    cursor = banco.cursor()

    senha_hash = generate_password_hash(senha)

    cursor.execute("""
        INSERT INTO usuarios
        (
            nome,
            email,
            senha_hash,
            perfil,
            identificador_institucional,
            aceitou_termos,
            data_aceite
        )
        VALUES (%s, %s, %s, %s, %s, %s,
        CASE WHEN %s = TRUE THEN CURRENT_TIMESTAMP ELSE NULL END)
    """, (
        nome,
        email,
        senha_hash,
        perfil,
        identificador,
        aceitou_termos,
        aceitou_termos
    ))

    banco.commit()

    cursor.close()
    banco.close()


def buscar_usuario_email(email):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT
            id,
            nome,
            email,
            senha_hash,
            perfil,
            identificador_institucional,
            aceitou_termos
        FROM usuarios
        WHERE email = %s
    """, (email,))

    usuario = cursor.fetchone()

    cursor.close()
    banco.close()

    return usuario


def buscar_usuario_id(usuario_id):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT
            id,
            nome,
            email,
            senha_hash,
            perfil,
            identificador_institucional,
            aceitou_termos,
            data_aceite
        FROM usuarios
        WHERE id = %s
    """, (usuario_id,))

    usuario = cursor.fetchone()

    cursor.close()
    banco.close()

    return usuario


def conferir_senha(senha_digitada, senha_hash):
    return check_password_hash(senha_hash, senha_digitada)


def excluir_usuario(usuario_id):
    banco = conectar()
    cursor = banco.cursor()

    # atividades antigas continuam no sistema,
    # mas deixam de ficar vinculadas a conta excluida
    cursor.execute("""
        UPDATE atividades
        SET usuario_id = NULL
        WHERE usuario_id = %s
    """, (usuario_id,))

    cursor.execute("""
        DELETE FROM usuarios
        WHERE id = %s
    """, (usuario_id,))

    banco.commit()

    cursor.close()
    banco.close()
def atualizar_senha(usuario_id, nova_senha):
    banco = conectar()
    cursor = banco.cursor()

    nova_senha_hash = generate_password_hash(nova_senha)

    cursor.execute("""
        UPDATE usuarios
        SET senha_hash = %s
        WHERE id = %s
    """, (
        nova_senha_hash,
        usuario_id
    ))

    banco.commit()

    cursor.close()
    banco.close()