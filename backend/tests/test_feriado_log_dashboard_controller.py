from datetime import date
import unittest
from unittest.mock import patch

from apoio_testes import criar_cliente
from controllers.feriado_controller import feriado_bp
from controllers.log_controller import log_bp
from controllers.dashboard_controller import dashboard_bp


class TestFeriadoController(unittest.TestCase):

    def setUp(self):
        self.log = patch("controllers.feriado_controller.registrar_log").start()
        self.verificar = patch("controllers.feriado_controller.verificar_feriado").start()
        self.addCleanup(patch.stopall)
        self.cliente = criar_cliente(feriado_bp, usuario_id=1)

    def test_sem_login(self):
        cliente = criar_cliente(feriado_bp)
        self.assertEqual(cliente.get("/verificar-feriado?data=2026-12-25").status_code, 401)

    def test_sem_data(self):
        self.assertEqual(self.cliente.get("/verificar-feriado").status_code, 400)

    def test_data_invalida(self):
        self.verificar.return_value = {"erro_data": True, "mensagem": "Data invalida"}
        resposta = self.cliente.get("/verificar-feriado?data=2026-02-30")
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.log.call_args[0][1], "CONSULTA_FERIADO_INVALIDA")

    def test_api_fora_do_ar(self):
        self.verificar.return_value = {"erro_api": True}
        resposta = self.cliente.get("/verificar-feriado?data=2026-12-25")
        self.assertEqual(resposta.status_code, 503)
        self.assertEqual(self.log.call_args[0][1], "ERRO_API_FERIADOS")

    def test_e_feriado(self):
        self.verificar.return_value = {"feriado": True, "nome": "Natal", "origem": "api"}
        resposta = self.cliente.get("/verificar-feriado?data=2026-12-25")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Natal", self.log.call_args[0][2])

    def test_nao_e_feriado(self):
        self.verificar.return_value = {"feriado": False, "origem": "cache"}
        resposta = self.cliente.get("/verificar-feriado?data=2026-12-26")
        self.assertFalse(resposta.get_json()["feriado"])
        self.assertIn("nao e feriado", self.log.call_args[0][2])


class TestLogController(unittest.TestCase):

    def test_sem_login(self):
        cliente = criar_cliente(log_bp)
        self.assertEqual(cliente.get("/logs").status_code, 401)

    def test_professor_nao_ve_logs(self):
        cliente = criar_cliente(log_bp, usuario_id=1, perfil="professor")
        self.assertEqual(cliente.get("/logs").status_code, 403)

    @patch("controllers.log_controller.contar_logs", return_value=1)
    @patch("controllers.log_controller.buscar_logs", return_value=[{"id": 1, "acao": "LOGIN"}])
    def test_coordenador_ve_logs(self, *_):
        cliente = criar_cliente(log_bp, usuario_id=1, perfil="coordenador")
        resposta = cliente.get("/logs")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()["logs"][0]["acao"], "LOGIN")


class TestDashboardController(unittest.TestCase):

    def test_sem_login(self):
        cliente = criar_cliente(dashboard_bp)
        self.assertEqual(cliente.get("/dashboard").status_code, 401)

    @patch("controllers.dashboard_controller.buscar_atividades_por_mes", return_value=[])
    @patch("controllers.dashboard_controller.buscar_atividades_por_disciplina", return_value=[])
    @patch("controllers.dashboard_controller.buscar_recursos_mais_usados", return_value=[])
    @patch("controllers.dashboard_controller.buscar_indicadores", return_value={"total_atividades": 3})
    def test_monta_o_painel_com_o_perfil_da_sessao(self, mock_ind, mock_rec, mock_disc, mock_mes):
        cliente = criar_cliente(dashboard_bp, usuario_id=8, perfil="professor")
        dados = cliente.get("/dashboard").get_json()

        self.assertEqual(dados["perfil"], "professor")
        self.assertEqual(dados["indicadores"]["total_atividades"], 3)
        # todas as consultas recebem o usuario e o perfil (professor so ve o que e dele)
        sem_filtro = {"inicio": None, "fim": None, "disciplina": None}
        for mock in (mock_ind, mock_rec, mock_disc, mock_mes):
            mock.assert_called_once_with(8, "professor", sem_filtro)

    @patch("controllers.dashboard_controller.buscar_atividades_por_mes", return_value=[])
    @patch("controllers.dashboard_controller.buscar_atividades_por_disciplina", return_value=[])
    @patch("controllers.dashboard_controller.buscar_recursos_mais_usados", return_value=[])
    @patch("controllers.dashboard_controller.buscar_indicadores", return_value={})
    def test_filtro_de_periodo_e_disciplina(self, mock_ind, mock_rec, mock_disc, mock_mes):
        cliente = criar_cliente(dashboard_bp, usuario_id=1, perfil="coordenador")
        resposta = cliente.get("/dashboard?inicio=2026-09-01&fim=2026-11-30&disciplina=2")

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()["filtros"],
                         {"inicio": "2026-09-01", "fim": "2026-11-30", "disciplina": 2})
        filtros = mock_ind.call_args[0][2]
        self.assertEqual(filtros["inicio"], date(2026, 9, 1))
        self.assertEqual(filtros["fim"], date(2026, 11, 30))
        self.assertEqual(filtros["disciplina"], 2)

    def test_filtro_com_data_invalida(self):
        cliente = criar_cliente(dashboard_bp, usuario_id=1, perfil="coordenador")
        resposta = cliente.get("/dashboard?inicio=2026-02-30")
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.get_json()["erro"], "Data inicial invalida")

    def test_filtro_com_data_final_antes_da_inicial(self):
        cliente = criar_cliente(dashboard_bp, usuario_id=1, perfil="coordenador")
        resposta = cliente.get("/dashboard?inicio=2026-11-01&fim=2026-10-01")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("depois da data inicial", resposta.get_json()["erro"])

    def test_filtro_com_periodo_muito_grande(self):
        cliente = criar_cliente(dashboard_bp, usuario_id=1, perfil="coordenador")
        resposta = cliente.get("/dashboard?inicio=2024-01-01&fim=2026-01-01")
        self.assertEqual(resposta.status_code, 400)

    def test_filtro_com_disciplina_invalida(self):
        cliente = criar_cliente(dashboard_bp, usuario_id=1, perfil="coordenador")
        resposta = cliente.get("/dashboard?disciplina=abc")
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.get_json()["erro"], "Disciplina invalida")


if __name__ == "__main__":
    unittest.main()
