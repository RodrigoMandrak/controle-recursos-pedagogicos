from banco import conectar


def buscar_solicitacoes(email=""):
    # cadastros feitos pela tela que ainda esperam o coordenador.
    # email: busca por parte do e-mail (ex.: "mariana" acha mariana@escola.com.br)
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT id, nome, email, identificador_institucional, data_aceite
        FROM usuarios
        WHERE status = 'pendente'
        AND (%s = '' OR email ILIKE %s)
        ORDER BY id DESC
        LIMIT 50
    """, (email, f"%{email}%"))

    dados = cursor.fetchall()

    cursor.close()
    banco.close()

    return [{
        "id": item[0],
        "nome": item[1],
        "email": item[2],
        "identificador": item[3],
        "data": str(item[4])[:16] if item[4] else None
    } for item in dados]


def aprovar_solicitacao(usuario_id):
    # vira professor ativo e entra na lista de professores (ligado a conta)
    # devolve o nome, ou None se a solicitacao nao existe mais
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        UPDATE usuarios
        SET status = 'ativo', perfil = 'professor'
        WHERE id = %s AND status = 'pendente'
        RETURNING nome
    """, (usuario_id,))

    linha = cursor.fetchone()

    if not linha:
        banco.rollback()
        cursor.close()
        banco.close()
        return None

    nome = linha[0]

    # se ja existe na lista um professor com o mesmo nome e sem conta, liga nele
    cursor.execute("""
        SELECT id FROM professores
        WHERE LOWER(nome) = LOWER(%s) AND usuario_id IS NULL
        ORDER BY id LIMIT 1
    """, (nome,))
    existente = cursor.fetchone()

    if existente:
        cursor.execute("UPDATE professores SET usuario_id = %s WHERE id = %s", (usuario_id, existente[0]))
    else:
        cursor.execute("INSERT INTO professores (nome, usuario_id) VALUES (%s, %s)", (nome, usuario_id))

    banco.commit()
    cursor.close()
    banco.close()

    return nome


def recusar_solicitacao(usuario_id):
    # cadastro recusado e apagado (ele nunca entrou no sistema)
    # devolve o e-mail, ou None se a solicitacao nao existe mais
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        DELETE FROM usuarios
        WHERE id = %s AND status = 'pendente'
        RETURNING email
    """, (usuario_id,))

    linha = cursor.fetchone()
    banco.commit()

    cursor.close()
    banco.close()

    return linha[0] if linha else None
