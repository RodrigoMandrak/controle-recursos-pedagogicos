import unittest
from unittest.mock import patch

from apoio_testes import criar_cliente
from controllers import alocacao_controller
from controllers.alocacao_controller import alocacao_bp

CAMINHO = "controllers.alocacao_controller."


class TestConverterId(unittest.TestCase):

    def test_numero_em_texto(self):
        self.assertEqual(alocacao_controller.converter_id("5"), 5)

    def test_texto_invalido(self):
        self.assertIsNone(alocacao_controller.converter_id("abc"))
        self.assertIsNone(alocacao_controller.converter_id(None))


class TestAlocarRecurso(unittest.TestCase):

    def setUp(self):
        # o registro de log nao e o foco destes testes
        self.log = patch(CAMINHO + "registrar_log").start()
        self.addCleanup(patch.stopall)

    def test_sem_login(self):
        cliente = criar_cliente(alocacao_bp)
        resposta = cliente.post("/alocacoes", json={"atividade_id": 1, "recurso_id": 1})
        self.assertEqual(resposta.status_code, 401)

    def test_campos_vazios(self):
        cliente = criar_cliente(alocacao_bp, usuario_id=1)
        resposta = cliente.post("/alocacoes", json={"atividade_id": 1})
        self.assertEqual(resposta.status_code, 400)

    def test_recurso_que_nao_e_numero(self):
        cliente = criar_cliente(alocacao_bp, usuario_id=1)
        resposta = cliente.post("/alocacoes", json={"atividade_id": 1, "recurso_id": "abc"})
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.get_json()["erro"], "Recurso invalido")

    @patch(CAMINHO + "buscar_usuario_atividade", return_value=None)
    def test_atividade_nao_existe(self, _):
        cliente = criar_cliente(alocacao_bp, usuario_id=1)
        resposta = cliente.post("/alocacoes", json={"atividade_id": 99, "recurso_id": 1})
        self.assertEqual(resposta.status_code, 404)

    @patch(CAMINHO + "buscar_usuario_atividade", return_value=(2,))
    def test_professor_nao_pode_alocar_em_atividade_de_outro(self, _):
        cliente = criar_cliente(alocacao_bp, usuario_id=1, perfil="professor")
        resposta = cliente.post("/alocacoes", json={"atividade_id": 5, "recurso_id": 1})
        self.assertEqual(resposta.status_code, 403)

    @patch(CAMINHO + "buscar_recurso", return_value=None)
    @patch(CAMINHO + "buscar_usuario_atividade", return_value=(1,))
    def test_recurso_nao_existe(self, *_):
        cliente = criar_cliente(alocacao_bp, usuario_id=1)
        resposta = cliente.post("/alocacoes", json={"atividade_id": 5, "recurso_id": 77})
        self.assertEqual(resposta.status_code, 404)

    @patch(CAMINHO + "salvar_alocacao")
    @patch(CAMINHO + "validar_conflitos", return_value="Esse recurso ja esta sendo usado nesse horario")
    @patch(CAMINHO + "buscar_recurso", return_value=(1,))
    @patch(CAMINHO + "buscar_usuario_atividade", return_value=(1,))
    def test_conflito_bloqueia_alocacao(self, _a, _b, _c, mock_salvar):
        cliente = criar_cliente(alocacao_bp, usuario_id=1)
        resposta = cliente.post("/alocacoes", json={"atividade_id": 5, "recurso_id": 1})
        self.assertEqual(resposta.status_code, 400)
        mock_salvar.assert_not_called()

    @patch(CAMINHO + "salvar_alocacao")
    @patch(CAMINHO + "validar_conflitos", return_value=None)
    @patch(CAMINHO + "buscar_recurso", return_value=(1,))
    @patch(CAMINHO + "buscar_usuario_atividade", return_value=(1,))
    def test_professor_aloca_na_propria_atividade(self, _a, _b, _c, mock_salvar):
        cliente = criar_cliente(alocacao_bp, usuario_id=1)
        resposta = cliente.post("/alocacoes", json={"atividade_id": 5, "recurso_id": "3"})
        self.assertEqual(resposta.status_code, 200)
        mock_salvar.assert_called_once_with(5, 3)
        self.log.assert_called_once()

    @patch(CAMINHO + "salvar_alocacao")
    @patch(CAMINHO + "validar_conflitos", return_value=None)
    @patch(CAMINHO + "buscar_recurso", return_value=(1,))
    @patch(CAMINHO + "buscar_usuario_atividade", return_value=(2,))
    def test_coordenador_aloca_em_qualquer_atividade(self, _a, _b, _c, mock_salvar):
        cliente = criar_cliente(alocacao_bp, usuario_id=1, perfil="coordenador")
        resposta = cliente.post("/alocacoes", json={"atividade_id": 5, "recurso_id": 3})
        self.assertEqual(resposta.status_code, 200)
        mock_salvar.assert_called_once()


class TestListarRecursosEAlocacoes(unittest.TestCase):

    def test_recursos_sem_login(self):
        cliente = criar_cliente(alocacao_bp)
        self.assertEqual(cliente.get("/recursos").status_code, 401)

    @patch(CAMINHO + "buscar_recursos", return_value=[{"id": 1, "nome": "Sala 204"}])
    def test_lista_recursos(self, _):
        cliente = criar_cliente(alocacao_bp, usuario_id=1)
        resposta = cliente.get("/recursos")
        self.assertEqual(resposta.get_json()[0]["nome"], "Sala 204")

    def test_alocacoes_sem_login(self):
        cliente = criar_cliente(alocacao_bp)
        self.assertEqual(cliente.get("/alocacoes").status_code, 401)

    @patch(CAMINHO + "buscar_alocacoes", return_value=[])
    def test_lista_alocacoes_usa_perfil_da_sessao(self, mock_buscar):
        cliente = criar_cliente(alocacao_bp, usuario_id=7, perfil="professor")
        resposta = cliente.get("/alocacoes")
        self.assertEqual(resposta.status_code, 200)
        mock_buscar.assert_called_once_with(7, "professor")


