"""
Prepara tudo o que o sistema precisa no banco, para rodar em um PC novo.

- cria o arquivo .env (se ainda nao existir), perguntando a senha do PostgreSQL
- cria o banco de dados (se ainda nao existir)
- cria as tabelas (se ainda nao existirem)
- coloca dados de demonstracao (so se o banco estiver vazio)
- cria uma conta de coordenador e uma de professor (so se nao existirem)
  e salva os e-mails e senhas em ACESSOS_DEMONSTRACAO.txt

Pode rodar quantas vezes quiser: ele nunca apaga nem duplica nada.
Uso (dentro da pasta backend, com o venv):  python preparar_banco.py
Para apagar e refazer so os dados de demonstracao (atividades, alocacoes e logs):
    python preparar_banco.py --recriar-demo
"""

import os
import secrets
import sys
from datetime import date, datetime, time, timedelta
from getpass import getpass

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_ENV = os.path.join(PASTA, ".env")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    perfil VARCHAR(20) NOT NULL DEFAULT 'professor',
    identificador_institucional VARCHAR(50),
    aceitou_termos BOOLEAN DEFAULT FALSE,
    data_aceite TIMESTAMP
);
CREATE TABLE IF NOT EXISTS disciplinas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL
);
CREATE TABLE IF NOT EXISTS turmas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL
);
CREATE TABLE IF NOT EXISTS professores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL
);
CREATE TABLE IF NOT EXISTS recursos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    status VARCHAR(30) DEFAULT 'disponivel',
    quantidade INTEGER NOT NULL DEFAULT 1
);
ALTER TABLE recursos ADD COLUMN IF NOT EXISTS quantidade INTEGER NOT NULL DEFAULT 1;
ALTER TABLE recursos ADD COLUMN IF NOT EXISTS ativo BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'ativo';
ALTER TABLE professores ADD COLUMN IF NOT EXISTS usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL;
CREATE TABLE IF NOT EXISTS atividades (
    id SERIAL PRIMARY KEY,
    disciplina_id INTEGER REFERENCES disciplinas(id),
    turma_id INTEGER REFERENCES turmas(id),
    professor_id INTEGER REFERENCES professores(id),
    descricao TEXT,
    data DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fim TIME NOT NULL,
    usuario_id INTEGER REFERENCES usuarios(id)
);
CREATE TABLE IF NOT EXISTS alocacoes (
    id SERIAL PRIMARY KEY,
    atividade_id INTEGER REFERENCES atividades(id) ON DELETE CASCADE,
    recurso_id INTEGER REFERENCES recursos(id)
);
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    acao VARCHAR(100),
    detalhes TEXT,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS recuperacao_senha (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expira_em TIMESTAMP NOT NULL,
    utilizado BOOLEAN DEFAULT FALSE
);
"""

DISCIPLINAS = ["Banco de Dados", "Engenharia de Software", "Inteligência Artificial", "Programação Web"]
TURMAS = ["7A", "7B", "8A", "8B"]
PROFESSORES = ["Carlos Silva", "Marcos Oliveira", "Ana Ribeiro"]
RECURSOS = [("Laboratorio 01", "laboratorio"), ("Laboratorio 02", "laboratorio"), ("Sala 12", "sala"),
            ("Sala de Cinema", "sala"), ("Projetor 01", "equipamento"), ("Notebook 01", "equipamento")]


def passo(texto):
    print("\n==== " + texto + " ====")


def criar_env():
    # no servidor (Render) os dados do banco vem das variaveis de ambiente, sem .env
    if os.getenv("DB_HOST") and not os.path.exists(ARQUIVO_ENV):
        print("Usando os dados do banco das variaveis de ambiente (servidor).")
        return
    if os.path.exists(ARQUIVO_ENV):
        print("Arquivo .env ja existe, mantendo o que esta nele.")
        return
    print("Ainda nao existe o arquivo .env neste PC. Vou criar agora.")
    print("(Aperte Enter para aceitar o valor entre colchetes.)")
    usuario = input("Usuario do PostgreSQL [postgres]: ").strip() or "postgres"
    senha = getpass("Senha do PostgreSQL (a mesma do pgAdmin; nao aparece enquanto digita): ")
    nome = input("Nome do banco [recursos_pedagogicos]: ").strip() or "recursos_pedagogicos"
    porta = input("Porta [5432]: ").strip() or "5432"
    with open(ARQUIVO_ENV, "w", encoding="utf-8") as arquivo:
        arquivo.write(f"DB_HOST=localhost\nDB_PORT={porta}\nDB_USER={usuario}\nDB_PASSWORD={senha}\n"
                      f"DB_NAME={nome}\nSECRET_KEY={secrets.token_hex(24)}\n")
    print("Arquivo .env criado.")


def conectar_em(banco_nome):
    import psycopg2
    return psycopg2.connect(host=os.getenv("DB_HOST", "localhost"), port=os.getenv("DB_PORT", "5432"),
                            user=os.getenv("DB_USER", "postgres"), password=os.getenv("DB_PASSWORD"),
                            database=banco_nome, sslmode=os.getenv("DB_SSLMODE", "prefer"))


def criar_banco():
    nome = os.getenv("DB_NAME")
    # se ja da para entrar no banco, ele existe (ex.: banco na nuvem, como o Neon)
    try:
        conectar_em(nome).close()
        print(f"Banco '{nome}' ja existe.")
        return
    except Exception:
        pass
    try:
        admin = conectar_em("postgres")
    except Exception as erro:
        print("\n[ERRO] Nao consegui conectar no PostgreSQL.")
        print("Confira se o PostgreSQL esta ligado (o pgAdmin abre o servidor?) e se a senha do .env esta certa.")
        print("Para trocar a senha, apague o arquivo backend\\.env e rode de novo.")
        print("Detalhe:", erro)
        sys.exit(1)
    admin.autocommit = True
    cursor = admin.cursor()
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (nome,))
    if cursor.fetchone():
        print(f"Banco '{nome}' ja existe.")
    else:
        cursor.execute(f'CREATE DATABASE "{nome}" ENCODING \'UTF8\'')
        print(f"Banco '{nome}' criado.")
    cursor.close()
    admin.close()


def contar(cursor, tabela):
    cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
    return cursor.fetchone()[0]


ARQUIVO_ACESSOS = os.path.join(os.path.dirname(PASTA), "ACESSOS_DEMONSTRACAO.txt")
CONTAS = [
    ("Luciano Coordenador", "luciano@escola.com.br", "coordenador"),
    ("Carlos Lima", "carlos.lima@escola.com.br", "professor"),
]


def gerar_senha():
    # facil de digitar: Pfc- + 4 numeros (8 caracteres, o minimo do sistema)
    return "Pfc-" + "".join(secrets.choice("23456789") for _ in range(4))


def criar_usuarios(cursor, banco):
    from models.usuario_model import cadastrar_usuario
    criadas = []
    for nome, email, perfil in CONTAS:
        cursor.execute("SELECT 1 FROM usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            print(f"Conta {perfil} ja existe ({email}), mantendo a senha que ja tinha.")
            continue
        # no servidor, a senha pode vir da variavel SENHA_COORDENADOR / SENHA_PROFESSOR
        senha = os.getenv(f"SENHA_{perfil.upper()}") or gerar_senha()
        cadastrar_usuario(nome, email, senha, perfil, None, True)
        criadas.append((perfil, email, senha))
        print(f"Conta {perfil} criada: {email}")
    banco.commit()

    if criadas:
        with open(ARQUIVO_ACESSOS, "w", encoding="utf-8") as arquivo:
            arquivo.write("ACESSOS DA DEMONSTRACAO - Sistema de Controle de Recursos Pedagogicos\n")
            arquivo.write(f"Gerado em {date.today().strftime('%d/%m/%Y')}\n\n")
            for perfil, email, senha in criadas:
                arquivo.write(f"{perfil.upper()}\n  E-mail: {email}\n  Senha:  {senha}\n\n")
            arquivo.write("Coordenador = janela normal do Chrome.\n")
            arquivo.write("Professor = janela anonima (Ctrl + Shift + N).\n")
            arquivo.write("\nApague este arquivo depois da apresentacao.\n")
        print("E-mails e senhas salvos em ACESSOS_DEMONSTRACAO.txt (vai abrir no Bloco de Notas).")
    elif not os.path.exists(ARQUIVO_ACESSOS):
        print("As contas ja existiam antes deste script; use as senhas que voce ja tinha.")


def proximo_dia_util(dia):
    dia += timedelta(days=1)
    while dia.weekday() >= 5:
        dia += timedelta(days=1)
    return dia


def dados_demonstracao(cursor, banco):
    if contar(cursor, "disciplinas") == 0:
        for nome in DISCIPLINAS:
            cursor.execute("INSERT INTO disciplinas (nome) VALUES (%s)", (nome,))
        for nome in TURMAS:
            cursor.execute("INSERT INTO turmas (nome) VALUES (%s)", (nome,))
        for nome in PROFESSORES:
            cursor.execute("INSERT INTO professores (nome) VALUES (%s)", (nome,))
        for nome, tipo in RECURSOS:
            cursor.execute("INSERT INTO recursos (nome, tipo) VALUES (%s, %s)", (nome, tipo))
        banco.commit()
        print("Disciplinas, turmas, professores e recursos cadastrados.")
    else:
        print("Disciplinas, turmas e recursos ja existem, mantendo.")

    if contar(cursor, "atividades") > 0:
        print("Ja existem atividades, nao vou mexer nelas.")
        return None

    def ids(tabela):
        cursor.execute(f"SELECT id FROM {tabela} ORDER BY id")
        return [linha[0] for linha in cursor.fetchall()]

    disc, turm, prof = ids("disciplinas"), ids("turmas"), ids("professores")
    # so recursos ativos (os excluidos/arquivados ficam de fora)
    cursor.execute("SELECT id FROM recursos WHERE ativo = TRUE ORDER BY id")
    rec = [linha[0] for linha in cursor.fetchall()]
    cursor.execute("SELECT id FROM usuarios WHERE perfil = 'coordenador' ORDER BY id LIMIT 1")
    coord = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM usuarios WHERE perfil = 'professor' ORDER BY id LIMIT 1")
    professor = cursor.fetchone()[0]

    hoje = date.today()
    horarios = [("08:00", "10:00"), ("10:00", "12:00"), ("13:30", "15:30"), ("19:00", "21:00")]
    descricoes = ["Aula prática no laboratório", "Revisão para a prova", "Apresentação de projetos",
                  "Exercícios em grupo", "Aula com vídeo", "Seminário da turma"]
    # so datas que ja passaram: 4 meses antes e o mes atual ate ontem (nada para frente)
    por_mes = [8, 11, 15, 12, 10]
    atividades = []
    for indice, quantidade in enumerate(por_mes):
        mes = hoje.month - 4 + indice
        ano = hoje.year + (mes - 1) // 12
        mes = (mes - 1) % 12 + 1
        for n in range(quantidade):
            dia = date(ano, mes, 1 + (n * 2) % 27)
            while dia.weekday() >= 5:
                dia += timedelta(days=1)
            if dia >= hoje:
                continue
            atividades.append((dia, horarios[n % 4], disc[n % len(disc)], turm[(n + indice) % len(turm)],
                               prof[(n + indice) % len(prof)], descricoes[(n + indice) % len(descricoes)],
                               professor if n % 2 == 0 else coord, rec[(n * 2 + indice) % len(rec)] if n % 4 != 3 else None))
    uso = {}
    logs = []
    nomes_recurso = {r: nome for r, (nome, _) in zip(rec, RECURSOS)}
    for numero, (dia, (inicio, fim), d, t, p, descricao, dono, recurso) in enumerate(atividades):
        novo_id = inserir_atividade(cursor, d, t, p, descricao, dia, inicio, fim, dono)
        # historico de auditoria, como se tivesse sido feito pelo sistema alguns dias antes da aula
        quando = datetime.combine(dia - timedelta(days=3), time(8 + numero % 10, (numero * 7) % 60))
        logs.append((dono, "LOGIN", "Usuario realizou login no sistema", quando))
        logs.append((dono, "CADASTRO_ATIVIDADE", f"Disciplina {d}, turma {t}, professor {p}", quando + timedelta(minutes=2)))
        if recurso and (dia, inicio, recurso) not in uso:
            uso[(dia, inicio, recurso)] = True
            cursor.execute("INSERT INTO alocacoes (atividade_id, recurso_id) VALUES (%s, %s) RETURNING id",
                           (novo_id, recurso))
            id_alocacao = cursor.fetchone()[0]
            logs.append((dono, "ALOCACAO_RECURSO", f"Recurso {recurso} alocado na atividade {novo_id}",
                         quando + timedelta(minutes=4)))
            if numero % 5 == 2:
                logs.append((dono, "ALTERACAO_ALOCACAO",
                             f"Alocacao {id_alocacao} alterada do recurso {rec[-1]} para {recurso}",
                             quando + timedelta(minutes=6)))
        elif numero % 4 == 3 and len(rec) > 2:
            logs.append((dono, "ALOCACAO_RECURSO", f"Recurso {rec[2]} alocado na atividade {novo_id}",
                         quando + timedelta(minutes=4)))
            logs.append((dono, "CANCELAMENTO_ALOCACAO",
                         f"Alocacao da atividade {novo_id} e recurso {rec[2]} foi cancelada",
                         quando + timedelta(minutes=9)))
        if numero % 6 == 1:
            logs.append((dono, "CONSULTA_FERIADO", f"Data {dia.isoformat()} nao e feriado (origem: api)",
                         quando + timedelta(minutes=1)))
        logs.append((dono, "LOGOUT", "Usuario saiu do sistema", quando + timedelta(minutes=12)))
    for dono, acao, detalhes, quando in logs:
        cursor.execute("INSERT INTO logs (usuario_id, acao, detalhes, data_hora) VALUES (%s, %s, %s, %s)",
                       (dono, acao, detalhes, quando))
    banco.commit()
    print(f"{len(atividades)} atividades de demonstracao (todas em datas que ja passaram) e "
          f"{len(logs)} registros de log cadastrados.")


def inserir_atividade(cursor, d, t, p, descricao, dia, inicio, fim, dono):
    cursor.execute("""INSERT INTO atividades (disciplina_id, turma_id, professor_id, descricao, data,
                      hora_inicio, hora_fim, usuario_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                   (d, t, p, descricao, dia, inicio, fim, dono))
    return cursor.fetchone()[0]


