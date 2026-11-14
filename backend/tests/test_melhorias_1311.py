# testes das melhorias depois do mock:
# dados academicos, editar/cancelar atividade, conflito no cadastro,
# limite de login, filtros do log e exclusao de conta
import unittest
from datetime import date, timedelta
from unittest.mock import patch

from apoio_testes import criar_cliente
from controllers.academico_controller import academico_bp
from controllers.atividade_controller import atividade_bp
from controllers.log_controller import log_bp
from controllers.usuario_controller import usuario_bp

ACAD = "controllers.academico_controller.academico_model."
ATIV = "controllers.atividade_controller."
USU = "controllers.usuario_controller."
LOG = "controllers.log_controller."

AMANHA = (date.today() + timedelta(days=1)).isoformat()


def atividade(**mudancas):
    dados = {"disciplina_id": 1, "turma_id": 1, "professor_id": 1, "descricao": "Aula",
             "data": AMANHA, "hora_inicio": "08:00", "hora_fim": "10:00"}
    dados.update(mudancas)
    return dados


class TestDadosAcademicos(unittest.TestCase):

    def setUp(self):
        self.log = patch("controllers.academico_controller.registrar_log").start()
        patch(ACAD + "buscar_nome", return_value="7A").start()
        self.addCleanup(patch.stopall)
        self.coord = criar_cliente(academico_bp, usuario_id=1, perfil="coordenador")

    def test_professor_nao_cadastra(self):
        cliente = criar_cliente(academico_bp, usuario_id=2, perfil="professor")
        self.assertEqual(cliente.post("/turmas", json={"nome": "9C"}).status_code, 403)

    def test_sem_login(self):
        self.assertEqual(criar_cliente(academico_bp).post("/turmas", json={"nome": "9C"}).status_code, 401)

    def test_nome_vazio(self):
        self.assertEqual(self.coord.post("/disciplinas", json={"nome": "   "}).status_code, 400)

    @patch(ACAD + "cadastrar", return_value=9)
    @patch(ACAD + "nome_existe", return_value=False)
    def test_cadastra_e_tira_espacos(self, _, mock_cadastrar):
        resposta = self.coord.post("/disciplinas", json={"nome": "  Robótica   Educacional "})
        self.assertEqual(resposta.status_code, 201)
        mock_cadastrar.assert_called_once_with("disciplinas", "Robótica Educacional")
        self.assertEqual(self.log.call_args[0][1], "CADASTRO_DISCIPLINA")

    @patch(ACAD + "nome_existe", return_value=True)
    def test_nome_repetido(self, _):
        resposta = self.coord.post("/turmas", json={"nome": "7A"})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("Ja existe", resposta.get_json()["erro"])

    @patch(ACAD + "renomear", return_value=False)
    @patch(ACAD + "nome_existe", return_value=False)
    def test_renomear_inexistente(self, *_):
        self.assertEqual(self.coord.put("/turmas/99", json={"nome": "8B"}).status_code, 404)

    @patch(ACAD + "excluir")
    @patch(ACAD + "contar_atividades", return_value=(2, 5))
    def test_nao_exclui_com_atividade_futura(self, _, mock_excluir):
        resposta = self.coord.delete("/disciplinas/3")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("2 atividade", resposta.get_json()["erro"])
        mock_excluir.assert_not_called()

    @patch(ACAD + "excluir", return_value=True)
    @patch(ACAD + "contar_atividades", return_value=(0, 4))
    def test_arquiva_quando_tem_historico(self, _, mock_excluir):
        self.assertEqual(self.coord.delete("/turmas/3").status_code, 200)
        mock_excluir.assert_called_once_with("turmas", 3, arquivar=True)
        self.assertIn("7A", self.log.call_args[0][2])

    @patch(ACAD + "excluir", return_value=True)
    @patch(ACAD + "contar_atividades", return_value=(0, 0))
    def test_apaga_quando_nunca_usado(self, _, mock_excluir):
        self.assertEqual(self.coord.delete("/turmas/3").status_code, 200)
        mock_excluir.assert_called_once_with("turmas", 3, arquivar=False)

    @patch(ACAD + "excluir")
    @patch(ACAD + "professor_tem_conta", return_value=True)
    def test_professor_com_conta_nao_sai(self, _, mock_excluir):
        resposta = self.coord.delete("/professores/4")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("conta", resposta.get_json()["erro"])
        mock_excluir.assert_not_called()