class TestEditarAlocacao(unittest.TestCase):

    def setUp(self):
        patch(CAMINHO + "registrar_log").start()
        self.addCleanup(patch.stopall)

    def test_sem_login(self):
        cliente = criar_cliente(alocacao_bp)
        self.assertEqual(cliente.put("/alocacoes/1", json={"recurso_id": 2}).status_code, 401)

    def test_sem_recurso(self):
        cliente = criar_cliente(alocacao_bp, usuario_id=1)
        self.assertEqual(cliente.put("/alocacoes/1", json={}).status_code, 400)

    def test_recurso_invalido(self):
        cliente = criar_cliente(alocacao_bp, usuario_id=1)
        self.assertEqual(cliente.put("/alocacoes/1", json={"recurso_id": "x"}).status_code, 400)

    @patch(CAMINHO + "buscar_alocacao", return_value=None)
    def test_alocacao_nao_existe(self, _):
        cliente = criar_cliente(alocacao_bp, usuario_id=1)
        self.assertEqual(cliente.put("/alocacoes/9", json={"recurso_id": 2}).status_code, 404)

    @patch(CAMINHO + "buscar_alocacao", return_value=(5, 1, 2))
    def test_professor_nao_altera_alocacao_de_outro(self, _):
        cliente = criar_cliente(alocacao_bp, usuario_id=1)
        self.assertEqual(cliente.put("/alocacoes/3", json={"recurso_id": 2}).status_code, 403)

    @patch(CAMINHO + "buscar_recurso", return_value=None)
    @patch(CAMINHO + "buscar_alocacao", return_value=(5, 1, 1))
    def test_novo_recurso_nao_existe(self, *_):
        cliente = criar_cliente(alocacao_bp, usuario_id=1)
        self.assertEqual(cliente.put("/alocacoes/3", json={"recurso_id": 99}).status_code, 404)

    @patch(CAMINHO + "buscar_recurso", return_value=(1,))
    @patch(CAMINHO + "buscar_alocacao", return_value=(5, 1, 1))
    def test_mesmo_recurso(self, *_):
        cliente = criar_cliente(alocacao_bp, usuario_id=1)
        resposta = cliente.put("/alocacoes/3", json={"recurso_id": 1})
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.get_json()["erro"], "Escolha um recurso diferente")

    @patch(CAMINHO + "alterar_alocacao")
    @patch(CAMINHO + "validar_conflitos", return_value="Esse recurso ja esta sendo usado nesse horario")
    @patch(CAMINHO + "buscar_recurso", return_value=(2,))
    @patch(CAMINHO + "buscar_alocacao", return_value=(5, 1, 1))
    def test_conflito_na_alteracao(self, _a, _b, _c, mock_alterar):
        cliente = criar_cliente(alocacao_bp, usuario_id=1)
        self.assertEqual(cliente.put("/alocacoes/3", json={"recurso_id": 2}).status_code, 400)
        mock_alterar.assert_not_called()

    @patch(CAMINHO + "alterar_alocacao")
    @patch(CAMINHO + "validar_conflitos", return_value=None)
    @patch(CAMINHO + "buscar_recurso", return_value=(2,))
    @patch(CAMINHO + "buscar_alocacao", return_value=(5, 1, 1))
    def test_altera_alocacao(self, _a, _b, _c, mock_alterar):
        cliente = criar_cliente(alocacao_bp, usuario_id=1)
        resposta = cliente.put("/alocacoes/3", json={"recurso_id": 2})
        self.assertEqual(resposta.status_code, 200)
        mock_alterar.assert_called_once_with(3, 2)


class TestExcluirAlocacao(unittest.TestCase):

    def setUp(self):
        patch(CAMINHO + "registrar_log").start()
        self.addCleanup(patch.stopall)

    def test_sem_login(self):
        cliente = criar_cliente(alocacao_bp)
        self.assertEqual(cliente.delete("/alocacoes/1").status_code, 401)

    @patch(CAMINHO + "buscar_alocacao", return_value=None)
    def test_alocacao_nao_existe(self, _):
        cliente = criar_cliente(alocacao_bp, usuario_id=1)
        self.assertEqual(cliente.delete("/alocacoes/1").status_code, 404)

    @patch(CAMINHO + "cancelar_alocacao")
    @patch(CAMINHO + "buscar_alocacao", return_value=(5, 1, 2))
    def test_professor_nao_cancela_alocacao_de_outro(self, _, mock_cancelar):
        cliente = criar_cliente(alocacao_bp, usuario_id=1)
        self.assertEqual(cliente.delete("/alocacoes/1").status_code, 403)
        mock_cancelar.assert_not_called()

    @patch(CAMINHO + "cancelar_alocacao")
    @patch(CAMINHO + "buscar_alocacao", return_value=(5, 1, 2))
    def test_coordenador_cancela(self, _, mock_cancelar):
        cliente = criar_cliente(alocacao_bp, usuario_id=1, perfil="coordenador")
        self.assertEqual(cliente.delete("/alocacoes/1").status_code, 200)
        mock_cancelar.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
