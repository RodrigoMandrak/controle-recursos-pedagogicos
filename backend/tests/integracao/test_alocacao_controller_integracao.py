"""
Testes de integracao do alocacao_controller (/recursos e /alocacoes).

Fluxo real exercitado em cada teste:
    requests -> HTTP real (porta aleatoria) -> alocacao_controller
    -> alocacao_model (validacao de conflitos) -> PostgreSQL de teste
"""

from apoio_integracao import (
    dia_futuro,
    build_atividade_request,
    consultar,
    criar_alocacao,
    criar_atividade,
    criar_cadastros_base,
    unico,
)


def _preparar_alocacao(cliente, base_url):
    """Cria cadastros base, uma atividade e uma alocacao pela API. Devolve (base, id_atividade, id_alocacao)."""
    base = criar_cadastros_base()
    id_atividade = criar_atividade(cliente, base_url, base, f"Atividade {unico()}")
    id_alocacao = criar_alocacao(cliente, base_url, id_atividade, base["recurso_id"], base["recurso_nome"])
    return base, id_atividade, id_alocacao


# ---------- GET /recursos ----------

def test_listarRecursos_logado_deveRetornar200ComTodosOsCamposDoRecurso(base_url, professor):
    cliente, _ = professor
    base = criar_cadastros_base()

    resposta = cliente.get(f"{base_url}/recursos")

    assert resposta.status_code == 200
    # a lista tambem traz estoque e uso (quantidade, em_uso_agora, reservas_futuras)
    recurso = next(item for item in resposta.json() if item["id"] == base["recurso_id"])
    assert recurso["nome"] == base["recurso_nome"]
    assert recurso["tipo"] == "projetor"
    assert recurso["status"] == "disponivel"
    assert recurso["quantidade"] == 1


def test_listarRecursos_semLogin_deveRetornar401ComMensagem(base_url, cliente_anonimo):
    resposta = cliente_anonimo.get(f"{base_url}/recursos")

    assert resposta.status_code == 401
    assert resposta.json()["erro"] == "Voce precisa estar logado"


# ---------- POST /alocacoes ----------

def test_alocar_comDadosValidos_deveRetornar200EGravarAlocacaoNoBanco(base_url, professor):
    cliente, usuario = professor
    base = criar_cadastros_base()
    id_atividade = criar_atividade(cliente, base_url, base, f"Alocar {unico()}")

    resposta = cliente.post(f"{base_url}/alocacoes", json={
        "atividade_id": id_atividade,
        "recurso_id": base["recurso_id"],
    })

    assert resposta.status_code == 200
    assert resposta.json() == {"mensagem": "Recurso alocado"}
    assert consultar(
        "SELECT recurso_id FROM alocacoes WHERE atividade_id = %s", (id_atividade,)
    ) == [(base["recurso_id"],)]
    assert consultar(
        "SELECT count(*) FROM logs WHERE usuario_id = %s AND acao = 'ALOCACAO_RECURSO'", (usuario["id"],)
    ) == [(1,)]


def test_alocar_semRecurso_deveRetornar400ComMensagem(base_url, professor):
    cliente, _ = professor
    base = criar_cadastros_base()
    id_atividade = criar_atividade(cliente, base_url, base, f"Sem recurso {unico()}")

    resposta = cliente.post(f"{base_url}/alocacoes", json={"atividade_id": id_atividade})

    assert resposta.status_code == 400
    assert resposta.json()["erro"] == "Escolha uma atividade e um recurso"
    assert consultar("SELECT id FROM alocacoes WHERE atividade_id = %s", (id_atividade,)) == []


def test_alocar_comAtividadeInexistente_deveRetornar404ComMensagem(base_url, professor):
    cliente, _ = professor
    base = criar_cadastros_base()

    resposta = cliente.post(f"{base_url}/alocacoes", json={
        "atividade_id": 999999999,
        "recurso_id": base["recurso_id"],
    })

    assert resposta.status_code == 404
    assert resposta.json()["erro"] == "Atividade nao encontrada"