def preparar_dia(cursor, banco):
    """Roda toda vez: deixa atividades de hoje e o conflito do proximo dia util prontos.
    So mexe no banco de demonstracao (o que tem as contas criadas por este script)."""
    cursor.execute("SELECT id FROM usuarios WHERE email = %s", (CONTAS[0][1],))
    coord = cursor.fetchone()
    cursor.execute("SELECT id FROM usuarios WHERE email = %s", (CONTAS[1][1],))
    professor = cursor.fetchone()
    if not coord or not professor:
        print("Banco com dados proprios: nao vou criar atividades de demonstracao do dia.")
        return None
    coord, professor = coord[0], professor[0]

    def primeiro(tabela, nome=None):
        if nome:
            cursor.execute(f"SELECT id FROM {tabela} WHERE nome = %s ORDER BY id LIMIT 1", (nome,))
        else:
            cursor.execute(f"SELECT id FROM {tabela} ORDER BY id LIMIT 1")
        linha = cursor.fetchone()
        return linha[0] if linha else None

    disc, turma, prof = primeiro("disciplinas"), primeiro("turmas"), primeiro("professores")
    turma_b = primeiro("turmas", "8B") or turma
    prof_b = primeiro("professores", "Marcos Oliveira") or prof
    laboratorio = primeiro("recursos", "Laboratorio 01") or primeiro("recursos")
    projetor = primeiro("recursos", "Projetor 01")
    hoje = date.today()

    # atividades de hoje, para o card "Atividades hoje".
    # So entram as que JA TERMINARAM (nada para frente).
    cursor.execute("SELECT COUNT(*) FROM atividades WHERE data = %s", (hoje,))
    if cursor.fetchone()[0] == 0:
        agora = datetime.now().strftime("%H:%M")
        criadas = 0
        if agora >= "10:00":
            novo = inserir_atividade(cursor, disc, turma, prof, "Aula prática no laboratório", hoje, "08:00", "10:00", professor)
            if projetor:
                cursor.execute("INSERT INTO alocacoes (atividade_id, recurso_id) VALUES (%s, %s)", (novo, projetor))
            criadas += 1
        if agora >= "15:30":
            inserir_atividade(cursor, disc, turma_b, prof_b, "Revisão para a prova", hoje, "13:30", "15:30", coord)
            criadas += 1
        if criadas:
            print(f"{criadas} atividade(s) de hoje cadastrada(s) (horarios que ja passaram).")

    banco.commit()

    # o conflito sera criado ao vivo na apresentacao: so aponta um dia util sem nenhuma atividade,
    # para a primeira reserva nao esbarrar em dados de demonstracao
    dia_livre = proximo_dia_util(hoje)
    while True:
        cursor.execute("SELECT COUNT(*) FROM atividades WHERE data = %s", (dia_livre,))
        if cursor.fetchone()[0] == 0:
            return dia_livre
        dia_livre = proximo_dia_util(dia_livre)


