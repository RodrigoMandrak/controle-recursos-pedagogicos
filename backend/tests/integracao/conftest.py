"""
Configuracao dos testes de integracao.

Fluxo real exercitado em cada teste:
    requests (HTTP real) -> servidor Flask em porta aleatoria
    -> controller -> model -> PostgreSQL de teste descartavel

O banco de teste e criado com nome unico (pfc_test_<uuid>) no inicio da
execucao e apagado no final (equivalente ao create-drop da aula).
O banco de desenvolvimento nunca e usado pelos testes.

Variaveis lidas do ambiente (ou do arquivo backend/.env):
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD
"""

import os
import threading
import uuid

import pytest
from dotenv import load_dotenv
from psycopg2 import sql
from werkzeug.serving import make_server

load_dotenv()

from app import app  # noqa: E402
from apoio_integracao import (  # noqa: E402
    ESQUEMA_TESTE,
    _conectar_admin,
    cadastrar_e_logar_professor,
    consultar,
    criar_e_logar_coordenador,
    novo_cliente,
)


@pytest.fixture(scope="session", autouse=True)
def banco_de_teste():
    nome_original = os.environ.get("DB_NAME")
    nome_teste = "pfc_test_" + uuid.uuid4().hex[:10]

    admin = _conectar_admin()
    cursor = admin.cursor()
    cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(nome_teste)))
    cursor.close()
    admin.close()

    # a partir daqui o banco.conectar() da aplicacao aponta para o banco de teste
    os.environ["DB_NAME"] = nome_teste
    consultar(ESQUEMA_TESTE)

    yield nome_teste

    if nome_original is None:
        os.environ.pop("DB_NAME", None)
    else:
        os.environ["DB_NAME"] = nome_original

    admin = _conectar_admin()
    cursor = admin.cursor()
    cursor.execute(
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        "WHERE datname = %s AND pid <> pg_backend_pid()",
        (nome_teste,),
    )
    cursor.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(nome_teste)))
    cursor.close()
    admin.close()


@pytest.fixture(scope="session")
def base_url(banco_de_teste):
    """Sobe a aplicacao real em uma porta aleatoria (equivalente ao RANDOM_PORT)."""
    app.config["TESTING"] = True
    app.secret_key = "chave-somente-para-testes-de-integracao"

    servidor = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{servidor.server_port}"

    servidor.shutdown()
    thread.join(timeout=5)


@pytest.fixture
def cliente_anonimo():
    cliente = novo_cliente()
    yield cliente
    cliente.close()

@pytest.fixture
def professor(base_url):
    cliente, usuario = cadastrar_e_logar_professor(base_url)
    yield cliente, usuario
    cliente.close()

@pytest.fixture
def outro_professor(base_url):
    cliente, usuario = cadastrar_e_logar_professor(base_url)
    yield cliente, usuario
    cliente.close()

@pytest.fixture
def coordenador(base_url):
    cliente, usuario = criar_e_logar_coordenador(base_url)
    yield cliente, usuario
    cliente.close()