class TestConflitoNoCadastro(unittest.TestCase):

    def setUp(self):
        self.salvar = patch(ATIV + "salvar_atividade").start()
        self.log = patch(ATIV + "registrar_log").start()
        patch(ATIV + "buscar_professor_do_usuario", return_value=None).start()
        self.ativos = patch(ATIV + "itens_ativos", return_value=True).start()
        self.conflito = patch(ATIV + "procurar_conflito_atividade", return_value=None).start()
        self.addCleanup(patch.stopall)
        self.cliente = criar_cliente(atividade_bp, usuario_id=4)

    def test_professor_em_dois_lugares(self):
        self.conflito.return_value = "professor"
        resposta = self.cliente.post("/atividades", json=atividade())
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("professor", resposta.get_json()["erro"])
        self.salvar.assert_not_called()
        # a tentativa bloqueada fica no log
        self.assertEqual(self.log.call_args[0][1], "CONFLITO_BLOQUEADO")

    def test_turma_em_dois_lugares(self):
        self.conflito.return_value = "turma"
        resposta = self.cliente.post("/atividades", json=atividade())
        self.assertIn("turma", resposta.get_json()["erro"])

    def test_item_excluido(self):
        self.ativos.return_value = False
        self.assertEqual(self.cliente.post("/atividades", json=atividade()).status_code, 400)
        self.salvar.assert_not_called()


class TestEditarCancelarAtividade(unittest.TestCase):

    def setUp(self):
        self.log = patch(ATIV + "registrar_log").start()
        patch(ATIV + "buscar_professor_do_usuario", return_value=None).start()
        patch(ATIV + "itens_ativos", return_value=True).start()
        self.conflito = patch(ATIV + "procurar_conflito_atividade", return_value=None).start()
        self.sem_vaga = patch(ATIV + "recursos_sem_vaga", return_value=[]).start()
        patch(ATIV + "descrever_atividade", return_value="Banco de Dados · 7A").start()
        self.alterar = patch(ATIV + "alterar_atividade").start()
        self.cancelar = patch(ATIV + "cancelar_atividade").start()
        # (dono, data, inicio, fim, ja_aconteceu)
        self.buscar = patch(ATIV + "buscar_atividade", return_value=(4, AMANHA, "08:00", "10:00", False)).start()
        self.addCleanup(patch.stopall)
        self.cliente = criar_cliente(atividade_bp, usuario_id=4)

    def test_edita_a_propria(self):
        resposta = self.cliente.put("/atividades/10", json=atividade(hora_inicio="09:00", hora_fim="11:00"))
        self.assertEqual(resposta.status_code, 200)
        self.alterar.assert_called_once()
        # na edicao a propria atividade nao conta como conflito
        self.assertEqual(self.conflito.call_args[0][5], 10)

    def test_nao_edita_de_outro_professor(self):
        self.buscar.return_value = (99, AMANHA, "08:00", "10:00", False)
        self.assertEqual(self.cliente.put("/atividades/10", json=atividade()).status_code, 403)
        self.alterar.assert_not_called()

    def test_coordenador_edita_qualquer_uma(self):
        self.buscar.return_value = (99, AMANHA, "08:00", "10:00", False)
        coord = criar_cliente(atividade_bp, usuario_id=1, perfil="coordenador")
        self.assertEqual(coord.put("/atividades/10", json=atividade()).status_code, 200)

    def test_nao_edita_o_que_ja_aconteceu(self):
        self.buscar.return_value = (4, "2026-01-10", "08:00", "10:00", True)
        self.assertEqual(self.cliente.put("/atividades/10", json=atividade()).status_code, 400)

    def test_inexistente(self):
        self.buscar.return_value = None
        self.assertEqual(self.cliente.delete("/atividades/10").status_code, 404)

    def test_recurso_sem_vaga_no_novo_horario(self):
        self.sem_vaga.return_value = ["Projetor"]
        resposta = self.cliente.put("/atividades/10", json=atividade())
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("Projetor", resposta.get_json()["erro"])
        self.alterar.assert_not_called()

    def test_cancela(self):
        resposta = self.cliente.delete("/atividades/10")
        self.assertEqual(resposta.status_code, 200)
        self.cancelar.assert_called_once_with(10)
        self.assertEqual(self.log.call_args[0][1], "CANCELAMENTO_ATIVIDADE")

    def test_nao_cancela_o_que_ja_aconteceu(self):
        self.buscar.return_value = (4, "2026-01-10", "08:00", "10:00", True)
        self.assertEqual(self.cliente.delete("/atividades/10").status_code, 400)
        self.cancelar.assert_not_called()


USUARIO = (1, "Mariana", "mariana@escola.com.br", "hash", "professor", "RGM123", True, "ativo")


