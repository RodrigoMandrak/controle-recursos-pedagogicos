from datetime import date

from banco import conectar


def montar_filtro(usuario_id, perfil, filtros=None, com_periodo=True):
    # devolve o WHERE do dashboard e os valores dele
    # filtros (opcional): {"inicio": date, "fim": date, "disciplina": id}
    filtros = filtros or {}
    condicoes = []
    parametros = []

    # coordenador ve os numeros de todos
    # professor ve somente as atividades que ele cadastrou
    if perfil != "coordenador":
        condicoes.append("a.usuario_id = %s")
        parametros.append(usuario_id)

    # filtro de periodo escolhido na tela
    if com_periodo and filtros.get("inicio"):
        condicoes.append("a.data >= %s")
        parametros.append(filtros["inicio"])

    if com_periodo and filtros.get("fim"):
        condicoes.append("a.data <= %s")
        parametros.append(filtros["fim"])

    # filtro de disciplina escolhido na tela
    if filtros.get("disciplina"):
        condicoes.append("a.disciplina_id = %s")
        parametros.append(filtros["disciplina"])

    if not condicoes:
        return "", ()

    return "WHERE " + " AND ".join(condicoes), tuple(parametros)


def primeiro_dia_do_mes(dia):
    return dia.replace(day=1)


def somar_meses(dia, meses):
    # trabalha sempre com o dia 1, entao nao tem problema de mes com 30 ou 31 dias
    total = dia.year * 12 + (dia.month - 1) + meses
    return date(total // 12, total % 12 + 1, 1)


def meses_do_grafico(filtros=None):
    # sem filtro: 4 meses para tras, o mes atual e o proximo (igual era antes)
    filtros = filtros or {}
    inicio = filtros.get("inicio")
    fim = filtros.get("fim")
    mes_atual = primeiro_dia_do_mes(date.today())

    if inicio and fim:
        return primeiro_dia_do_mes(inicio), primeiro_dia_do_mes(fim)

    if inicio:
        primeiro = primeiro_dia_do_mes(inicio)
        return primeiro, somar_meses(primeiro, 5)

    if fim:
        ultimo = primeiro_dia_do_mes(fim)
        return somar_meses(ultimo, -5), ultimo

    return somar_meses(mes_atual, -4), somar_meses(mes_atual, 1)


def buscar_indicadores(usuario_id, perfil, filtros=None):
    banco = conectar()
    cursor = banco.cursor()

    filtro, parametros = montar_filtro(usuario_id, perfil, filtros)

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
    # aqui o periodo nao entra (hoje e sempre hoje), so o perfil e a disciplina
    filtro_sem_periodo, parametros_hoje = montar_filtro(usuario_id, perfil, filtros, com_periodo=False)
    filtro_hoje = "WHERE a.data = CURRENT_DATE"
    if filtro_sem_periodo:
        filtro_hoje = filtro_sem_periodo + " AND a.data = CURRENT_DATE"

    cursor.execute(f"""
        SELECT COUNT(*)
        FROM atividades a
        {filtro_hoje}
    """, parametros_hoje)
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
    cursor.execute("SELECT COUNT(*) FROM recursos WHERE ativo = TRUE")
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


def buscar_recursos_mais_usados(usuario_id, perfil, filtros=None):
    banco = conectar()
    cursor = banco.cursor()

    filtro, parametros = montar_filtro(usuario_id, perfil, filtros)

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


def buscar_atividades_por_disciplina(usuario_id, perfil, filtros=None):
    banco = conectar()
    cursor = banco.cursor()

    filtro, parametros = montar_filtro(usuario_id, perfil, filtros)

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


def buscar_atividades_por_mes(usuario_id, perfil, filtros=None):
    banco = conectar()
    cursor = banco.cursor()

    filtro, parametros = montar_filtro(usuario_id, perfil, filtros)

    # gera um mes por linha no periodo do grafico
    # assim os meses sem atividade tambem aparecem com zero
    primeiro_mes, ultimo_mes = meses_do_grafico(filtros)

    condicao = "date_trunc('month', a.data) = mes"
    if filtro:
        # as mesmas condicoes do WHERE entram no JOIN (perfil, periodo e disciplina)
        condicao += " AND " + filtro.replace("WHERE ", "", 1)

    cursor.execute(f"""
        SELECT mes::date, COUNT(a.id) AS total
        FROM generate_series(
            %s::date,
            %s::date,
            INTERVAL '1 month'
        ) AS mes
        LEFT JOIN atividades a ON {condicao}
        GROUP BY mes
        ORDER BY mes
    """, (primeiro_mes, ultimo_mes) + parametros)

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
