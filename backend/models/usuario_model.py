import re

from banco import conectar
from werkzeug.security import generate_password_hash, check_password_hash


def cadastrar_usuario(nome, email, senha, perfil, identificador=None, aceitou_termos=False, status="ativo"):
    # status: "pendente" = cadastro feito pela tela, esperando o coordenador aprovar
    #         "ativo"    = pode entrar no sistema
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
            data_aceite,
            status
        )
        VALUES (%s, %s, %s, %s, %s, %s,
        CASE WHEN %s = TRUE THEN CURRENT_TIMESTAMP ELSE NULL END, %s)
    """, (
        nome,
        email,
        senha_hash,
        perfil,
        identificador,
        aceitou_termos,
        aceitou_termos,
        status
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
            aceitou_termos,
            status
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


# atividade que ainda nao comecou (pode ser cancelada)
FUTURA = "(a.data > CURRENT_DATE OR (a.data = CURRENT_DATE AND a.hora_inicio > CURRENT_TIME))"


def resumo_exclusao(usuario_id):
    # quantas atividades futuras (e reservas de recurso) a conta tem.
    # A tela mostra isso antes de confirmar a exclusao.
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute(f"""
        SELECT COUNT(DISTINCT a.id), COUNT(al.id)
        FROM atividades a
        LEFT JOIN alocacoes al ON al.atividade_id = a.id
        WHERE {FUTURA}
        AND (
            a.usuario_id = %s
            OR a.professor_id IN (SELECT id FROM professores WHERE usuario_id = %s)
        )
    """, (usuario_id, usuario_id))

    linha = cursor.fetchone()

    cursor.close()
    banco.close()

    return {
        "atividades_futuras": (linha[0] or 0) if linha else 0,
        "reservas_futuras": (linha[1] or 0) if linha else 0,
    }


def excluir_usuario(usuario_id):
    # devolve quantas atividades futuras foram canceladas
    banco = conectar()
    cursor = banco.cursor()

    # atividades que ainda nao aconteceram sao canceladas:
    # as reservas saem junto (ON DELETE CASCADE) e os recursos ficam livres
    cursor.execute(f"""
        DELETE FROM atividades a
        WHERE {FUTURA}
        AND (
            a.usuario_id = %s
            OR a.professor_id IN (SELECT id FROM professores WHERE usuario_id = %s)
        )
    """, (usuario_id, usuario_id))

    canceladas = cursor.rowcount if isinstance(cursor.rowcount, int) and cursor.rowcount > 0 else 0

    # LGPD: o nome da pessoa tambem sai do texto dos logs
    cursor.execute("""
        SELECT nome FROM usuarios WHERE id = %s
        UNION
        SELECT nome FROM professores WHERE usuario_id = %s
        ORDER BY 1
    """, (usuario_id, usuario_id))

    # nome mais comprido primeiro: "Prof. Joana Lima" antes de "Joana Lima"
    nomes = sorted((linha[0] for linha in cursor.fetchall() if linha[0]), key=len, reverse=True)

    for nome in nomes:
        if len(nome.strip()) >= 3:
            cursor.execute("""
                UPDATE logs
                SET detalhes = REGEXP_REPLACE(detalhes, %s, 'Professor(a) removido(a)', 'g')
                WHERE POSITION(%s IN detalhes) > 0
            """, ("\\m" + re.escape(nome.strip()) + "\\M", nome.strip()))

    # atividades antigas continuam no sistema,
    # mas deixam de ficar vinculadas a conta excluida
    cursor.execute("""
        UPDATE atividades
        SET usuario_id = NULL
        WHERE usuario_id = %s
    """, (usuario_id,))

    # LGPD: o nome do professor sai do historico e da lista
    cursor.execute("""
        UPDATE professores
        SET nome = 'Professor(a) removido(a)', ativo = FALSE, usuario_id = NULL
        WHERE usuario_id = %s
    """, (usuario_id,))

    cursor.execute("""
        DELETE FROM usuarios
        WHERE id = %s
    """, (usuario_id,))

    banco.commit()

    cursor.close()
    banco.close()

    return canceladas


# limite de tentativas de login
MAXIMO_TENTATIVAS = 5
MINUTOS_BLOQUEIO = 5


def minutos_bloqueado(usuario_id):
    # quantos minutos faltam para a conta poder tentar de novo (0 = liberada)
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT CEIL(EXTRACT(EPOCH FROM (bloqueado_ate - NOW()::timestamp)) / 60)
        FROM usuarios
        WHERE id = %s AND bloqueado_ate > NOW()::timestamp
    """, (usuario_id,))

    linha = cursor.fetchone()

    cursor.close()
    banco.close()

    return int(linha[0]) if linha and linha[0] else 0


def registrar_senha_errada(usuario_id):
    # soma uma tentativa errada. Na quinta, bloqueia por alguns minutos.
    # Devolve True quando a conta acabou de ser bloqueada
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute(f"""
        UPDATE usuarios
        SET tentativas_login = tentativas_login + 1,
            bloqueado_ate = CASE
                WHEN tentativas_login + 1 >= {MAXIMO_TENTATIVAS}
                THEN NOW()::timestamp + INTERVAL '{MINUTOS_BLOQUEIO} minutes'
                ELSE bloqueado_ate
            END
        WHERE id = %s
        RETURNING tentativas_login
    """, (usuario_id,))

    linha = cursor.fetchone()
    bloqueou = bool(linha and linha[0] >= MAXIMO_TENTATIVAS)

    if bloqueou:
        cursor.execute("UPDATE usuarios SET tentativas_login = 0 WHERE id = %s", (usuario_id,))

    banco.commit()

    cursor.close()
    banco.close()

    return bloqueou


def zerar_tentativas(usuario_id):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        UPDATE usuarios
        SET tentativas_login = 0, bloqueado_ate = NULL
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
        SET senha_hash = %s, tentativas_login = 0, bloqueado_ate = NULL
        WHERE id = %s
    """, (
        nova_senha_hash,
        usuario_id
    ))

    banco.commit()

    cursor.close()
    banco.close()