def test_alocar_comRecursoInexistente_deveRetornar404ComMensagem(base_url, professor):
    cliente, _ = professor
    base = criar_cadastros_base()
    id_atividade = criar_atividade(cliente, base_url, base, f"Recurso fantasma {unico()}")

    resposta = cliente.post(f"{base_url}/alocacoes", json={
        "atividade_id": id_atividade,
        "recurso_id": 999999999,
    })

    assert resposta.status_code == 404
    assert resposta.json()["erro"] == "Recurso nao encontrado"
    assert consultar("SELECT id FROM alocacoes WHERE atividade_id = %s", (id_atividade,)) == []


def test_alocar_comRecursoJaOcupadoNoHorario_deveRetornar400ComMensagemDeConflito(base_url, professor):
    cliente, _ = professor
    base = criar_cadastros_base()
    outra_base = criar_cadastros_base()  # outro professor e outra turma: so o recurso coincide
    id_primeira = criar_atividade(cliente, base_url, base, f"Primeira {unico()}", inicio="08:00", fim="10:00")
    id_segunda = criar_atividade(cliente, base_url, outra_base, f"Segunda {unico()}", inicio="09:00", fim="11:00")
    criar_alocacao(cliente, base_url, id_primeira, base["recurso_id"], base["recurso_nome"])

    resposta = cliente.post(f"{base_url}/alocacoes", json={
        "atividade_id": id_segunda,
        "recurso_id": base["recurso_id"],
    })

    assert resposta.status_code == 400
    assert resposta.json()["erro"] == "Esse recurso ja esta sendo usado nesse horario"
    assert consultar("SELECT id FROM alocacoes WHERE atividade_id = %s", (id_segunda,)) == []


def test_cadastrar_comProfessorEmOutraAtividadeNoHorario_deveRetornar400ERegistrarConflito(base_url, professor):
    cliente, _ = professor
    base = criar_cadastros_base()
    criar_atividade(cliente, base_url, base, f"Prof 1 {unico()}", inicio="14:00", fim="16:00")

    # mesma pessoa (professor_id) dando outra aula, para outra turma, no mesmo horario:
    # desde o cadastro o sistema ja bloqueia
    outra_turma = consultar("INSERT INTO turmas (nome) VALUES (%s) RETURNING id", (f"Turma B {unico()}",))[0][0]
    resposta = cliente.post(f"{base_url}/atividades", json=build_atividade_request(
        dict(base, turma_id=outra_turma), f"Prof 2 {unico()}", inicio="15:00", fim="17:00"
    ))

    assert resposta.status_code == 400
    assert resposta.json()["erro"] == "Esse professor ja tem outra atividade nesse horario"
    assert consultar("SELECT COUNT(*) FROM logs WHERE acao = 'CONFLITO_BLOQUEADO'")[0][0] >= 1


def test_alocar_comProfessorComOutraAlocacaoNoHorario_deveRetornar400ComMensagemDeConflito(base_url, professor):
    cliente, usuario = professor
    base = criar_cadastros_base()
    id_primeira = criar_atividade(cliente, base_url, base, f"Prof 1 {unico()}", inicio="14:00", fim="16:00")
    criar_alocacao(cliente, base_url, id_primeira, base["recurso_id"], base["recurso_nome"])

    # atividade antiga gravada direto no banco (de antes da regra do cadastro):
    # na alocacao o conflito continua sendo conferido
    outra_turma = consultar("INSERT INTO turmas (nome) VALUES (%s) RETURNING id", (f"Turma B {unico()}",))[0][0]
    id_segunda = consultar(
        "INSERT INTO atividades (disciplina_id, turma_id, professor_id, descricao, data, hora_inicio, hora_fim, usuario_id) "
        "VALUES (%s, %s, %s, %s, %s, '15:00', '17:00', %s) RETURNING id",
        (base["disciplina_id"], outra_turma, base["professor_id"], f"Prof 2 {unico()}", dia_futuro(0), usuario["id"]),
    )[0][0]

    resposta = cliente.post(f"{base_url}/alocacoes", json={
        "atividade_id": id_segunda,
        "recurso_id": base["recurso2_id"],
    })

    assert resposta.status_code == 400
    assert resposta.json()["erro"] == "Esse professor ja possui uma atividade nesse horario"


