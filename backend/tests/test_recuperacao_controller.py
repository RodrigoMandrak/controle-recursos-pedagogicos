import unittest
from unittest.mock import patch

from apoio_testes import criar_cliente
from controllers import recuperacao_controller
from controllers.recuperacao_controller import recuperacao_bp

CAMINHO = "controllers.recuperacao_controller."


class TestEsqueciSenha(unittest.TestCase):

    def setUp(self):
        self.log = patch(CAMINHO + "registrar_log").start()
        self.email = patch(CAMINHO + "enviar_email_recuperacao").start()
        self.addCleanup(patch.stopall)
        self.cliente = criar_cliente(recuperacao_bp)

    def test_sem_email(self):
        self.assertEqual(self.cliente.post("/esqueci-senha", json={}).status_code, 400)

    @patch(CAMINHO + "buscar_usuario_email", return_value=None)
    def test_email_nao_cadastrado_tem_resposta_generica(self, _):
        # nao pode revelar se o email existe ou nao
        resposta = self.cliente.post("/esqueci-senha", json={"email": "nao@existe.com"})
        self.assertEqual(resposta.status_code, 200)
        self.email.assert_not_called()

    @patch(CAMINHO + "criar_token_recuperacao", return_value="token123")
    @patch(CAMINHO + "buscar_usuario_email", return_value=(1, "Ana"))
    def test_envia_link(self, _a, _b):
        resposta = self.cliente.post("/esqueci-senha", json={"email": " ANA@escola.com.br "})
        self.assertEqual(resposta.status_code, 200)
        destino, nome, link = self.email.call_args[0]
        # o email e normalizado antes da busca
        self.assertEqual(destino, "ana@escola.com.br")
        self.assertIn("token123", link)
        self.log.assert_called_once()

    @patch(CAMINHO + "criar_token_recuperacao", return_value="token123")
    @patch(CAMINHO + "buscar_usuario_email", return_value=(1, "Ana"))
    def test_falha_no_envio_do_email(self, _a, _b):
        self.email.side_effect = Exception("smtp fora do ar")
        resposta = self.cliente.post("/esqueci-senha", json={"email": "ana@escola.com.br"})
        self.assertEqual(resposta.status_code, 500)


class TestEnvioDeEmail(unittest.TestCase):

    @patch(CAMINHO + "smtplib.SMTP_SSL")
    def test_monta_e_envia_mensagem(self, mock_smtp):
        servidor = mock_smtp.return_value.__enter__.return_value
        recuperacao_controller.enviar_email_recuperacao("ana@escola.com.br", "Ana", "http://link")
        mensagem = servidor.send_message.call_args[0][0]
        self.assertEqual(mensagem["To"], "ana@escola.com.br")
        self.assertIn("http://link", mensagem.get_content())


class TestRedefinirSenha(unittest.TestCase):

    def setUp(self):
        self.log = patch(CAMINHO + "registrar_log").start()
        self.atualizar = patch(CAMINHO + "atualizar_senha").start()
        self.marcar = patch(CAMINHO + "marcar_token_utilizado").start()
        self.addCleanup(patch.stopall)
        self.cliente = criar_cliente(recuperacao_bp)

    def enviar(self, **dados):
        return self.cliente.post("/redefinir-senha", json=dados)

    def test_sem_token(self):
        self.assertEqual(self.enviar(senha="12345678", confirmar_senha="12345678").status_code, 400)

    def test_sem_senha(self):
        self.assertEqual(self.enviar(token="t").status_code, 400)

    def test_senhas_diferentes(self):
        resposta = self.enviar(token="t", senha="12345678", confirmar_senha="87654321")
        self.assertEqual(resposta.get_json()["erro"], "As senhas nao conferem")

    def test_senha_curta(self):
        self.assertEqual(self.enviar(token="t", senha="123", confirmar_senha="123").status_code, 400)

    @patch(CAMINHO + "buscar_token_valido", return_value=None)
    def test_link_expirado_ou_usado(self, _):
        resposta = self.enviar(token="t", senha="12345678", confirmar_senha="12345678")
        self.assertEqual(resposta.get_json()["erro"], "Link invalido ou expirado")
        self.atualizar.assert_not_called()

    @patch(CAMINHO + "buscar_token_valido", return_value=(10, 1))
    def test_redefine_e_invalida_o_link(self, _):
        resposta = self.enviar(token="t", senha="12345678", confirmar_senha="12345678")
        self.assertEqual(resposta.status_code, 200)
        self.atualizar.assert_called_once_with(1, "12345678")
        self.marcar.assert_called_once_with(10)


if __name__ == "__main__":
    unittest.main()
