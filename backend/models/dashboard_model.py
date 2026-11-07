from banco import conectar


def montar_filtro(usuario_id, perfil):
    # coordenador ve os numeros de todos
    # professor ve somente as atividades que ele cadastrou
    if perfil == "coordenador":
        return "", ()

    return "WHERE a.usuario_id = %s", (usuario_id,)


def buscar_indicadores(usuario_id, perfil):
    banco = conectar()
    cursor = banco.cursor()

    filtro, parametros = montar_filtro(usuario_id, perfil)

    # total de atividades
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM atividades a
        {filtro}
    """, parametros)
    total_atividades = cursor.fetchone()[0]

    # total de recursos alocados
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM alocacoes al
        JOIN atividades a ON a.id = al.atividade_id
        {filtro}
    """, parametros)
    total_alocacoes = cursor.fetchone()[0]

    # atividades marcadas para hoje
    filtro_hoje = "WHERE a.data = CURRENT_DATE"
    if filtro:
        filtro_hoje = filtro + " AND a.data = CURRENT_DATE"

    cursor.execute(f"""
        SELECT COUNT(*)
        FROM atividades a
        {filtro_hoje}
    """, parametros)
    atividades_hoje = cursor.fetchone()[0]

    # atividades sem nenhum recurso alocado
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM atividades a
        LEFT JOIN alocacoes al ON al.atividade_id = a.id
        {filtro + " AND" if filtro else "WHERE"} al.id IS NULL
    """, parametros)
    sem_recurso = cursor.fetchone()[0]

    # recursos cadastrados e quantos ja foram usados
    cursor.execute("SELECT COUNT(*) FROM recursos")
    total_recursos = cursor.fetchone()[0]

    cursor.execute(f"""
        SELECT COUNT(DISTINCT al.recurso_id)
        FROM alocacoes al
        JOIN atividades a ON a.id = al.atividade_id
        {filtro}
    """, parametros)
    recursos_usados = cursor.fetchone()[0]

    cursor.close()
    banco.close()

    return {
        "total_atividades": total_atividades,
        "total_alocacoes": total_alocacoes,
        "atividades_hoje": atividades_hoje,
        "sem_recurso": sem_recurso,
        "total_recursos": total_recursos,
        "recursos_usados": recursos_usados
    }


def buscar_recursos_mais_usados(usuario_id, perfil):
    banco = conectar()
    cursor = banco.cursor()

    filtro, parametros = montar_filtro(usuario_id, perfil)

    cursor.execute(f"""
        SELECT r.nome, r.tipo, COUNT(*) AS total
        FROM alocacoes al
        JOIN atividades a ON a.id = al.atividade_id
        JOIN recursos r ON r.id = al.recurso_id
        {filtro}
        GROUP BY r.nome, r.tipo
        ORDER BY total DESC, r.nome
        LIMIT 5
    """, parametros)

    dados = cursor.fetchall()
    lista = []

    for item in dados:
        lista.append({
            "recurso": item[0],
            "tipo": item[1],
            "total": item[2]
        })

    cursor.close()
    banco.close()

    return lista


def buscar_atividades_por_disciplina(usuario_id, perfil):
    banco = conectar()
    cursor = banco.cursor()

    filtro, parametros = montar_filtro(usuario_id, perfil)

    cursor.execute(f"""
        SELECT d.nome, COUNT(*) AS total
        FROM atividades a
        JOIN disciplinas d ON d.id = a.disciplina_id
        {filtro}
        GROUP BY d.nome
        ORDER BY total DESC, d.nome
    """, parametros)

    dados = cursor.fetchall()
    lista = []

    for item in dados:
        lista.append({
            "disciplina": item[0],
            "total": item[1]
        })

    cursor.close()
    banco.close()

    return lista


def buscar_atividades_por_mes(usuario_id, perfil):
    banco = conectar()
    cursor = banco.cursor()

    filtro, parametros = montar_filtro(usuario_id, perfil)

    # gera 6 meses: 4 meses para tras, o mes atual e o proximo
    # assim os meses sem atividade tambem aparecem com zero
    condicao = "date_trunc('month', a.data) = mes"
    if filtro:
        condicao += " AND a.usuario_id = %s"

    cursor.execute(f"""
        SELECT mes::date, COUNT(a.id) AS total
        FROM generate_series(
            date_trunc('month', CURRENT_DATE) - INTERVAL '4 months',
            date_trunc('month', CURRENT_DATE) + INTERVAL '1 month',
            INTERVAL '1 month'
        ) AS mes
        LEFT JOIN atividades a ON {condicao}
        GROUP BY mes
        ORDER BY mes
    """, parametros)

    dados = cursor.fetchall()
    lista = []

    for item in dados:
        lista.append({
            "mes": item[0].strftime("%Y-%m"),
            "total": item[1]
        })

    cursor.close()
    banco.close()

    return lista
