from banco import conectar


def buscar_recursos():
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT id, nome, tipo, status
        FROM recursos
        ORDER BY nome
    """)

    dados = cursor.fetchall()
    lista = []

    for recurso in dados:
        lista.append({
            "id": recurso[0],
            "nome": recurso[1],
            "tipo": recurso[2],
            "status": recurso[3]
        })

    cursor.close()
    banco.close()

    return lista


def pegar_atividade(id_atividade):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT data, hora_inicio, hora_fim, professor_id, turma_id
        FROM atividades
        WHERE id = %s
    """, (id_atividade,))

    atividade = cursor.fetchone()

    cursor.close()
    banco.close()

    return atividade


def procurar_conflito_recurso(recurso, data, inicio, fim):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT al.id
        FROM alocacoes al
        JOIN atividades a ON a.id = al.atividade_id
        WHERE al.recurso_id = %s
        AND a.data = %s
        AND %s < a.hora_fim
        AND %s > a.hora_inicio
    """, (recurso, data, inicio, fim))

    conflito = cursor.fetchone()

    cursor.close()
    banco.close()

    return conflito


def procurar_conflito_professor(professor, atividade, data, inicio, fim):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT al.id
        FROM alocacoes al
        JOIN atividades a ON a.id = al.atividade_id
        WHERE a.professor_id = %s
        AND a.id <> %s
        AND a.data = %s
        AND %s < a.hora_fim
        AND %s > a.hora_inicio
    """, (professor, atividade, data, inicio, fim))

    conflito = cursor.fetchone()

    cursor.close()
    banco.close()

    return conflito


def procurar_conflito_turma(turma, atividade, data, inicio, fim):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT al.id
        FROM alocacoes al
        JOIN atividades a ON a.id = al.atividade_id
        WHERE a.turma_id = %s
        AND a.id <> %s
        AND a.data = %s
        AND %s < a.hora_fim
        AND %s > a.hora_inicio
    """, (turma, atividade, data, inicio, fim))

    conflito = cursor.fetchone()

    cursor.close()
    banco.close()

    return conflito


def salvar_alocacao(atividade, recurso):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute(
        "INSERT INTO alocacoes (atividade_id, recurso_id) VALUES (%s, %s)",
        (atividade, recurso)
    )

    banco.commit()

    cursor.close()
    banco.close()


def buscar_alocacoes():
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT al.id, d.nome, t.nome, p.nome,
        a.data, a.hora_inicio, a.hora_fim,
        r.nome, r.tipo
        FROM alocacoes al
        JOIN atividades a ON a.id = al.atividade_id
        JOIN disciplinas d ON d.id = a.disciplina_id
        JOIN turmas t ON t.id = a.turma_id
        JOIN professores p ON p.id = a.professor_id
        JOIN recursos r ON r.id = al.recurso_id
        ORDER BY al.id DESC
    """)

    dados = cursor.fetchall()
    lista = []

    for item in dados:
        lista.append({
            "id": item[0],
            "disciplina": item[1],
            "turma": item[2],
            "professor": item[3],
            "data": str(item[4]),
            "hora_inicio": str(item[5]),
            "hora_fim": str(item[6]),
            "recurso": item[7],
            "tipo": item[8]
        })

    cursor.close()
    banco.close()

    return lista


def buscar_alocacao(id_alocacao):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT atividade_id, recurso_id
        FROM alocacoes
        WHERE id = %s
    """, (id_alocacao,))

    alocacao = cursor.fetchone()

    cursor.close()
    banco.close()

    return alocacao


def alterar_alocacao(id_alocacao, recurso):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        UPDATE alocacoes
        SET recurso_id = %s
        WHERE id = %s
    """, (recurso, id_alocacao))

    banco.commit()

    cursor.close()
    banco.close()


def cancelar_alocacao(id_alocacao):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        DELETE FROM alocacoes
        WHERE id = %s
    """, (id_alocacao,))

    banco.commit()

    cursor.close()
    banco.close()


def validar_conflitos(atividade_id, recurso_id):

    atividade = pegar_atividade(atividade_id)

    if not atividade:
        return "Atividade nao encontrada"

    data = atividade[0]
    inicio = atividade[1]
    fim = atividade[2]
    professor = atividade[3]
    turma = atividade[4]

    print("testando conflitos:", atividade_id, recurso_id)

    conflito_recurso = procurar_conflito_recurso(
        recurso_id,
        data,
        inicio,
        fim
    )

    if conflito_recurso:
        print("conflito de recurso")
        return "Esse recurso ja esta sendo usado nesse horario"

    conflito_professor = procurar_conflito_professor(
        professor,
        atividade_id,
        data,
        inicio,
        fim
    )

    if conflito_professor:
        print("conflito de professor")
        return "Esse professor ja possui uma atividade nesse horario"

    conflito_turma = procurar_conflito_turma(
        turma,
        atividade_id,
        data,
        inicio,
        fim
    )

    if conflito_turma:
        print("conflito de turma")
        return "Essa turma ja possui uma atividade nesse horario"

    return None