def recriar_demo(cursor, banco):
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE email IN (%s, %s)", (CONTAS[0][1], CONTAS[1][1]))
    if cursor.fetchone()[0] < 2:
        print("Este banco nao e o de demonstracao (nao tem as contas criadas por este script). Nao vou apagar nada.")
        return
    resposta = input("Isso APAGA todas as atividades, alocacoes e logs deste banco e cria tudo de novo. "
                     "Digite SIM para continuar: ").strip().upper()
    if resposta != "SIM":
        print("Cancelado, nada foi apagado.")
        return
    cursor.execute("DELETE FROM alocacoes")
    cursor.execute("DELETE FROM atividades")
    cursor.execute("DELETE FROM logs")
    banco.commit()
    print("Atividades, alocacoes e logs apagados. Criando de novo...")


def main():
    os.chdir(PASTA)
    sys.path.insert(0, PASTA)
    passo("1. Arquivo .env")
    criar_env()
    from dotenv import load_dotenv
    if os.path.exists(ARQUIVO_ENV):
        load_dotenv(ARQUIVO_ENV, override=True)

    passo("2. Banco de dados")
    criar_banco()

    passo("3. Tabelas")
    banco = conectar_em(os.getenv("DB_NAME"))
    cursor = banco.cursor()
    cursor.execute(ESQUEMA)
    banco.commit()
    print("Tabelas prontas.")

    passo("4. Contas de acesso")
    criar_usuarios(cursor, banco)

    passo("5. Dados de demonstracao")
    if "--recriar-demo" in sys.argv:
        recriar_demo(cursor, banco)
    dados_demonstracao(cursor, banco)
    dia_livre = preparar_dia(cursor, banco)

    cursor.close()
    banco.close()
    print("\nBanco pronto!")
    if dia_livre:
        print(f"Dia livre para criar o conflito ao vivo: {dia_livre.strftime('%d/%m/%Y')} "
              f"(nenhuma reserva nesse dia).")


if __name__ == "__main__":
    main()