class TestLimiteDeLogin(unittest.TestCase):

    def setUp(self):
        self.log = patch(USU + "registrar_log").start()
        patch(USU + "buscar_usuario_email", return_value=USUARIO).start()
        self.bloqueado = patch(USU + "minutos_bloqueado", return_value=0).start()
        self.errada = patch(USU + "registrar_senha_errada", return_value=False).start()
        self.zerar = patch(USU + "zerar_tentativas").start()
        self.conferir = patch(USU + "conferir_senha", return_value=False).start()
        self.addCleanup(patch.stopall)
        self.cliente = criar_cliente(usuario_bp)

    def entrar(self):
        return self.cliente.post("/login", json={"email": "mariana@escola.com.br", "senha": "x12345678"})

    def test_senha_errada_conta_tentativa(self):
        self.assertEqual(self.entrar().status_code, 401)
        self.errada.assert_called_once_with(1)

    def test_quinta_senha_errada_bloqueia(self):
        self.errada.return_value = True
        resposta = self.entrar()
        self.assertEqual(resposta.status_code, 429)
        self.assertEqual(self.log.call_args[0][1], "LOGIN_BLOQUEADO")

    def test_bloqueada_nem_confere_senha(self):
        self.bloqueado.return_value = 3
        resposta = self.entrar()
        self.assertEqual(resposta.status_code, 429)
        self.assertIn("3 minuto", resposta.get_json()["erro"])
        self.conferir.assert_not_called()

    def test_acertou_zera(self):
        self.conferir.return_value = True
        self.assertEqual(self.entrar().status_code, 200)
        self.zerar.assert_called_once_with(1)


class TestExclusaoDeConta(unittest.TestCase):

    def setUp(self):
        self.log = patch(USU + "registrar_log").start()
        self.addCleanup(patch.stopall)

    @patch(USU + "resumo_exclusao", return_value={"atividades_futuras": 2, "reservas_futuras": 3})
    def test_resumo_antes_de_excluir(self, _):
        cliente = criar_cliente(usuario_bp, usuario_id=1)
        self.assertEqual(cliente.get("/minha-conta/resumo-exclusao").get_json()["atividades_futuras"], 2)

    @patch(USU + "excluir_usuario", return_value=2)
    @patch(USU + "conferir_senha", return_value=True)
    @patch(USU + "buscar_usuario_id", return_value=USUARIO)
    def test_log_sem_nome(self, *_):
        cliente = criar_cliente(usuario_bp, usuario_id=1)
        self.assertEqual(cliente.delete("/minha-conta", json={"senha": "certa123"}).status_code, 200)
        usuario, acao, detalhes = self.log.call_args[0]
        self.assertIsNone(usuario)
        self.assertEqual(acao, "EXCLUSAO_CONTA")
        self.assertNotIn("Mariana", detalhes)
        self.assertIn("2 atividade", detalhes)


class TestFiltrosDoLog(unittest.TestCase):

    def setUp(self):
        self.coord = criar_cliente(log_bp, usuario_id=1, perfil="coordenador")

    @patch(LOG + "contar_logs", return_value=0)
    @patch(LOG + "buscar_logs", return_value=[])
    def test_repassa_filtros(self, mock_logs, _):
        self.coord.get("/logs?acao=LOGIN&usuario=Ana&data_inicio=2026-11-01&data_fim=2026-11-13")
        mock_logs.assert_called_once_with(limite=20, deslocamento=0, acao="LOGIN", usuario="Ana", texto=None,
                                          data_inicio="2026-11-01", data_fim="2026-11-13")

    @patch(LOG + "contar_logs", return_value=45)
    @patch(LOG + "buscar_logs", return_value=[])
    def test_paginas(self, mock_logs, _):
        resposta = self.coord.get("/logs?pagina=3").get_json()
        self.assertEqual((resposta["total"], resposta["paginas"], resposta["pagina"]), (45, 3, 3))
        self.assertEqual(mock_logs.call_args.kwargs["deslocamento"], 40)

    @patch(LOG + "contar_logs", return_value=5)
    @patch(LOG + "buscar_logs", return_value=[])
    def test_pagina_alem_do_fim_volta_para_a_ultima(self, mock_logs, _):
        self.assertEqual(self.coord.get("/logs?pagina=99").get_json()["pagina"], 1)
        self.assertEqual(self.coord.get("/logs?pagina=abc").get_json()["pagina"], 1)

    def test_data_invalida(self):
        self.assertEqual(self.coord.get("/logs?data_inicio=13/11/2026").status_code, 400)

    def test_periodo_invertido(self):
        self.assertEqual(self.coord.get("/logs?data_inicio=2026-11-13&data_fim=2026-11-01").status_code, 400)

    @patch(LOG + "buscar_acoes", return_value=["LOGIN", "CONFLITO_BLOQUEADO"])
    def test_lista_de_acoes(self, _):
        self.assertIn("LOGIN", self.coord.get("/logs/acoes").get_json())

    def test_professor_nao_ve(self):
        cliente = criar_cliente(log_bp, usuario_id=2, perfil="professor")
        self.assertEqual(cliente.get("/logs/acoes").status_code, 403)


if __name__ == "__main__":
    unittest.main()
