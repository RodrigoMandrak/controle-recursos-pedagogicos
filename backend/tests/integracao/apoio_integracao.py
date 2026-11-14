"""
Helpers dos testes de integracao (equivalentes ao buildBookRequest/criarLivro da aula).
"""

import os
from datetime import date, timedelta
import uuid

import psycopg2
import requests

from models.usuario_model import cadastrar_usuario


ESQUEMA_TESTE = """
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    perfil VARCHAR(30) NOT NULL,
    identificador_institucional VARCHAR(100),
    aceitou_termos BOOLEAN DEFAULT FALSE,
    data_aceite TIMESTAMP
);

CREATE TABLE disciplinas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL
);

CREATE TABLE turmas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL
);

CREATE TABLE professores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL
);

CREATE TABLE recursos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    tipo VARCHAR(60) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'disponivel'
);

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
);

CREATE TABLE alocacoes (
    id SERIAL PRIMARY KEY,
    atividade_id INTEGER NOT NULL REFERENCES atividades(id) ON DELETE CASCADE,
    recurso_id INTEGER NOT NULL REFERENCES recursos(id)
);

CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    acao VARCHAR(100) NOT NULL,
    detalhes TEXT,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE recuperacao_senha (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expira_em TIMESTAMP NOT NULL,
    utilizado BOOLEAN DEFAULT FALSE
);
"""


def _conectar_admin():
    banco = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database="postgres",
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        port=os.getenv("DB_PORT", "5432"),
    )
    banco.autocommit = True
    return banco


def consultar(comando, parametros=()):
    """Consulta direta no banco de teste, usada so para conferir persistencia."""
    nome_banco = os.environ["DB_NAME"]
    assert nome_banco.startswith("pfc_test_"), "Testes nunca devem usar o banco de desenvolvimento"

    banco = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=nome_banco,
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        port=os.getenv("DB_PORT", "5432"),
    )
    cursor = banco.cursor()
    cursor.execute(comando, parametros)

    resultado = cursor.fetchall() if cursor.description else None

    banco.commit()
    cursor.close()
    banco.close()

    return resultado




def unico():
    return uuid.uuid4().hex[:12]


def novo_cliente():
    """Cliente HTTP que nao lanca excecao em 4xx/5xx (os testes conferem o status)."""
    cliente = requests.Session()
    cliente.trust_env = False  # ignora proxy da maquina: chamada sempre local
    return cliente


def cadastrar_e_logar_professor(base_url):
    """Cadastra um professor pelo endpoint real e faz login. Retorna (cliente, usuario)."""
    sufixo = unico()
    email = f"prof.{sufixo}@teste.umc.br"
    senha = "SenhaForte123"

    cliente = novo_cliente()

    cadastro = cliente.post(f"{base_url}/usuarios/cadastro", json={
        "nome": f"Professor {sufixo}",
        "email": email,
        "senha": senha,
        "confirmar_senha": senha,
        "identificador_institucional": f"RA-{sufixo}",
        "aceitou_termos": True,
    })
    assert cadastro.status_code == 200, cadastro.text

    # o cadastro fica pendente ate a coordenacao aprovar; aqui o teste ja libera a conta
    consultar("UPDATE usuarios SET status = 'ativo' WHERE email = %s", (email,))

    login = cliente.post(f"{base_url}/login", json={"email": email, "senha": senha})
    assert login.status_code == 200, login.text

    return cliente, login.json()["usuario"]


def criar_e_logar_coordenador(base_url):
    """
    Nao existe endpoint de cadastro de coordenador: ele e criado pela mesma funcao
    usada no script criar_coordenador.py. O login e feito pelo endpoint real.
    """
    sufixo = unico()
    email = f"coord.{sufixo}@teste.umc.br"
    senha = "SenhaForte123"

    cadastrar_usuario(f"Coordenador {sufixo}", email, senha, "coordenador")

    cliente = novo_cliente()
    login = cliente.post(f"{base_url}/login", json={"email": email, "senha": senha})
    assert login.status_code == 200, login.text

    return cliente, login.json()["usuario"]


def criar_cadastros_base():
    """
    Disciplina, turma, professor e dois recursos com nomes unicos.
    Sao inseridas direto no banco de teste para cada teste comecar
    com dados conhecidos (a tela de Dados academicos tem seus proprios testes).
    """
    sufixo = unico()

    def inserir(comando, parametros):
        return consultar(comando + " RETURNING id", parametros)[0][0]

    return {
        "sufixo": sufixo,
        "disciplina_id": inserir("INSERT INTO disciplinas (nome) VALUES (%s)", (f"Disciplina {sufixo}",)),
        "disciplina_nome": f"Disciplina {sufixo}",
        "turma_id": inserir("INSERT INTO turmas (nome) VALUES (%s)", (f"Turma {sufixo}",)),
        "turma_nome": f"Turma {sufixo}",
        "professor_id": inserir("INSERT INTO professores (nome) VALUES (%s)", (f"Prof Cadastro {sufixo}",)),
        "professor_nome": f"Prof Cadastro {sufixo}",
        "recurso_id": inserir(
            "INSERT INTO recursos (nome, tipo, status) VALUES (%s, %s, %s)",
            (f"Projetor {sufixo}", "projetor", "disponivel"),
        ),
        "recurso_nome": f"Projetor {sufixo}",
        "recurso2_id": inserir(
            "INSERT INTO recursos (nome, tipo, status) VALUES (%s, %s, %s)",
            (f"Lab Informatica {sufixo}", "laboratorio", "disponivel"),
        ),
        "recurso2_nome": f"Lab Informatica {sufixo}",
    }


def dia_futuro(deslocamento=0):
    # data sempre no futuro (o sistema nao aceita atividade em data passada)
    return (date.today() + timedelta(days=60 + deslocamento)).isoformat()


def build_atividade_request(base, descricao, data=None, inicio="08:00", fim="10:00"):
    return {
        "disciplina_id": base["disciplina_id"],
        "turma_id": base["turma_id"],
        "professor_id": base["professor_id"],
        "descricao": descricao,
        "data": data or dia_futuro(0),
        "hora_inicio": inicio,
        "hora_fim": fim,
    }


def criar_atividade(cliente, base_url, base, descricao, **horario):
    """Cria a atividade pelo endpoint real e devolve o id (buscado via GET /atividades)."""
    resposta = cliente.post(f"{base_url}/atividades", json=build_atividade_request(base, descricao, **horario))
    assert resposta.status_code == 200, resposta.text

    lista = cliente.get(f"{base_url}/atividades").json()
    return next(item["id"] for item in lista if item["descricao"] == descricao)


def criar_alocacao(cliente, base_url, atividade_id, recurso_id, recurso_nome):
    """Aloca o recurso pelo endpoint real e devolve o id (buscado via GET /alocacoes)."""
    resposta = cliente.post(f"{base_url}/alocacoes", json={
        "atividade_id": atividade_id,
        "recurso_id": recurso_id,
    })
    assert resposta.status_code == 200, resposta.text

    lista = cliente.get(f"{base_url}/alocacoes").json()
    return next(item["id"] for item in lista if item["recurso"] == recurso_nome)