def test_alocar_atividadeDeOutroProfessor_deveRetornar403ENaoGravar(base_url, professor, outro_professor):
    cliente_dono, _ = professor
    cliente_intruso, _ = outro_professor
    base = criar_cadastros_base()
    id_atividade = criar_atividade(cliente_dono, base_url, base, f"Alheia {unico()}")

    resposta = cliente_intruso.post(f"{base_url}/alocacoes", json={
        "atividade_id": id_atividade,
        "recurso_id": base["recurso_id"],
    })

    assert resposta.status_code == 403
    assert resposta.json()["erro"] == "Voce nao tem permissao para essa atividade"
    assert consultar("SELECT id FROM alocacoes WHERE atividade_id = %s", (id_atividade,)) == []


# ---------- GET /alocacoes ----------

def test_fluxo_criarAtividadeAlocarRecursoEListar_deveMostrarDadosDasEntidadesRelacionadas(base_url, professor):
    cliente, _ = professor
    base = criar_cadastros_base()
    id_atividade = criar_atividade(
        cliente, base_url, base, f"Fluxo {unico()}", data=dia_futuro(10), inicio="19:00", fim="20:40"
    )
    id_alocacao = criar_alocacao(cliente, base_url, id_atividade, base["recurso2_id"], base["recurso2_nome"])

    resposta = cliente.get(f"{base_url}/alocacoes")

    assert resposta.status_code == 200
    item = next(a for a in resposta.json() if a["id"] == id_alocacao)
    assert item == {
        "id": id_alocacao,
        "disciplina": base["disciplina_nome"],
        "turma": base["turma_nome"],
        "professor": base["professor_nome"],
        "data": dia_futuro(10),
        "hora_inicio": "19:00:00",
        "hora_fim": "20:40:00",
        "recurso": base["recurso2_nome"],
        "tipo": "laboratorio",
    }


def test_listarAlocacoes_comoProfessor_naoDeveMostrarAlocacoesDeOutroProfessor(
    base_url, professor, outro_professor
):
    cliente_a, _ = professor
    cliente_b, _ = outro_professor
    _, _, id_alocacao_b = _preparar_alocacao(cliente_b, base_url)

    resposta = cliente_a.get(f"{base_url}/alocacoes")

    assert resposta.status_code == 200
    assert id_alocacao_b not in [a["id"] for a in resposta.json()]


def test_listarAlocacoes_semLogin_deveRetornar401ComMensagem(base_url, cliente_anonimo):
    resposta = cliente_anonimo.get(f"{base_url}/alocacoes")

    assert resposta.status_code == 401
    assert resposta.json()["erro"] == "Voce precisa estar logado"


# ---------- PUT /alocacoes/{id} ----------

def test_editar_comNovoRecurso_deveRetornar200EGravarNovoRecursoNoBanco(base_url, professor):
    cliente, _ = professor
    base, _, id_alocacao = _preparar_alocacao(cliente, base_url)

    resposta = cliente.put(f"{base_url}/alocacoes/{id_alocacao}", json={"recurso_id": base["recurso2_id"]})

    assert resposta.status_code == 200
    assert resposta.json() == {"mensagem": "Alocacao alterada"}
    assert consultar("SELECT recurso_id FROM alocacoes WHERE id = %s", (id_alocacao,)) == [(base["recurso2_id"],)]


def test_editar_comMesmoRecurso_deveRetornar400ComMensagem(base_url, professor):
    cliente, _ = professor
    base, _, id_alocacao = _preparar_alocacao(cliente, base_url)

    resposta = cliente.put(f"{base_url}/alocacoes/{id_alocacao}", json={"recurso_id": base["recurso_id"]})

    assert resposta.status_code == 400
    assert resposta.json()["erro"] == "Escolha um recurso diferente"


def test_editar_comRecursoNaoNumerico_deveRetornar400ComMensagem(base_url, professor):
    cliente, _ = professor
    base, _, id_alocacao = _preparar_alocacao(cliente, base_url)

    resposta = cliente.put(f"{base_url}/alocacoes/{id_alocacao}", json={"recurso_id": "abc"})

    assert resposta.status_code == 400
    assert resposta.json()["erro"] == "Recurso invalido"
    assert consultar("SELECT recurso_id FROM alocacoes WHERE id = %s", (id_alocacao,)) == [(base["recurso_id"],)]


