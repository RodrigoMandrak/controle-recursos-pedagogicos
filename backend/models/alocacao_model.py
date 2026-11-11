from banco import conectar


def buscar_recursos():
    banco = conectar()
    cursor = banco.cursor()

    # quantidade = quantas unidades o recurso tem (ex.: 3 notebooks)
    # em_uso_agora = quantas unidades estao numa atividade acontecendo neste momento
    cursor.execute("""
        SELECT r.id, r.nome, r.tipo, r.status, r.quantidade,
               (
                   SELECT COUNT(*)
                   FROM alocacoes al
                   JOIN atividades a ON a.id = al.atividade_id
                   WHERE al.recurso_id = r.id
                   AND a.data = CURRENT_DATE
                   AND CURRENT_TIME >= a.hora_inicio
                   AND CURRENT_TIME < a.hora_fim
               ) AS em_uso_agora,
               (
                   SELECT COUNT(*)
                   FROM alocacoes al
                   JOIN atividades a ON a.id = al.atividade_id
                   WHERE al.recurso_id = r.id
                   AND (a.data > CURRENT_DATE
                        OR (a.data = CURRENT_DATE AND a.hora_fim > CURRENT_TIME))
               ) AS reservas_futuras
        FROM recursos r
        WHERE r.ativo = TRUE
        ORDER BY r.nome
    """)

    dados = cursor.fetchall()
    lista = []

    for recurso in dados:
        lista.append({
            "id": recurso[0],
            "nome": recurso[1],
            "tipo": recurso[2],
            "status": recurso[3],
            "quantidade": recurso[4],
            "em_uso_agora": recurso[5],
            "reservas_futuras": recurso[6]
        })

    cursor.close()
    banco.close()

    return lista


def buscar_recurso(id_recurso):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT id
        FROM recursos
        WHERE id = %s
        AND ativo = TRUE
    """, (id_recurso,))

    recurso = cursor.fetchone()

    cursor.close()
    banco.close()

    return recurso


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


def buscar_usuario_atividade(id_atividade):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT usuario_id
        FROM atividades
        WHERE id = %s
    """, (id_atividade,))

    usuario = cursor.fetchone()

    cursor.close()
    banco.close()

    return usuario


def procurar_conflito_recurso(recurso, data, inicio, fim):
    # o recurso tem um estoque (quantidade). Conta quantas unidades ja estao
    # reservadas em atividades que batem com esse horario.
    # Devolve (em_uso, quantidade, status) quando NAO pode alocar, ou None quando pode.
    # Quando a aula termina, ela para de bater com os proximos horarios,
    # entao a unidade volta a ficar livre sozinha.
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT r.quantidade, r.status,
               (
                   SELECT COUNT(*)
                   FROM alocacoes al
                   JOIN atividades a ON a.id = al.atividade_id
                   WHERE al.recurso_id = r.id
                   AND a.data = %s
                   AND %s < a.hora_fim
                   AND %s > a.hora_inicio
               ) AS em_uso
        FROM recursos r
        WHERE r.id = %s
    """, (data, inicio, fim, recurso))

    linha = cursor.fetchone()

    cursor.close()
    banco.close()

    if not linha:
        return None

    quantidade, status, em_uso = linha[0] or 1, linha[1], linha[2]

    if status == "manutencao" or em_uso >= quantidade:
        return (em_uso, quantidade, status)

    return None


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


def contar_uso_no_horario(cursor, atividade, recurso):
    # conta as unidades do recurso ja reservadas no horario dessa atividade
    cursor.execute("""
        SELECT COUNT(*)
        FROM alocacoes al
        JOIN atividades a ON a.id = al.atividade_id
        JOIN atividades nova ON nova.id = %s
        WHERE al.recurso_id = %s
        AND a.data = nova.data
        AND nova.hora_inicio < a.hora_fim
        AND nova.hora_fim > a.hora_inicio
    """, (atividade, recurso))

    linha = cursor.fetchone()
    return linha[0] if linha else 0


def salvar_alocacao(atividade, recurso):
    # Trava o recurso (FOR UPDATE) e confere o estoque de novo na mesma transacao.
    # Assim, se dois professores clicarem em "Alocar" no mesmo instante,
    # o segundo espera o primeiro terminar e ve a unidade ja ocupada.
    # Devolve True quando salvou e False quando o recurso acabou.
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("SELECT quantidade FROM recursos WHERE id = %s FOR UPDATE", (recurso,))
    linha = cursor.fetchone()
    quantidade = linha[0] if linha and linha[0] else 1

    if contar_uso_no_horario(cursor, atividade, recurso) >= quantidade:
        banco.rollback()
        cursor.close()
        banco.close()
        return False

    cursor.execute(
        "INSERT INTO alocacoes (atividade_id, recurso_id) VALUES (%s, %s)",
        (atividade, recurso)
    )

    banco.commit()

    cursor.close()
    banco.close()

    return True


def buscar_alocacoes(usuario_id, perfil):
    banco = conectar()
    cursor = banco.cursor()

    # coordenador consegue visualizar todas
    if perfil == "coordenador":
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

    # professor visualiza somente alocacoes das atividades dele
    else:
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
            WHERE a.usuario_id = %s
            ORDER BY al.id DESC
        """, (usuario_id,))

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
        SELECT al.atividade_id, al.recurso_id, a.usuario_id
        FROM alocacoes al
        JOIN atividades a ON a.id = al.atividade_id
        WHERE al.id = %s
    """, (id_alocacao,))

    alocacao = cursor.fetchone()

    cursor.close()
    banco.close()

    return alocacao


def alterar_alocacao(id_alocacao, recurso):
    # mesma trava do salvar_alocacao: confere o estoque do novo recurso na mesma transacao
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("SELECT quantidade FROM recursos WHERE id = %s FOR UPDATE", (recurso,))
    linha = cursor.fetchone()
    quantidade = linha[0] if linha and linha[0] else 1

    cursor.execute("SELECT atividade_id FROM alocacoes WHERE id = %s", (id_alocacao,))
    linha = cursor.fetchone()

    if linha and contar_uso_no_horario(cursor, linha[0], recurso) >= quantidade:
        banco.rollback()
        cursor.close()
        banco.close()
        return False

    cursor.execute("""
        UPDATE alocacoes
        SET recurso_id = %s
        WHERE id = %s
    """, (recurso, id_alocacao))

    banco.commit()

    cursor.close()
    banco.close()

    return True


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


def mensagem_recurso_indisponivel(conflito):
    # conflito = (em_uso, quantidade, status)
    if len(conflito) >= 3 and conflito[2] == "manutencao":
        return "Esse recurso esta em manutencao e nao pode ser alocado"

    if len(conflito) >= 2 and conflito[1] and conflito[1] > 1:
        return f"Recurso indisponivel nesse horario: as {conflito[1]} unidades ja estao reservadas"

    return "Esse recurso ja esta sendo usado nesse horario"


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
        return mensagem_recurso_indisponivel(conflito_recurso)

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