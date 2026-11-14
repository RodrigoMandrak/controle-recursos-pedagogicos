from banco import conectar


def salvar_atividade(
    disciplina,
    turma,
    professor,
    descricao,
    data,
    inicio,
    fim,
    usuario_id
):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute(
        """INSERT INTO atividades
        (disciplina_id, turma_id, professor_id, descricao, data,
        hora_inicio, hora_fim, usuario_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id""",
        (
            disciplina,
            turma,
            professor,
            descricao,
            data,
            inicio,
            fim,
            usuario_id
        )
    )

    linha = cursor.fetchone()
    banco.commit()

    cursor.close()
    banco.close()

    return linha[0] if linha else None


def buscar_atividades(usuario_id, perfil):
    banco = conectar()
    cursor = banco.cursor()

    # coordenador consegue visualizar todas as atividades
    if perfil == "coordenador":
        cursor.execute("""
            SELECT a.id, d.nome, t.nome, p.nome,
            a.descricao, a.data, a.hora_inicio, a.hora_fim,
            a.disciplina_id, a.turma_id, a.professor_id,
            (a.data < CURRENT_DATE OR (a.data = CURRENT_DATE AND a.hora_fim <= CURRENT_TIME))
            FROM atividades a
            JOIN disciplinas d ON d.id = a.disciplina_id
            JOIN turmas t ON t.id = a.turma_id
            JOIN professores p ON p.id = a.professor_id
            ORDER BY a.id DESC
        """)

    # professor visualiza somente as atividades dele
    else:
        cursor.execute("""
            SELECT a.id, d.nome, t.nome, p.nome,
            a.descricao, a.data, a.hora_inicio, a.hora_fim,
            a.disciplina_id, a.turma_id, a.professor_id,
            (a.data < CURRENT_DATE OR (a.data = CURRENT_DATE AND a.hora_fim <= CURRENT_TIME))
            FROM atividades a
            JOIN disciplinas d ON d.id = a.disciplina_id
            JOIN turmas t ON t.id = a.turma_id
            JOIN professores p ON p.id = a.professor_id
            WHERE a.usuario_id = %s
            ORDER BY a.id DESC
        """, (usuario_id,))

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
            "hora_fim": str(atividade[7]),
            "disciplina_id": atividade[8] if len(atividade) > 8 else None,
            "turma_id": atividade[9] if len(atividade) > 9 else None,
            "professor_id": atividade[10] if len(atividade) > 10 else None,
            "ja_aconteceu": bool(atividade[11]) if len(atividade) > 11 else False
        })

    cursor.close()
    banco.close()

    return lista


def buscar_disciplinas():
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute(
        "SELECT id, nome FROM disciplinas WHERE ativo = TRUE ORDER BY nome"
    )

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

    cursor.execute(
        "SELECT id, nome FROM turmas WHERE ativo = TRUE ORDER BY nome"
    )

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

    cursor.execute(
        "SELECT id, nome FROM professores WHERE ativo = TRUE ORDER BY nome"
    )

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

def buscar_professor_do_usuario(usuario_id):
    # id do professor (lista de professores) ligado a conta do usuario, ou None
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute(
        "SELECT id FROM professores WHERE usuario_id = %s AND ativo = TRUE ORDER BY id LIMIT 1",
        (usuario_id,)
    )
    linha = cursor.fetchone()

    cursor.close()
    banco.close()

    return linha[0] if linha else None


def buscar_atividade(id_atividade):
    # (usuario_id dono, data, hora_inicio, hora_fim, ja_aconteceu) ou None
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT usuario_id, data, hora_inicio, hora_fim,
        (data < CURRENT_DATE OR (data = CURRENT_DATE AND hora_inicio <= CURRENT_TIME))
        FROM atividades
        WHERE id = %s
    """, (id_atividade,))

    linha = cursor.fetchone()

    cursor.close()
    banco.close()

    return linha


def procurar_conflito_atividade(professor, turma, data, inicio, fim, ignorar_id=None):
    # o mesmo professor ou a mesma turma nao podem estar em duas atividades ao mesmo tempo.
    # Devolve "professor", "turma" ou None
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT
            BOOL_OR(professor_id = %s),
            BOOL_OR(turma_id = %s)
        FROM atividades
        WHERE (professor_id = %s OR turma_id = %s)
        AND data = %s
        AND %s < hora_fim
        AND %s > hora_inicio
        AND (%s IS NULL OR id <> %s)
    """, (professor, turma, professor, turma, data, inicio, fim, ignorar_id, ignorar_id))

    linha = cursor.fetchone()

    cursor.close()
    banco.close()

    if linha and linha[0]:
        return "professor"

    if linha and linha[1]:
        return "turma"

    return None


def recursos_sem_vaga(id_atividade, data, inicio, fim):
    # ao mudar o horario de uma atividade, confere se os recursos que ela ja tem
    # continuam livres no horario novo. Devolve os nomes dos que nao cabem.
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT r.nome
        FROM alocacoes al
        JOIN recursos r ON r.id = al.recurso_id
        WHERE al.atividade_id = %s
        AND (
            r.status = 'manutencao'
            OR (
                SELECT COUNT(*)
                FROM alocacoes outra
                JOIN atividades a ON a.id = outra.atividade_id
                WHERE outra.recurso_id = r.id
                AND a.id <> %s
                AND a.data = %s
                AND %s < a.hora_fim
                AND %s > a.hora_inicio
            ) >= COALESCE(r.quantidade, 1)
        )
        ORDER BY r.nome
    """, (id_atividade, id_atividade, data, inicio, fim))

    nomes = [linha[0] for linha in cursor.fetchall()]

    cursor.close()
    banco.close()

    return nomes


def alterar_atividade(id_atividade, disciplina, turma, professor, descricao, data, inicio, fim):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        UPDATE atividades
        SET disciplina_id = %s, turma_id = %s, professor_id = %s, descricao = %s,
            data = %s, hora_inicio = %s, hora_fim = %s
        WHERE id = %s
    """, (disciplina, turma, professor, descricao, data, inicio, fim, id_atividade))

    banco.commit()

    cursor.close()
    banco.close()


def cancelar_atividade(id_atividade):
    # as alocacoes da atividade saem junto (ON DELETE CASCADE): os recursos ficam livres
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("DELETE FROM atividades WHERE id = %s", (id_atividade,))

    banco.commit()

    cursor.close()
    banco.close()


def descrever_atividade(id_atividade):
    # texto legivel para log e mensagens: "Banco de Dados · 7A · 22/09/2026 08:00-10:00 · Prof. Ana"
    try:
        banco = conectar()
        cursor = banco.cursor()

        cursor.execute("""
            SELECT d.nome, t.nome, a.data, a.hora_inicio, a.hora_fim, p.nome
            FROM atividades a
            JOIN disciplinas d ON d.id = a.disciplina_id
            JOIN turmas t ON t.id = a.turma_id
            JOIN professores p ON p.id = a.professor_id
            WHERE a.id = %s
        """, (id_atividade,))

        linha = cursor.fetchone()

        cursor.close()
        banco.close()
    except Exception:
        linha = None

    if not linha:
        return f"atividade {id_atividade}"

    data = linha[2].strftime("%d/%m/%Y") if hasattr(linha[2], "strftime") else str(linha[2])
    inicio = str(linha[3])[:5]
    fim = str(linha[4])[:5]

    return f"{linha[0]} · {linha[1]} · {data} {inicio}-{fim} · {linha[5]}"
