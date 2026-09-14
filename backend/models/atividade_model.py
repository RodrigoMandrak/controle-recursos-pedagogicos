from banco import conectar


def salvar_atividade(disciplina, turma, professor, descricao, data, inicio, fim):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute(
        """INSERT INTO atividades
        (disciplina_id, turma_id, professor_id, descricao, data, hora_inicio, hora_fim)
        VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (disciplina, turma, professor, descricao, data, inicio, fim)
    )

    banco.commit()
    cursor.close()
    banco.close()


def buscar_atividades():
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT a.id, d.nome, t.nome, p.nome,
        a.descricao, a.data, a.hora_inicio, a.hora_fim
        FROM atividades a
        JOIN disciplinas d ON d.id = a.disciplina_id
        JOIN turmas t ON t.id = a.turma_id
        JOIN professores p ON p.id = a.professor_id
        ORDER BY a.id DESC
    """)

    dados = cursor.fetchall()

    lista = []

    for atividade in dados:
        lista.append({
            "id": atividade[0],
            "disciplina": atividade[1],
            "turma": atividade[2],
            "professor": atividade[3],
            "descricao": atividade[4],
            "data": str(atividade[5]),
            "hora_inicio": str(atividade[6]),
            "hora_fim": str(atividade[7])
        })

    cursor.close()
    banco.close()

    return lista


def buscar_disciplinas():
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("SELECT id, nome FROM disciplinas ORDER BY nome")
    dados = cursor.fetchall()

    lista = []

    for item in dados:
        lista.append({
            "id": item[0],
            "nome": item[1]
        })

    cursor.close()
    banco.close()

    return lista


def buscar_turmas():
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("SELECT id, nome FROM turmas ORDER BY nome")
    dados = cursor.fetchall()

    lista = []

    for item in dados:
        lista.append({
            "id": item[0],
            "nome": item[1]
        })

    cursor.close()
    banco.close()

    return lista


def buscar_professores():
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("SELECT id, nome FROM professores ORDER BY nome")
    dados = cursor.fetchall()

    lista = []

    for item in dados:
        lista.append({
            "id": item[0],
            "nome": item[1]
        })

    cursor.close()
    banco.close()

    return lista