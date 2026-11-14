"""
Deixa o banco com cara de escola de verdade para a apresentacao:

- organiza as disciplinas: 10 disciplinas de escola
- organiza os recursos: 10 recursos que existem em escola (com estoque)
- cria cerca de 300 atividades que JA ACONTECERAM, com recursos alocados
  e o historico no log, para o dashboard e a auditoria ficarem cheios

O que ja esta cadastrado e aproveitado: um nome que nao e de escola
(ex.: "Banco de Dados") e renomeado para uma disciplina da lista, entao as
atividades antigas continuam ligadas a ele. Nada que ja existe e apagado.
Turmas, professores e contas de acesso nao sao alterados.

Uso (dentro da pasta backend, com o venv):  python turbinar_demo.py
Ele mostra em qual banco vai mexer e pede confirmacao antes.
"""

import os
import random
import sys
import unicodedata
from datetime import date, datetime, time, timedelta

PASTA = os.path.dirname(os.path.abspath(__file__))
os.chdir(PASTA)
sys.path.insert(0, PASTA)

from banco import JUNTA_ATIVIDADE, ROTULO_SQL, atualizar_estrutura, conectar  # noqa: E402

DISCIPLINAS = [
    "Língua Portuguesa", "Matemática", "Ciências", "História", "Geografia",
    "Língua Inglesa", "Arte", "Educação Física", "Informática Educativa", "Robótica",
]

# (nome, tipo, quantidade)
RECURSOS = [
    ("Laboratório de Informática", "laboratorio", 1),
    ("Laboratório de Ciências", "laboratorio", 1),
    ("Sala de Vídeo", "sala", 1),
    ("Biblioteca", "sala", 1),
    ("Quadra Poliesportiva", "sala", 1),
    ("Projetor Multimídia", "equipamento", 3),
    ("Notebooks (kit com 30)", "equipamento", 2),
    ("Caixa de Som Portátil", "equipamento", 2),
    ("Kit de Robótica", "material", 4),
    ("Microscópios (kit)", "material", 2),
]

# recurso que combina com cada disciplina (o primeiro e o mais usado)
RECURSO_DA_DISCIPLINA = {
    "Língua Portuguesa": ["Biblioteca", "Projetor Multimídia", "Sala de Vídeo"],
    "Matemática": ["Projetor Multimídia", "Notebooks (kit com 30)", "Laboratório de Informática"],
    "Ciências": ["Laboratório de Ciências", "Microscópios (kit)", "Projetor Multimídia"],
    "História": ["Sala de Vídeo", "Projetor Multimídia", "Biblioteca"],
    "Geografia": ["Projetor Multimídia", "Sala de Vídeo", "Notebooks (kit com 30)"],
    "Língua Inglesa": ["Caixa de Som Portátil", "Sala de Vídeo", "Projetor Multimídia"],
    "Arte": ["Sala de Vídeo", "Caixa de Som Portátil", "Projetor Multimídia"],
    "Educação Física": ["Quadra Poliesportiva", "Caixa de Som Portátil"],
    "Informática Educativa": ["Laboratório de Informática", "Notebooks (kit com 30)"],
    "Robótica": ["Kit de Robótica", "Laboratório de Informática", "Notebooks (kit com 30)"],
}

DESCRICOES = {
    "Língua Portuguesa": ["Leitura e interpretação de texto", "Produção de redação", "Roda de leitura"],
    "Matemática": ["Exercícios de frações", "Geometria com materiais concretos", "Revisão para a prova"],
    "Ciências": ["Experimento de densidade", "Observação de células no microscópio", "Feira de ciências"],
    "História": ["Documentário sobre o Brasil Colônia", "Seminário da turma", "Linha do tempo em grupo"],
    "Geografia": ["Mapas e coordenadas", "Clima e vegetação", "Apresentação de pesquisa"],
    "Língua Inglesa": ["Listening com música", "Diálogos em dupla", "Filme legendado"],
    "Arte": ["Apresentação de teatro", "Estudo de obras de arte", "Ensaio da apresentação"],
    "Educação Física": ["Jogos de vôlei", "Circuito de atividades", "Festival de handebol"],
    "Informática Educativa": ["Planilhas no computador", "Pesquisa segura na internet", "Digitação de texto"],
    "Robótica": ["Montagem do robô seguidor de linha", "Programação em blocos", "Desafio de robótica"],
}

# horarios de escola (manha e tarde)
HORARIOS = [("07:30", "09:10"), ("09:30", "11:10"), ("13:00", "14:40"), ("15:00", "16:40")]

QUANTIDADE = 300


def normalizar(texto):
    sem_acento = unicodedata.normalize("NFD", str(texto or "")).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


