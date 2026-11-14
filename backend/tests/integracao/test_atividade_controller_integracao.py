"""
Testes de integracao do atividade_controller (/atividades, /disciplinas, /turmas, /professores).

Fluxo real exercitado em cada teste:
    requests -> HTTP real (porta aleatoria) -> atividade_controller
    -> atividade_model -> PostgreSQL de teste
"""

from apoio_integracao import (
    dia_futuro,
    build_atividade_request,
    consultar,
    criar_atividade,
    criar_cadastros_base,
    unico,
)


# ---------- POST /atividades ----------

def test_cadastrar_comDadosValidos_deveRetornar200EGravarNoBanco(base_url, professor):
    # Arrange
    cliente, usuario = professor
    base = criar_cadastros_base()
    descricao = f"Aula pratica {unico()}"
    request = build_atividade_request(base, descricao, data=dia_futuro(2), inicio="08:00", fim="09:40")

    # Act
    resposta = cliente.post(f"{base_url}/atividades", json=request)

    # Assert
    assert resposta.status_code == 200
    assert resposta.json() == {"mensagem": "Atividade cadastrada"}

    linhas = consultar(
        "SELECT disciplina_id, turma_id, professor_id, data::text, "
        "hora_inicio::text, hora_fim::text, usuario_id "
        "FROM atividades WHERE descricao = %s",
        (descricao,),
    )
    assert linhas == [(
        base["disciplina_id"], base["turma_id"], base["professor_id"],
        dia_futuro(2), "08:00:00", "09:40:00", usuario["id"],
    )]


def test_cadastrar_comDadosValidos_deveRegistrarLogDaAcao(base_url, professor):
    cliente, usuario = professor
    base = criar_cadastros_base()

    resposta = cliente.post(f"{base_url}/atividades", json=build_atividade_request(base, f"Log {unico()}"))

    assert resposta.status_code == 200
    logs = consultar(
        "SELECT acao, detalhes FROM logs WHERE usuario_id = %s AND acao = 'CADASTRO_ATIVIDADE'",
        (usuario["id"],),
    )
    assert len(logs) == 1
    # o log mostra os nomes (nao os numeros), para a auditoria ser legivel
    assert base["disciplina_nome"] in logs[0][1]
    assert base["turma_nome"] in logs[0][1]
    assert base["professor_nome"] in logs[0][1]


def test_cadastrar_semDisciplina_deveRetornar400ComMensagemENaoGravar(base_url, professor):
    cliente, _ = professor
    base = criar_cadastros_base()
    descricao = f"Sem disciplina {unico()}"
    request = build_atividade_request(base, descricao)
    request["disciplina_id"] = None

    resposta = cliente.post(f"{base_url}/atividades", json=request)

    assert resposta.status_code == 400
    assert resposta.json()["erro"] == "Preencha todos os dados"
    assert consultar("SELECT id FROM atividades WHERE descricao = %s", (descricao,)) == []


def test_cadastrar_semData_deveRetornar400ComMensagem(base_url, professor):
    cliente, _ = professor
    base = criar_cadastros_base()
    request = build_atividade_request(base, f"Sem data {unico()}")
    request["data"] = ""

    resposta = cliente.post(f"{base_url}/atividades", json=request)

    assert resposta.status_code == 400
    assert resposta.json()["erro"] == "Preencha a data e o horario"


def test_cadastrar_comHoraFimAntesDoInicio_deveRetornar400ComMensagem(base_url, professor):
    cliente, _ = professor
    base = criar_cadastros_base()
    descricao = f"Horario invertido {unico()}"

    resposta = cliente.post(
        f"{base_url}/atividades",
        json=build_atividade_request(base, descricao, inicio="10:00", fim="09:00"),
    )

    assert resposta.status_code == 400
    assert resposta.json()["erro"] == "Horario final invalido"
    assert consultar("SELECT id FROM atividades WHERE descricao = %s", (descricao,)) == []


def test_cadastrar_semLogin_deveRetornar401ComMensagem(base_url, cliente_anonimo):
    base = criar_cadastros_base()
    descricao = f"Anonima {unico()}"

    resposta = cliente_anonimo.post(f"{base_url}/atividades", json=build_atividade_request(base, descricao))

    assert resposta.status_code == 401
    assert resposta.json()["erro"] == "Voce precisa estar logado"
    assert consultar("SELECT id FROM atividades WHERE descricao = %s", (descricao,)) == []


