from banco import conectar

# tabelas que o coordenador pode cadastrar pela tela.
# coluna = campo da tabela atividades que aponta para ela
TABELAS = {
    "disciplinas": "disciplina_id",
    "turmas": "turma_id",
    "professores": "professor_id",
}


def nome_existe(tabela, nome, ignorar_id=None):
    # nao deixa cadastrar dois itens ativos com o mesmo nome
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute(f"""
        SELECT id
        FROM {tabela}
        WHERE LOWER(nome) = LOWER(%s)
        AND ativo = TRUE
        AND (%s IS NULL OR id <> %s)
    """, (nome, ignorar_id, ignorar_id))

    linha = cursor.fetchone()

    cursor.close()
    banco.close()

    return linha is not None


def cadastrar(tabela, nome):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute(f"INSERT INTO {tabela} (nome) VALUES (%s) RETURNING id", (nome,))
    novo_id = cursor.fetchone()[0]
    banco.commit()

    cursor.close()
    banco.close()

    return novo_id


def renomear(tabela, id_item, nome):
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute(f"UPDATE {tabela} SET nome = %s WHERE id = %s AND ativo = TRUE", (nome, id_item))
    alterou = cursor.rowcount
    banco.commit()

    cursor.close()
    banco.close()

    return alterou > 0


def contar_atividades(tabela, id_item):
    # devolve (atividades que ainda vao acontecer, atividades que ja passaram)
    coluna = TABELAS[tabela]
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute(f"""
        SELECT
            COUNT(*) FILTER (
                WHERE data > CURRENT_DATE
                OR (data = CURRENT_DATE AND hora_fim > CURRENT_TIME)
            ),
            COUNT(*) FILTER (
                WHERE data < CURRENT_DATE
                OR (data = CURRENT_DATE AND hora_fim <= CURRENT_TIME)
            )
        FROM atividades
        WHERE {coluna} = %s
    """, (id_item,))

    linha = cursor.fetchone()

    cursor.close()
    banco.close()

    return (linha[0] or 0, linha[1] or 0) if linha else (0, 0)


def excluir(tabela, id_item, arquivar):
    # arquivar = True: ja tem aulas antigas -> some das listas, mas o historico continua
    # arquivar = False: nunca foi usado -> apaga de vez
    banco = conectar()
    cursor = banco.cursor()

    if arquivar:
        cursor.execute(f"UPDATE {tabela} SET ativo = FALSE WHERE id = %s AND ativo = TRUE", (id_item,))
    else:
        cursor.execute(f"DELETE FROM {tabela} WHERE id = %s AND ativo = TRUE", (id_item,))

    excluiu = cursor.rowcount
    banco.commit()

    cursor.close()
    banco.close()

    return excluiu > 0


def professor_tem_conta(id_professor):
    # professor ligado a uma conta de login nao pode ser apagado pela lista:
    # a conta dele deixaria de ter um professor para cadastrar atividades
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT 1 FROM professores
        WHERE id = %s AND ativo = TRUE AND usuario_id IS NOT NULL
    """, (id_professor,))

    linha = cursor.fetchone()

    cursor.close()
    banco.close()

    return linha is not None


def itens_ativos(disciplina, turma, professor):
    # confere se disciplina, turma e professor existem e nao foram excluidos
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT
            EXISTS (SELECT 1 FROM disciplinas WHERE id = %s AND ativo = TRUE),
            EXISTS (SELECT 1 FROM turmas WHERE id = %s AND ativo = TRUE),
            EXISTS (SELECT 1 FROM professores WHERE id = %s AND ativo = TRUE)
    """, (disciplina, turma, professor))

    linha = cursor.fetchone()

    cursor.close()
    banco.close()

    return bool(linha and all(linha))


def buscar_nome(tabela, id_item):
    # nome atual do item (para o log dizer "Turma 7A excluida" em vez do numero)
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute(f"SELECT nome FROM {tabela} WHERE id = %s", (id_item,))
    linha = cursor.fetchone()

    cursor.close()
    banco.close()

    return linha[0] if linha else None