def organizar(cursor, tabela, alvos, extras=None, tipo_alvo=None):
    """
    Deixa a tabela so com os nomes da lista (mais os criados pelo coordenador
    que tambem estao na lista). Itens com nome fora da lista sao renomeados
    para um nome que esta faltando; se sobrar, sao arquivados.
    extras: funcao que recebe (id, nome_alvo) para atualizar outras colunas.
    tipo_alvo: {nome: tipo} (recursos). Um projetor vira o projetor da lista, um laboratorio vira laboratorio...
    """
    if tipo_alvo:
        cursor.execute(f"SELECT id, nome, tipo FROM {tabela} WHERE ativo = TRUE ORDER BY id")
        existentes = cursor.fetchall()
    else:
        cursor.execute(f"SELECT id, nome FROM {tabela} WHERE ativo = TRUE ORDER BY id")
        existentes = [(id_item, nome, None) for id_item, nome in cursor.fetchall()]

    nomes_alvo = {normalizar(nome): nome for nome in alvos}
    ja_tem = {}
    sobrando = []

    for id_item, nome, tipo in existentes:
        chave = normalizar(nome)
        if chave in nomes_alvo and chave not in ja_tem:
            ja_tem[chave] = id_item
        else:
            sobrando.append((id_item, nome, tipo))

    faltando = [nome for chave, nome in nomes_alvo.items() if chave not in ja_tem]
    renomeados, arquivados, criados = 0, 0, 0

    for id_item, nome, tipo in sobrando:
        if faltando:
            # prefere um nome do mesmo tipo (ex.: "Projetor Epson" -> "Projetor Multimidia")
            parecidos = [alvo for alvo in faltando if tipo_alvo and tipo_alvo.get(alvo) == tipo]
            if tipo_alvo and "projetor" in normalizar(nome):
                parecidos = [alvo for alvo in faltando if "projetor" in normalizar(alvo)] or parecidos
            if tipo_alvo and "notebook" in normalizar(nome):
                parecidos = [alvo for alvo in faltando if "notebook" in normalizar(alvo)] or parecidos
            novo = (parecidos or faltando)[0]
            faltando.remove(novo)
            cursor.execute(f"UPDATE {tabela} SET nome = %s WHERE id = %s", (novo, id_item))
            ja_tem[normalizar(novo)] = id_item
            renomeados += 1
        else:
            # mais itens do que a lista: some das listas, mas o historico continua
            cursor.execute(f"UPDATE {tabela} SET ativo = FALSE WHERE id = %s", (id_item,))
            arquivados += 1

    for nome in faltando:
        if tipo_alvo:
            # status sempre informado: em alguns bancos a coluna nao tem valor padrao
            cursor.execute(f"INSERT INTO {tabela} (nome, tipo, status) VALUES (%s, %s, 'disponivel') RETURNING id",
                           (nome, tipo_alvo[nome]))
        else:
            cursor.execute(f"INSERT INTO {tabela} (nome) VALUES (%s) RETURNING id", (nome,))
        ja_tem[normalizar(nome)] = cursor.fetchone()[0]
        criados += 1

    if extras:
        for nome in alvos:
            extras(ja_tem[normalizar(nome)], nome)

    print(f"  {tabela}: {renomeados} renomeado(s), {criados} criado(s), {arquivados} arquivado(s)")
    return {nome: ja_tem[normalizar(nome)] for nome in alvos}


def dias_uteis_passados(quantidade_dias):
    hoje = date.today()
    dia = hoje - timedelta(days=quantidade_dias)
    dias = []
    while dia < hoje:
        if dia.weekday() < 5:
            dias.append(dia)
        dia += timedelta(days=1)
    return dias


def bate(inicio_a, fim_a, inicio_b, fim_b):
    # mesmo teste de sobreposicao do sistema: inicio novo < fim existente E fim novo > inicio existente
    return inicio_a < fim_b and fim_a > inicio_b


def carregar_agenda(cursor, primeiro_dia):
    # o que ja existe no periodo, para conferir os conflitos sem ir ao banco a cada tentativa
    cursor.execute("""
        SELECT a.id, a.professor_id, a.turma_id, a.data, TO_CHAR(a.hora_inicio, 'HH24:MI'),
               TO_CHAR(a.hora_fim, 'HH24:MI'), al.recurso_id
        FROM atividades a
        LEFT JOIN alocacoes al ON al.atividade_id = a.id
        WHERE a.data >= %s
    """, (primeiro_dia,))

    agenda = {}
    for _, professor, turma, dia, inicio, fim, recurso in cursor.fetchall():
        agenda.setdefault(str(dia), []).append((professor, turma, inicio, fim, recurso))
    return agenda


