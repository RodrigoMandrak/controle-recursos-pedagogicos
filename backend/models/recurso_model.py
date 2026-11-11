from banco import conectar


def buscar_recurso_por_nome(nome, ignorar_id=None):
    # usado para nao deixar cadastrar dois recursos com o mesmo nome
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT id
        FROM recursos
        WHERE LOWER(nome) = LOWER(%s)
        AND ativo = TRUE
        AND (%s IS NULL OR id <> %s)
    """, (nome, ignorar_id, ignorar_id))

    recurso = cursor.fetchone()

    cursor.close()
    banco.close()

    return recurso


def cadastrar_recurso(nome, tipo, quantidade):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        INSERT INTO recursos (nome, tipo, quantidade, status)
        VALUES (%s, %s, %s, 'disponivel')
        RETURNING id
    """, (nome, tipo, quantidade))

    novo_id = cursor.fetchone()[0]
    banco.commit()

    cursor.close()
    banco.close()

    return novo_id


def alterar_recurso(id_recurso, nome, tipo, quantidade, status):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        UPDATE recursos
        SET nome = %s, tipo = %s, quantidade = %s, status = %s
        WHERE id = %s
        AND ativo = TRUE
    """, (nome, tipo, quantidade, status, id_recurso))

    alterou = cursor.rowcount
    banco.commit()

    cursor.close()
    banco.close()

    return alterou > 0


def contar_alocacoes_do_recurso(id_recurso):
    # devolve (reservas que ainda vao acontecer ou estao acontecendo, reservas antigas)
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) FILTER (
                WHERE a.data > CURRENT_DATE
                OR (a.data = CURRENT_DATE AND a.hora_fim > CURRENT_TIME)
            ) AS futuras,
            COUNT(*) FILTER (
                WHERE a.data < CURRENT_DATE
                OR (a.data = CURRENT_DATE AND a.hora_fim <= CURRENT_TIME)
            ) AS antigas
        FROM alocacoes al
        JOIN atividades a ON a.id = al.atividade_id
        WHERE al.recurso_id = %s
    """, (id_recurso,))

    linha = cursor.fetchone()

    cursor.close()
    banco.close()

    return (linha[0] or 0, linha[1] or 0) if linha else (0, 0)


def excluir_recurso(id_recurso, arquivar):
    # arquivar = True: o recurso ja foi usado em aulas antigas.
    # Ele some da lista e nao pode mais ser alocado, mas continua no banco
    # para o historico (alocacoes antigas, dashboard e logs) nao quebrar.
    # arquivar = False: nunca foi usado, apaga de vez.
    banco = conectar()
    cursor = banco.cursor()

    if arquivar:
        cursor.execute("UPDATE recursos SET ativo = FALSE WHERE id = %s AND ativo = TRUE", (id_recurso,))
    else:
        cursor.execute("DELETE FROM recursos WHERE id = %s AND ativo = TRUE", (id_recurso,))

    excluiu = cursor.rowcount
    banco.commit()

    cursor.close()
    banco.close()

    return excluiu > 0


def buscar_proximas_reservas(id_recurso):
    # reservas do recurso que ainda vao acontecer (ou estao acontecendo agora)
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT a.data, a.hora_inicio, a.hora_fim, d.nome, t.nome, p.nome
        FROM alocacoes al
        JOIN atividades a ON a.id = al.atividade_id
        LEFT JOIN disciplinas d ON d.id = a.disciplina_id
        LEFT JOIN turmas t ON t.id = a.turma_id
        LEFT JOIN professores p ON p.id = a.professor_id
        WHERE al.recurso_id = %s
        AND (a.data > CURRENT_DATE
             OR (a.data = CURRENT_DATE AND a.hora_fim > CURRENT_TIME))
        ORDER BY a.data, a.hora_inicio
    """, (id_recurso,))

    dados = cursor.fetchall()

    cursor.close()
    banco.close()

    return [{
        "data": str(item[0]),
        "hora_inicio": str(item[1])[:5],
        "hora_fim": str(item[2])[:5],
        "disciplina": item[3],
        "turma": item[4],
        "professor": item[5]
    } for item in dados]
