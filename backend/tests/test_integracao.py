import os
import uuid

import psycopg2
import pytest
from dotenv import load_dotenv
from psycopg2 import sql

from app import app
from models.atividade_model import salvar_atividade, buscar_atividades


load_dotenv()


@pytest.fixture(scope="module", autouse=True)
def banco_de_teste():
    host = os.getenv("DB_HOST")
    usuario = os.getenv("DB_USER")
    senha = os.getenv("DB_PASSWORD")
    porta = os.getenv("DB_PORT")

    if not host or not usuario or not porta:
        pytest.fail("Dados do PostgreSQL nao foram encontrados")

    nome_original = os.getenv("DB_NAME")
    nome_teste = "pfc_test_" + uuid.uuid4().hex[:8]

    admin = psycopg2.connect(
        host=host,
        database="postgres",
        user=usuario,
        password=senha,
        port=porta
    )
    admin.autocommit = True

    cursor = admin.cursor()
    cursor.execute(
        sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(nome_teste)
        )
    )
    cursor.close()
    admin.close()

    os.environ["DB_NAME"] = nome_teste

    banco = psycopg2.connect(
        host=host,
        database=nome_teste,
        user=usuario,
        password=senha,
        port=porta
    )
    cursor = banco.cursor()

    cursor.execute("""
        CREATE TABLE usuarios (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(120) NOT NULL,
            email VARCHAR(150) NOT NULL,
            senha_hash TEXT NOT NULL,
            perfil VARCHAR(30) NOT NULL,
            identificador_institucional VARCHAR(100),
            aceitou_termos BOOLEAN DEFAULT TRUE,
            data_aceite TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE disciplinas (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(120) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE turmas (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(120) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE professores (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(120) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE atividades (
            id SERIAL PRIMARY KEY,
            disciplina_id INTEGER NOT NULL REFERENCES disciplinas(id),
            turma_id INTEGER NOT NULL REFERENCES turmas(id),
            professor_id INTEGER NOT NULL REFERENCES professores(id),
            descricao TEXT,
            data DATE NOT NULL,
            hora_inicio TIME NOT NULL,
            hora_fim TIME NOT NULL,
            usuario_id INTEGER REFERENCES usuarios(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE logs (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER REFERENCES usuarios(id),
            acao VARCHAR(100) NOT NULL,
            detalhes TEXT,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    banco.commit()
    cursor.close()
    banco.close()

    app.config["TESTING"] = True
    app.secret_key = "chave-teste"

    yield

    if nome_original:
        os.environ["DB_NAME"] = nome_original
    else:
        os.environ.pop("DB_NAME", None)

    admin = psycopg2.connect(
        host=host,
        database="postgres",
        user=usuario,
        password=senha,
        port=porta
    )
    admin.autocommit = True
    cursor = admin.cursor()

    cursor.execute(
        """
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = %s
        AND pid <> pg_backend_pid()
        """,
        (nome_teste,)
    )

    cursor.execute(
        sql.SQL("DROP DATABASE {}").format(
            sql.Identifier(nome_teste)
        )
    )

    cursor.close()
    admin.close()


@pytest.fixture(autouse=True)
def preparar_dados():
    banco = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    )
    cursor = banco.cursor()

    cursor.execute(
        "TRUNCATE logs, atividades, professores, turmas, disciplinas, usuarios RESTART IDENTITY CASCADE"
    )

    cursor.execute("""
        INSERT INTO usuarios
        (nome, email, senha_hash, perfil, aceitou_termos)
        VALUES ('Professor Teste', 'teste@umc.br', 'hash', 'professor', TRUE)
    """)

    cursor.execute(
        "INSERT INTO disciplinas (nome) VALUES ('Engenharia de Software')"
    )
    cursor.execute(
        "INSERT INTO turmas (nome) VALUES ('Turma A')"
    )
    cursor.execute(
        "INSERT INTO professores (nome) VALUES ('Professor Teste')"
    )

    banco.commit()
    cursor.close()
    banco.close()


@pytest.fixture
def cliente():
    with app.test_client() as cliente_teste:
        with cliente_teste.session_transaction() as sessao:
            sessao["usuario_id"] = 1
            sessao["nome"] = "Professor Teste"
            sessao["perfil"] = "professor"

        yield cliente_teste


def test_endpoint_cadastrar_atividade(cliente):
    dados = {
        "disciplina_id": 1,
        "turma_id": 1,
        "professor_id": 1,
        "descricao": "Aula de teste",
        "data": "2026-10-20",
        "hora_inicio": "08:00",
        "hora_fim": "09:00"
    }

    resposta = cliente.post("/atividades", json=dados)

    assert resposta.status_code == 200
    assert resposta.get_json()["mensagem"] == "Atividade cadastrada"


def test_endpoint_horario_invalido(cliente):
    dados = {
        "disciplina_id": 1,
        "turma_id": 1,
        "professor_id": 1,
        "descricao": "Horario errado",
        "data": "2026-10-20",
        "hora_inicio": "10:00",
        "hora_fim": "09:00"
    }

    resposta = cliente.post("/atividades", json=dados)

    assert resposta.status_code == 400
    assert resposta.get_json()["erro"] == "Horario final invalido"


def test_persistencia_salvar_e_buscar_atividade():
    salvar_atividade(
        1,
        1,
        1,
        "Atividade gravada no banco",
        "2026-10-21",
        "09:00",
        "10:00",
        1
    )

    atividades = buscar_atividades(1, "professor")

    assert len(atividades) == 1
    assert atividades[0]["descricao"] == "Atividade gravada no banco"


def test_fluxo_criar_e_listar_atividade(cliente):
    dados = {
        "disciplina_id": 1,
        "turma_id": 1,
        "professor_id": 1,
        "descricao": "Fluxo completo",
        "data": "2026-10-22",
        "hora_inicio": "14:00",
        "hora_fim": "15:00"
    }

    resposta_cadastro = cliente.post("/atividades", json=dados)
    resposta_lista = cliente.get("/atividades")

    lista = resposta_lista.get_json()

    assert resposta_cadastro.status_code == 200
    assert resposta_lista.status_code == 200
    assert len(lista) == 1
    assert lista[0]["descricao"] == "Fluxo completo"
