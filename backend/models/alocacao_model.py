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