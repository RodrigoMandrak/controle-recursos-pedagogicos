import unittest
from unittest.mock import patch

from apoio_testes import criar_cliente
from controllers.usuario_controller import usuario_bp

CAMINHO = "controllers.usuario_controller."

# (id, nome, email, senha_hash, perfil, identificador, aceitou_termos, data_aceite)
USUARIO = (1, "Mariana", "mariana@escola.com.br", "hash", "professor", "RGM123", True, "2026-11-01 10:00:00")


def cadastro(**mudancas):
    dados = {
        "nome": "Mariana Souza",
        "email": "mariana@escola.com.br",
        "senha": "senha123",
        "confirmar_senha": "senha123",
        "identificador_institucional": "RGM123",
        "aceitou_termos": True,
    }
    dados.update(mudancas)
    return dados


class TestCadastro(unittest.TestCase):

    def setUp(self):
        self.cadastrar = patch(CAMINHO + "cadastrar_usuario").start()
        self.buscar = patch(CAMINHO + "buscar_usuario_email", return_value=None).start()
        self.addCleanup(patch.stopall)
        self.cliente = criar_cliente(usuario_bp)

    def enviar(self, dados):
        return self.cliente.post("/usuarios/cadastro", json=dados)

    def test_campos_obrigatorios(self):
        self.assertEqual(self.enviar(cadastro(nome="")).status_code, 400)

    def test_nome_curto(self):
        resposta = self.enviar(cadastro(nome="Al"))
        self.assertIn("nome", resposta.get_json()["erro"])

    def test_email_invalido(self):
        resposta = self.enviar(cadastro(email="email-sem-arroba"))
        self.assertEqual(resposta.get_json()["erro"], "Informe um email valido")

    def test_identificador_grande(self):
        self.assertEqual(self.enviar(cadastro(identificador_institucional="1" * 51)).status_code, 400)

    def test_senha_curta(self):
        resposta = self.enviar(cadastro(senha="123", confirmar_senha="123"))
        self.assertIn("8 caracteres", resposta.get_json()["erro"])

    def test_senhas_diferentes(self):
        resposta = self.enviar(cadastro(confirmar_senha="outra123"))
        self.assertEqual(resposta.get_json()["erro"], "As senhas nao conferem")

    def test_sem_aceitar_termos(self):
        self.assertEqual(self.enviar(cadastro(aceitou_termos=False)).status_code, 400)
        self.cadastrar.assert_not_called()

    def test_email_ja_cadastrado(self):
        self.buscar.return_value = USUARIO
        resposta = self.enviar(cadastro())
        self.assertEqual(resposta.get_json()["erro"], "Esse email ja esta cadastrado")

    def test_cadastro_cria_sempre_professor(self):
        # mesmo tentando mandar outro perfil, a conta nasce como professor
        resposta = self.enviar(cadastro(perfil="coordenador"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(self.cadastrar.call_args[0][3], "professor")


class TestLogin(unittest.TestCase):

    def setUp(self):
        self.log = patch(CAMINHO + "registrar_log").start()
        self.addCleanup(patch.stopall)
        self.cliente = criar_cliente(usuario_bp)

    def test_sem_email_ou_senha(self):
        self.assertEqual(self.cliente.post("/login", json={"email": ""}).status_code, 400)

    @patch(CAMINHO + "buscar_usuario_email", return_value=None)
    def test_email_nao_existe(self, _):
        resposta = self.cliente.post("/login", json={"email": "x@x.com", "senha": "12345678"})
        self.assertEqual(resposta.status_code, 401)

    @patch(CAMINHO + "conferir_senha", return_value=False)
    @patch(CAMINHO + "buscar_usuario_email", return_value=USUARIO)
    def test_senha_errada(self, *_):
        resposta = self.cliente.post("/login", json={"email": USUARIO[2], "senha": "errada12"})
        self.assertEqual(resposta.status_code, 401)
        self.log.assert_not_called()

    @patch(CAMINHO + "conferir_senha", return_value=True)
    @patch(CAMINHO + "buscar_usuario_email", return_value=USUARIO)
    def test_login_certo_abre_sessao(self, *_):
        resposta = self.cliente.post("/login", json={"email": USUARIO[2], "senha": "certa123"})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()["usuario"]["perfil"], "professor")
        self.log.assert_called_once()

        # depois do login a rota de usuario logado responde
        logado = self.cliente.get("/usuario-logado").get_json()
        self.assertEqual(logado["id"], 1)


class TestContaDoUsuario(unittest.TestCase):

    def setUp(self):
        self.log = patch(CAMINHO + "registrar_log").start()
        self.addCleanup(patch.stopall)

    def test_usuario_logado_sem_sessao(self):
        cliente = criar_cliente(usuario_bp)
        self.assertEqual(cliente.get("/usuario-logado").status_code, 401)

    def test_meus_dados_sem_login(self):
        cliente = criar_cliente(usuario_bp)
        self.assertEqual(cliente.get("/meus-dados").status_code, 401)

    @patch(CAMINHO + "buscar_usuario_id", return_value=None)
    def test_meus_dados_usuario_apagado(self, _):
        cliente = criar_cliente(usuario_bp, usuario_id=1)
        self.assertEqual(cliente.get("/meus-dados").status_code, 404)

    @patch(CAMINHO + "buscar_usuario_id", return_value=USUARIO)
    def test_meus_dados(self, _):
        cliente = criar_cliente(usuario_bp, usuario_id=1)
        dados = cliente.get("/meus-dados").get_json()
        self.assertEqual(dados["email"], USUARIO[2])
        self.assertTrue(dados["aceitou_termos"])
        # a senha nunca volta para o front
        self.assertNotIn("senha", dados)

    def test_excluir_sem_login(self):
        cliente = criar_cliente(usuario_bp)
        self.assertEqual(cliente.delete("/minha-conta", json={"senha": "x"}).status_code, 401)

    def test_coordenador_nao_exclui_a_propria_conta(self):
        cliente = criar_cliente(usuario_bp, usuario_id=1, perfil="coordenador")
        self.assertEqual(cliente.delete("/minha-conta", json={"senha": "x"}).status_code, 403)

    def test_excluir_sem_senha(self):
        cliente = criar_cliente(usuario_bp, usuario_id=1)
        self.assertEqual(cliente.delete("/minha-conta", json={}).status_code, 400)

    @patch(CAMINHO + "buscar_usuario_id", return_value=None)
    def test_excluir_usuario_nao_encontrado(self, _):
        cliente = criar_cliente(usuario_bp, usuario_id=1)
        self.assertEqual(cliente.delete("/minha-conta", json={"senha": "x"}).status_code, 404)

    @patch(CAMINHO + "excluir_usuario")
    @patch(CAMINHO + "conferir_senha", return_value=False)
    @patch(CAMINHO + "buscar_usuario_id", return_value=USUARIO)
    def test_excluir_com_senha_errada(self, _a, _b, mock_excluir):
        cliente = criar_cliente(usuario_bp, usuario_id=1)
        self.assertEqual(cliente.delete("/minha-conta", json={"senha": "errada"}).status_code, 401)
        mock_excluir.assert_not_called()

    @patch(CAMINHO + "excluir_usuario")
    @patch(CAMINHO + "conferir_senha", return_value=True)
    @patch(CAMINHO + "buscar_usuario_id", return_value=USUARIO)
    def test_excluir_conta(self, _a, _b, mock_excluir):
        cliente = criar_cliente(usuario_bp, usuario_id=1)
        resposta = cliente.delete("/minha-conta", json={"senha": "certa123"})
        self.assertEqual(resposta.status_code, 200)
        mock_excluir.assert_called_once_with(1)
        # a sessao e encerrada depois da exclusao
        self.assertEqual(cliente.get("/usuario-logado").status_code, 401)

    def test_logout(self):
        cliente = criar_cliente(usuario_bp, usuario_id=1)
        self.assertEqual(cliente.post("/logout").status_code, 200)
        self.log.assert_called_once()
        self.assertEqual(cliente.get("/usuario-logado").status_code, 401)

    def test_logout_sem_estar_logado(self):
        cliente = criar_cliente(usuario_bp)
        self.assertEqual(cliente.post("/logout").status_code, 200)
        self.log.assert_not_called()


if __name__ == "__main__":
    unittest.main()