def test_cadastrar_comOrigemDoFrontend_deveRetornarHeadersCorsComCredenciais(base_url, professor):
    cliente, _ = professor
    base = criar_cadastros_base()
    origem = "http://localhost:8080"

    resposta = cliente.post(
        f"{base_url}/atividades",
        json=build_atividade_request(base, f"CORS {unico()}"),
        headers={"Origin": origem},
    )

    assert resposta.status_code == 200
    assert resposta.headers["Content-Type"] == "application/json"
    assert resposta.headers["Access-Control-Allow-Origin"] == origem
    assert resposta.headers["Access-Control-Allow-Credentials"] == "true"


# ---------- GET /atividades ----------

def test_listar_aposCadastrar_deveRetornar200ComNomesDaDisciplinaTurmaEProfessor(base_url, professor):
    cliente, _ = professor
    base = criar_cadastros_base()
    descricao = f"Listagem {unico()}"
    id_atividade = criar_atividade(cliente, base_url, base, descricao, data=dia_futuro(3), inicio="13:00", fim="14:30")

    resposta = cliente.get(f"{base_url}/atividades")

    assert resposta.status_code == 200
    item = next(a for a in resposta.json() if a["id"] == id_atividade)
    assert item == {
        "id": id_atividade,
        "disciplina": base["disciplina_nome"],
        "turma": base["turma_nome"],
        "professor": base["professor_nome"],
        "descricao": descricao,
        "data": dia_futuro(3),
        "hora_inicio": "13:00:00",
        "hora_fim": "14:30:00",
        # ids e situacao usados pela tela para alterar/cancelar
        "disciplina_id": base["disciplina_id"],
        "turma_id": base["turma_id"],
        "professor_id": base["professor_id"],
        "ja_aconteceu": False,
    }


def test_listar_comoProfessor_deveRetornarSomenteAtividadesDoProprioUsuario(base_url, professor, outro_professor):
    cliente_a, _ = professor
    cliente_b, _ = outro_professor
    base = criar_cadastros_base()
    id_a = criar_atividade(cliente_a, base_url, base, f"Do professor A {unico()}", data=dia_futuro(6))
    id_b = criar_atividade(cliente_b, base_url, base, f"Do professor B {unico()}", data=dia_futuro(7))

    resposta = cliente_a.get(f"{base_url}/atividades")

    assert resposta.status_code == 200
    ids = [a["id"] for a in resposta.json()]
    assert id_a in ids
    assert id_b not in ids


def test_listar_comoCoordenador_deveRetornar200ComAtividadesDeTodosOsProfessores(
    base_url, professor, outro_professor, coordenador
):
    cliente_a, _ = professor
    cliente_b, _ = outro_professor
    cliente_coord, _ = coordenador
    base = criar_cadastros_base()
    id_a = criar_atividade(cliente_a, base_url, base, f"Coord ve A {unico()}", data=dia_futuro(8))
    id_b = criar_atividade(cliente_b, base_url, base, f"Coord ve B {unico()}", data=dia_futuro(9))

    resposta = cliente_coord.get(f"{base_url}/atividades")

    assert resposta.status_code == 200
    ids = [a["id"] for a in resposta.json()]
    assert {id_a, id_b}.issubset(ids)


def test_listar_semLogin_deveRetornar401ComMensagem(base_url, cliente_anonimo):
    resposta = cliente_anonimo.get(f"{base_url}/atividades")

    assert resposta.status_code == 401
    assert resposta.json()["erro"] == "Voce precisa estar logado"


# ---------- GET /disciplinas, /turmas, /professores ----------

def test_listarDisciplinas_comDisciplinaCadastrada_deveRetornar200ComIdENome(base_url, cliente_anonimo):
    base = criar_cadastros_base()

    resposta = cliente_anonimo.get(f"{base_url}/disciplinas")

    assert resposta.status_code == 200
    assert {"id": base["disciplina_id"], "nome": base["disciplina_nome"]} in resposta.json()


def test_listarTurmas_comTurmaCadastrada_deveRetornar200ComIdENome(base_url, cliente_anonimo):
    base = criar_cadastros_base()

    resposta = cliente_anonimo.get(f"{base_url}/turmas")

    assert resposta.status_code == 200
    assert {"id": base["turma_id"], "nome": base["turma_nome"]} in resposta.json()


def test_listarProfessores_comProfessorCadastrado_deveRetornar200ComIdENome(base_url, cliente_anonimo):
    base = criar_cadastros_base()

    resposta = cliente_anonimo.get(f"{base_url}/professores")

    assert resposta.status_code == 200
    assert {"id": base["professor_id"], "nome": base["professor_nome"]} in resposta.json()
