import unittest
from unittest.mock import patch

from werkzeug.security import generate_password_hash

from models import usuario_model


class TestUsuarioModel(unittest.TestCase):

    def test_senha_correta(self):
        senha_hash = generate_password_hash("123456")

        resultado = usuario_model.conferir_senha(
            "123456",
            senha_hash
        )

        self.assertTrue(resultado)


    def test_senha_errada(self):
        senha_hash = generate_password_hash("123456")

        resultado = usuario_model.conferir_senha(
            "654321",
            senha_hash
        )

        self.assertFalse(resultado)


    def test_senha_vazia(self):
        senha_hash = generate_password_hash("123456")

        resultado = usuario_model.conferir_senha(
            "",
            senha_hash
        )

        self.assertFalse(resultado)


    def test_erro_ao_buscar_usuario(self):
        with patch(
            "models.usuario_model.conectar",
            side_effect=ConnectionError("Banco indisponivel")
        ):
            with self.assertRaisesRegex(
                ConnectionError,
                "Banco indisponivel"
            ):
                usuario_model.buscar_usuario_email(
                    "teste@teste.com"
                )


    def test_erro_ao_atualizar_senha(self):
        with patch(
            "models.usuario_model.conectar",
            side_effect=RuntimeError("Erro ao acessar o banco")
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Erro ao acessar o banco"
            ):
                usuario_model.atualizar_senha(
                    1,
                    "nova123"
                )


if __name__ == "__main__":
    unittest.main()