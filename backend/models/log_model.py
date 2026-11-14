from banco import conectar


def registrar_log(usuario_id, acao, detalhes=None):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        INSERT INTO logs
        (usuario_id, acao, detalhes)
        VALUES (%s, %s, %s)
    """, (
        usuario_id,
        acao,
        detalhes
    ))

    banco.commit()

    cursor.close()
    banco.close()


def montar_filtros(acao=None, usuario=None, texto=None, data_inicio=None, data_fim=None):
    # filtros opcionais: tipo de acao, nome de quem fez, texto nos detalhes e periodo
    condicoes = []
    valores = []

    if acao:
        condicoes.append("l.acao = %s")
        valores.append(acao)

    if usuario:
        condicoes.append("u.nome ILIKE %s")
        valores.append(f"%{usuario}%")

    if texto:
        condicoes.append("l.detalhes ILIKE %s")
        valores.append(f"%{texto}%")

    if data_inicio:
        condicoes.append("l.data_hora::date >= %s")
        valores.append(data_inicio)

    if data_fim:
        condicoes.append("l.data_hora::date <= %s")
        valores.append(data_fim)

    onde = ("WHERE " + " AND ".join(condicoes)) if condicoes else ""

    return onde, valores


def contar_logs(**filtros):
    onde, valores = montar_filtros(**filtros)

    banco = conectar()
    cursor = banco.cursor()

    cursor.execute(f"""
        SELECT COUNT(*)
        FROM logs l
        LEFT JOIN usuarios u ON u.id = l.usuario_id
        {onde}
    """, tuple(valores))

    linha = cursor.fetchone()

    cursor.close()
    banco.close()

    return (linha[0] or 0) if linha else 0


def buscar_logs(limite=20, deslocamento=0, **filtros):
    # uma pagina por vez (LIMIT/OFFSET): a tela nao trava com milhares de registros
    onde, valores = montar_filtros(**filtros)

    banco = conectar()
    cursor = banco.cursor()

    cursor.execute(f"""
        SELECT
            l.id,
            u.nome,
            l.acao,
            l.detalhes,
            l.data_hora
        FROM logs l
        LEFT JOIN usuarios u ON u.id = l.usuario_id
        {onde}
        ORDER BY l.id DESC
        LIMIT %s OFFSET %s
    """, tuple(valores) + (limite, deslocamento))

    dados = cursor.fetchall()

    lista = []

    for item in dados:
        lista.append({
            "id": item[0],
            "usuario": item[1],
            "acao": item[2],
            "detalhes": item[3],
            "data_hora": str(item[4])
        })

    cursor.close()
    banco.close()

    return lista


def buscar_acoes():
    # tipos de acao que ja aparecem no log (para o filtro da tela)
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("SELECT DISTINCT acao FROM logs ORDER BY acao")
    acoes = [linha[0] for linha in cursor.fetchall()]

    cursor.close()
    banco.close()

    return acoes
