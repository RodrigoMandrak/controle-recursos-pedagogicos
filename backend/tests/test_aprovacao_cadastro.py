import unittest
from unittest.mock import patch

from apoio_testes import criar_cliente
from controllers.usuario_controller import usuario_bp
from controllers.solicitacao_controller import solicitacao_bp
from controllers.atividade_controller import atividade_bp

# (id, nome, email, senha_hash, perfil, identificador, aceitou_termos, status)
PENDENTE = (9, "Mariana", "mariana@escola.com.br", "hash", "professor", "RGM1", True, "pendente")
ATIVO = (9, "Mariana", "mariana@escola.com.br", "hash", "professor", "RGM1", True, "ativo")
SOL = "controllers.solicitacao_controller."


class TestCadastroPendente(unittest.TestCase):

    @patch("controllers.usuario_controller.buscar_usuario_email", return_value=None)
    @patch("controllers.usuario_controller.cadastrar_usuario")
    def test_cadastro_nasce_pendente(self, mock_cadastrar, _):
        cliente = criar_cliente(usuario_bp)
        resposta = cliente.post("/usuarios/cadastro", json={
            "nome": "Mariana Souza", "email": "mariana@escola.com.br", "senha": "senha123",
            "confirmar_senha": "senha123", "identificador_institucional": "RGM1", "aceitou_termos": True})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(mock_cadastrar.call_args.kwargs["status"], "pendente")
        self.assertIn("aprovacao", resposta.get_json()["mensagem"])

    @patch("controllers.usuario_controller.zerar_tentativas")
    @patch("controllers.usuario_controller.minutos_bloqueado", return_value=0)
    @patch("controllers.usuario_controller.registrar_log")
    @patch("controllers.usuario_controller.conferir_senha", return_value=True)
    @patch("controllers.usuario_controller.buscar_usuario_email", return_value=PENDENTE)
    def test_pendente_nao_entra(self, *_):
        cliente = criar_cliente(usuario_bp)
        resposta = cliente.post("/login", json={"email": "mariana@escola.com.br", "senha": "senha123"})
        self.assertEqual(resposta.status_code, 403)
        self.assertIn("aguardando aprovacao", resposta.get_json()["erro"])

    @patch("controllers.usuario_controller.zerar_tentativas")
    @patch("controllers.usuario_controller.minutos_bloqueado", return_value=0)
    @patch("controllers.usuario_controller.registrar_log")
    @patch("controllers.usuario_controller.conferir_senha", return_value=True)
    @patch("controllers.usuario_controller.buscar_usuario_email", return_value=ATIVO)
    def test_aprovado_entra(self, *_):
        cliente = criar_cliente(usuario_bp)
        resposta = cliente.post("/login", json={"email": "mariana@escola.com.br", "senha": "senha123"})
        self.assertEqual(resposta.status_code, 200)


class TestSolicitacoes(unittest.TestCase):

    def test_professor_nao_ve_solicitacoes(self):
        cliente = criar_cliente(solicitacao_bp, usuario_id=2, perfil="professor")
        self.assertEqual(cliente.get("/solicitacoes").status_code, 403)

    @patch(SOL + "buscar_solicitacoes", return_value=[])
    def test_busca_por_email(self, mock_buscar):
        cliente = criar_cliente(solicitacao_bp, usuario_id=1, perfil="coordenador")
        cliente.get("/solicitacoes?email= Mariana@ ")
        mock_buscar.assert_called_once_with("mariana@")

    @patch(SOL + "registrar_log")
    @patch(SOL + "aprovar_solicitacao", return_value="Mariana")
    def test_aprovar_da_o_cargo(self, mock_aprovar, mock_log):
        cliente = criar_cliente(solicitacao_bp, usuario_id=1, perfil="coordenador")
        resposta = cliente.post("/solicitacoes/9/aprovar")
        self.assertEqual(resposta.status_code, 200)
        mock_aprovar.assert_called_once_with(9)
        self.assertEqual(mock_log.call_args[0][1], "APROVACAO_CADASTRO")

    @patch(SOL + "aprovar_solicitacao", return_value=None)
    def test_aprovar_inexistente(self, _):
        cliente = criar_cliente(solicitacao_bp, usuario_id=1, perfil="coordenador")
        self.assertEqual(cliente.post("/solicitacoes/99/aprovar").status_code, 404)

    @patch(SOL + "registrar_log")
    @patch(SOL + "recusar_solicitacao", return_value="x@escola.com.br")
    def test_recusar(self, mock_recusar, mock_log):
        cliente = criar_cliente(solicitacao_bp, usuario_id=1, perfil="coordenador")
        self.assertEqual(cliente.delete("/solicitacoes/9").status_code, 200)
        self.assertEqual(mock_log.call_args[0][1], "RECUSA_CADASTRO")


class TestProfessorNoProprioNome(unittest.TestCase):

    @patch("controllers.atividade_controller.procurar_conflito_atividade", return_value=None)
    @patch("controllers.atividade_controller.itens_ativos", return_value=True)
    @patch("controllers.atividade_controller.registrar_log")
    @patch("controllers.atividade_controller.salvar_atividade")
    @patch("controllers.atividade_controller.buscar_professor_do_usuario", return_value=7)
    def test_professor_nao_cadastra_para_outro(self, _, mock_salvar, *__):
        from datetime import date, timedelta
        amanha = (date.today() + timedelta(days=1)).isoformat()
        cliente = criar_cliente(atividade_bp, usuario_id=4, perfil="professor")
        cliente.post("/atividades", json={"disciplina_id": 1, "turma_id": 1, "professor_id": 3,
                                          "descricao": "Aula", "data": amanha,
                                          "hora_inicio": "08:00", "hora_fim": "10:00"})
        # mandou professor 3, mas a atividade fica no nome dele (7)
        self.assertEqual(mock_salvar.call_args[0][2], 7)


if __name__ == "__main__":
    unittest.main()
