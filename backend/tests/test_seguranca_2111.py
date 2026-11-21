"""Correcoes de seguranca pedidas na orientacao (item 21)."""

import importlib
import os
import unittest
from unittest.mock import patch

from models.log_model import buscar_logs, mascarar_dados_pessoais


class TestMascaraNosLogs(unittest.TestCase):

    def test_email_fica_parcial(self):
        self.assertEqual(
            mascarar_dados_pessoais("Cadastro de ana.souza@escola.com.br recusado"),
            "Cadastro de an*****@escola.com.br recusado",
        )

    def test_celular_fica_parcial(self):
        self.assertEqual(mascarar_dados_pessoais("Contato (11) 91234-5678"), "Contato (11) 9****-5678")
        self.assertEqual(mascarar_dados_pessoais("Contato 11912345678"), "Contato (11) 9****-5678")

    def test_fixo_fica_parcial(self):
        self.assertEqual(mascarar_dados_pessoais("Fone (11) 3234-5678"), "Fone (11) ****-5678")

    def test_nao_mexe_em_data_hora_e_numeros_curtos(self):
        texto = "Banco de Dados · 7A · 22/09/2026 08:00-10:00 · Prof. Ana; atividade 51 e recurso 3"
        self.assertEqual(mascarar_dados_pessoais(texto), texto)

    def test_texto_vazio(self):
        self.assertIsNone(mascarar_dados_pessoais(None))
        self.assertEqual(mascarar_dados_pessoais(""), "")

    @patch("models.log_model.conectar")
    def test_buscar_logs_devolve_mascarado(self, mock_conectar):
        cursor = mock_conectar.return_value.cursor.return_value
        cursor.fetchall.return_value = [
            (1, "Coordenador", "RECUSA_CADASTRO", "Cadastro de joao@gmail.com recusado", "2026-11-21 10:00:00"),
        ]
        logs = buscar_logs()
        self.assertEqual(logs[0]["detalhes"], "Cadastro de jo*****@gmail.com recusado")


class TestCookieDaSessao(unittest.TestCase):

    def carregar_app(self, **variaveis):
        with patch.dict(os.environ, variaveis, clear=False), patch("banco.atualizar_estrutura"):
            for nome in ("RENDER", "COOKIE_SAMESITE"):
                if nome not in variaveis:
                    os.environ.pop(nome, None)
            import app as modulo
            return importlib.reload(modulo).app

    def test_no_computador(self):
        app = self.carregar_app()
        self.assertTrue(app.config["SESSION_COOKIE_HTTPONLY"])
        self.assertEqual(app.config["SESSION_COOKIE_SAMESITE"], "Lax")
        self.assertFalse(app.config["SESSION_COOKIE_SECURE"])

    def test_no_render_liga_secure(self):
        app = self.carregar_app(RENDER="true")
        self.assertTrue(app.config["SESSION_COOKIE_SECURE"])
        self.assertTrue(app.config["SESSION_COOKIE_HTTPONLY"])

    def test_samesite_none_exige_secure(self):
        app = self.carregar_app(COOKIE_SAMESITE="None")
        self.assertEqual(app.config["SESSION_COOKIE_SAMESITE"], "None")
        self.assertTrue(app.config["SESSION_COOKIE_SECURE"])


if __name__ == "__main__":
    unittest.main()


class TestTentativasNoBanco(unittest.TestCase):

    def setUp(self):
        self.conectar = patch("models.usuario_model.conectar").start()
        self.cursor = self.conectar.return_value.cursor.return_value
        self.addCleanup(patch.stopall)

    def test_minutos_bloqueado_usa_email_e_ip(self):
        from models.usuario_model import minutos_bloqueado
        self.cursor.fetchone.return_value = (3,)
        self.assertEqual(minutos_bloqueado("a@b.com", "1.2.3.4"), 3)
        self.assertEqual(self.cursor.execute.call_args[0][1], ("a@b.com", "1.2.3.4"))

    def test_minutos_bloqueado_liberado(self):
        from models.usuario_model import minutos_bloqueado
        self.cursor.fetchone.return_value = None
        self.assertEqual(minutos_bloqueado("a@b.com", "1.2.3.4"), 0)

    def test_quinta_tentativa_bloqueia_e_zera_contagem(self):
        from models.usuario_model import registrar_senha_errada
        self.cursor.fetchone.return_value = (5,)
        self.assertTrue(registrar_senha_errada("a@b.com", "1.2.3.4"))
        self.assertEqual(self.cursor.execute.call_count, 2)

    def test_tentativa_comum_nao_bloqueia(self):
        from models.usuario_model import registrar_senha_errada
        self.cursor.fetchone.return_value = (2,)
        self.assertFalse(registrar_senha_errada("a@b.com", "1.2.3.4"))
        self.assertEqual(self.cursor.execute.call_count, 1)

    def test_zerar_apaga_so_aquele_email_e_ip(self):
        from models.usuario_model import zerar_tentativas
        zerar_tentativas("a@b.com", "1.2.3.4")
        self.assertIn("DELETE FROM tentativas_login", self.cursor.execute.call_args[0][0])
        self.assertEqual(self.cursor.execute.call_args[0][1], ("a@b.com", "1.2.3.4"))