def criar_atividades(cursor, disciplinas, recursos, estoque):
    cursor.execute("SELECT id, usuario_id FROM professores WHERE ativo = TRUE ORDER BY id")
    professores = cursor.fetchall()
    cursor.execute("SELECT id FROM turmas WHERE ativo = TRUE ORDER BY id")
    turmas = [linha[0] for linha in cursor.fetchall()]
    cursor.execute("SELECT id FROM usuarios WHERE perfil = 'coordenador' ORDER BY id LIMIT 1")
    linha = cursor.fetchone()

    if not professores or not turmas or not linha:
        print("  Faltam professores, turmas ou a conta do coordenador. Cadastre antes e rode de novo.")
        return 0

    coordenador = linha[0]
    sorteio = random.Random(2026)  # sempre o mesmo resultado, para dar para repetir
    dias = dias_uteis_passados(150)
    agenda = carregar_agenda(cursor, dias[0])
    nomes_disciplinas = list(disciplinas)
    criadas = 0
    tentativas = 0

    while criadas < QUANTIDADE and tentativas < QUANTIDADE * 30:
        tentativas += 1
        dia = sorteio.choice(dias)
        inicio, fim = sorteio.choice(HORARIOS)
        nome_disc = nomes_disciplinas[(criadas + tentativas) % len(nomes_disciplinas)]
        turma = sorteio.choice(turmas)
        professor, conta_professor = sorteio.choice(professores)

        # mesmas regras do sistema: professor e turma nao ficam em dois lugares
        no_horario = [item for item in agenda.get(str(dia), []) if bate(inicio, fim, item[2], item[3])]
        if any(item[0] == professor or item[1] == turma for item in no_horario):
            continue

        # 1 recurso quase sempre, as vezes 2; respeitando o estoque
        opcoes = RECURSO_DA_DISCIPLINA[nome_disc]
        quantos = 2 if sorteio.random() < 0.25 and len(opcoes) > 1 else 1
        escolhidos = []
        for nome_rec in opcoes:
            if len(escolhidos) == quantos:
                break
            em_uso = sum(1 for item in no_horario if item[4] == recursos[nome_rec])
            if em_uso < estoque[nome_rec]:
                escolhidos.append(nome_rec)
        if not escolhidos:
            continue

        dono = conta_professor or coordenador
        descricao = sorteio.choice(DESCRICOES[nome_disc])

        cursor.execute("""
            INSERT INTO atividades
            (disciplina_id, turma_id, professor_id, descricao, data, hora_inicio, hora_fim, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (disciplinas[nome_disc], turma, professor, descricao, dia, inicio, fim, dono))
        id_atividade = cursor.fetchone()[0]

        # historico como se tivesse sido feito pelo sistema alguns dias antes da aula
        quando = datetime.combine(dia - timedelta(days=sorteio.randint(2, 7)),
                                  time(sorteio.randint(7, 18), sorteio.randint(0, 59)))
        # mesmo texto que o sistema grava: "Ciências · 7A · 22/09/2026 07:30-09:10 · Prof. Ana"
        cursor.execute(f"SELECT {ROTULO_SQL} FROM atividades a {JUNTA_ATIVIDADE} WHERE a.id = %s",
                       (id_atividade,))
        rotulo = cursor.fetchone()[0]
        logs = [(dono, "CADASTRO_ATIVIDADE", rotulo, quando)]

        for minuto, nome_rec in enumerate(escolhidos, start=1):
            cursor.execute("INSERT INTO alocacoes (atividade_id, recurso_id) VALUES (%s, %s)",
                           (id_atividade, recursos[nome_rec]))
            logs.append((dono, "ALOCACAO_RECURSO", f"{nome_rec} reservado para {rotulo}",
                         quando + timedelta(minutes=2 * minuto)))

        for usuario, acao, detalhes, momento in logs:
            cursor.execute("INSERT INTO logs (usuario_id, acao, detalhes, data_hora) VALUES (%s, %s, %s, %s)",
                           (usuario, acao, detalhes, momento))

        for nome_rec in escolhidos:
            agenda.setdefault(str(dia), []).append((professor, turma, inicio, fim, recursos[nome_rec]))

        criadas += 1

    return criadas


def main():
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PASTA, ".env"))

    print("Banco que vai ser alterado:")
    print(f"  servidor: {os.getenv('DB_HOST')}  |  banco: {os.getenv('DB_NAME')}")
    resposta = input("Organizar disciplinas e recursos e criar ~300 atividades antigas? Digite SIM: ")
    if resposta.strip().upper() != "SIM":
        print("Cancelado, nada foi alterado.")
        return

    # garante as colunas novas (ativo, quantidade...) antes de mexer
    atualizar_estrutura()

    banco = conectar()
    cursor = banco.cursor()

    try:
        print("\nOrganizando...")
        disciplinas = organizar(cursor, "disciplinas", DISCIPLINAS)

        def ajustar_recurso(id_recurso, nome):
            _, tipo, quantidade = next(item for item in RECURSOS if item[0] == nome)
            cursor.execute("UPDATE recursos SET tipo = %s, quantidade = %s WHERE id = %s",
                           (tipo, quantidade, id_recurso))

        recursos = organizar(cursor, "recursos", [item[0] for item in RECURSOS], ajustar_recurso,
                             tipo_alvo={nome: tipo for nome, tipo, _ in RECURSOS})
        estoque = {nome: quantidade for nome, _, quantidade in RECURSOS}

        print("\nCriando atividades antigas (pode levar um minuto no banco da nuvem)...")
        criadas = criar_atividades(cursor, disciplinas, recursos, estoque)

        banco.commit()
        print(f"\nPronto! {criadas} atividades antigas criadas, com recursos alocados e historico no log.")
    except Exception:
        banco.rollback()
        print("\nDeu erro e NADA foi alterado (desfeito).")
        raise
    finally:
        cursor.close()
        banco.close()


if __name__ == "__main__":
    main()
