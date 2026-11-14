import unittest
from datetime import date, timedelta
from unittest.mock import patch

from apoio_testes import criar_cliente
from controllers.atividade_controller import atividade_bp

CAMINHO = "controllers.atividade_controller."

# data calculada a partir de hoje, para o teste nao quebrar com o passar dos dias
AMANHA = (date.today() + timedelta(days=1)).isoformat()
ONTEM = (date.today() - timedelta(days=1)).isoformat()


def atividade(**mudancas):
    dados = {
        "disciplina_id": 1,
        "turma_id": 1,
        "professor_id": 1,
        "descricao": "Aula pratica",
        "data": AMANHA,
        "hora_inicio": "08:00",
        "hora_fim": "10:00",
    }
    dados.update(mudancas)
    return dados


class TestCadastrarAtividade(unittest.TestCase):

    def setUp(self):
        self.salvar = patch(CAMINHO + "salvar_atividade").start()
        self.log = patch(CAMINHO + "registrar_log").start()
        self.meu_professor = patch(CAMINHO + "buscar_professor_do_usuario", return_value=None).start()
        self.ativos = patch(CAMINHO + "itens_ativos", return_value=True).start()
        self.conflito = patch(CAMINHO + "procurar_conflito_atividade", return_value=None).start()
        self.addCleanup(patch.stopall)
        self.cliente = criar_cliente(atividade_bp, usuario_id=4)

    def enviar(self, dados):
        return self.cliente.post("/atividades", json=dados)

    def test_sem_login(self):
        cliente = criar_cliente(atividade_bp)
        self.assertEqual(cliente.post("/atividades", json=atividade()).status_code, 401)

    def test_sem_disciplina(self):
        self.assertEqual(self.enviar(atividade(disciplina_id=None)).status_code, 400)

    def test_sem_horario(self):
        resposta = self.enviar(atividade(hora_fim=""))
        self.assertEqual(resposta.get_json()["erro"], "Preencha a data e o horario")

    def test_data_invalida(self):
        resposta = self.enviar(atividade(data="2026-02-30"))
        self.assertEqual(resposta.get_json()["erro"], "Data invalida")

    def test_data_passada(self):
        resposta = self.enviar(atividade(data=ONTEM))
        self.assertEqual(resposta.status_code, 400)
        self.salvar.assert_not_called()

    def test_horario_invalido(self):
        resposta = self.enviar(atividade(hora_inicio="99:00"))
        self.assertEqual(resposta.get_json()["erro"], "Horario invalido")

    def test_fim_antes_do_inicio(self):
        resposta = self.enviar(atividade(hora_inicio="10:00", hora_fim="09:00"))
        self.assertEqual(resposta.get_json()["erro"], "Horario final invalido")

    def test_fim_igual_ao_inicio(self):
        resposta = self.enviar(atividade(hora_inicio="10:00", hora_fim="10:00"))
        self.assertEqual(resposta.status_code, 400)

    def test_descricao_muito_grande(self):
        resposta = self.enviar(atividade(descricao="a" * 501))
        self.assertEqual(resposta.status_code, 400)

    def test_cadastra_atividade(self):
        resposta = self.enviar(atividade())
        self.assertEqual(resposta.status_code, 200)
        self.salvar.assert_called_once()
        # a atividade fica ligada ao usuario logado
        self.assertEqual(self.salvar.call_args[0][-1], 4)
        self.log.assert_called_once()


class TestListagens(unittest.TestCase):

    def test_atividades_sem_login(self):
        cliente = criar_cliente(atividade_bp)
        self.assertEqual(cliente.get("/atividades").status_code, 401)

    @patch(CAMINHO + "buscar_atividades", return_value=[])
    def test_atividades_usa_perfil(self, mock_buscar):
        cliente = criar_cliente(atividade_bp, usuario_id=3, perfil="coordenador")
        cliente.get("/atividades")
        mock_buscar.assert_called_once_with(3, "coordenador")

    @patch(CAMINHO + "buscar_professores", return_value=[{"id": 1, "nome": "Prof. Ana"}])
    @patch(CAMINHO + "buscar_turmas", return_value=[{"id": 1, "nome": "ES A"}])
    @patch(CAMINHO + "buscar_disciplinas", return_value=[{"id": 1, "nome": "IA"}])
    def test_listas_de_apoio(self, *_):
        cliente = criar_cliente(atividade_bp)
        self.assertEqual(cliente.get("/disciplinas").get_json()[0]["nome"], "IA")
        self.assertEqual(cliente.get("/turmas").get_json()[0]["nome"], "ES A")
        self.assertEqual(cliente.get("/professores").get_json()[0]["nome"], "Prof. Ana")


if __name__ == "__main__":
    unittest.main()
