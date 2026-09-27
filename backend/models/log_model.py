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


def buscar_logs():
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT
            l.id,
            u.nome,
            l.acao,
            l.detalhes,
            l.data_hora
        FROM logs l
        LEFT JOIN usuarios u ON u.id = l.usuario_id
        ORDER BY l.id DESC
    """)

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