def test_editar_comRecursoInexistente_deveRetornar404ComMensagem(base_url, professor):
    cliente, _ = professor
    base, _, id_alocacao = _preparar_alocacao(cliente, base_url)

    resposta = cliente.put(f"{base_url}/alocacoes/{id_alocacao}", json={"recurso_id": 999999999})

    assert resposta.status_code == 404
    assert resposta.json()["erro"] == "Recurso nao encontrado"
    assert consultar("SELECT recurso_id FROM alocacoes WHERE id = %s", (id_alocacao,)) == [(base["recurso_id"],)]


def test_editar_comIdInexistente_deveRetornar404ComMensagem(base_url, professor):
    cliente, _ = professor
    base = criar_cadastros_base()

    resposta = cliente.put(f"{base_url}/alocacoes/999999999", json={"recurso_id": base["recurso_id"]})

    assert resposta.status_code == 404
    assert resposta.json()["erro"] == "Alocacao nao encontrada"


# ---------- DELETE /alocacoes/{id} ----------

def test_cancelar_comIdExistente_deveRetornar200EAlocacaoDeixaDeExistir(base_url, professor):
    cliente, _ = professor
    _, _, id_alocacao = _preparar_alocacao(cliente, base_url)

    resposta = cliente.delete(f"{base_url}/alocacoes/{id_alocacao}")

    assert resposta.status_code == 200
    assert resposta.json() == {"mensagem": "Alocacao cancelada"}
    assert consultar("SELECT id FROM alocacoes WHERE id = %s", (id_alocacao,)) == []
    # efeito observavel pela API: cancelar de novo agora retorna 404
    assert cliente.delete(f"{base_url}/alocacoes/{id_alocacao}").status_code == 404


def test_cancelar_comIdInexistente_deveRetornar404ComMensagem(base_url, professor):
    cliente, _ = professor

    resposta = cliente.delete(f"{base_url}/alocacoes/999999999")

    assert resposta.status_code == 404
    assert resposta.json()["erro"] == "Alocacao nao encontrada"


# ---------- Seguranca: DELETE /alocacoes/{id} (401 / 403 / 2xx) ----------

def test_cancelar_semLogin_deveRetornar401EAlocacaoContinuaNoBanco(base_url, professor, cliente_anonimo):
    cliente, _ = professor
    _, _, id_alocacao = _preparar_alocacao(cliente, base_url)

    resposta = cliente_anonimo.delete(f"{base_url}/alocacoes/{id_alocacao}")

    assert resposta.status_code == 401
    assert resposta.json()["erro"] == "Voce precisa estar logado"
    assert consultar("SELECT id FROM alocacoes WHERE id = %s", (id_alocacao,)) == [(id_alocacao,)]


def test_cancelar_comoOutroProfessor_deveRetornar403EAlocacaoContinuaNoBanco(base_url, professor, outro_professor):
    cliente_dono, _ = professor
    cliente_intruso, _ = outro_professor
    _, _, id_alocacao = _preparar_alocacao(cliente_dono, base_url)

    resposta = cliente_intruso.delete(f"{base_url}/alocacoes/{id_alocacao}")

    assert resposta.status_code == 403
    assert resposta.json()["erro"] == "Voce nao tem permissao para cancelar essa alocacao"
    assert consultar("SELECT id FROM alocacoes WHERE id = %s", (id_alocacao,)) == [(id_alocacao,)]


def test_cancelar_comoCoordenador_deveRetornar200EAlocacaoDeixaDeExistir(base_url, professor, coordenador):
    cliente_prof, _ = professor
    cliente_coord, _ = coordenador
    _, _, id_alocacao = _preparar_alocacao(cliente_prof, base_url)

    resposta = cliente_coord.delete(f"{base_url}/alocacoes/{id_alocacao}")

    assert resposta.status_code == 200
    assert resposta.json() == {"mensagem": "Alocacao cancelada"}
    assert consultar("SELECT id FROM alocacoes WHERE id = %s", (id_alocacao,)) == []
