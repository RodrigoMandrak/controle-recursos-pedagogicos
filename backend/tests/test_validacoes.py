import unittest
from datetime import date

import validacoes


class TestValidacoes(unittest.TestCase):

    def test_email_valido(self):
        self.assertTrue(validacoes.email_valido("professor@escola.com.br"))

    def test_email_sem_arroba(self):
        self.assertFalse(validacoes.email_valido("professorescola.com.br"))

    def test_email_vazio(self):
        self.assertFalse(validacoes.email_valido(""))
        self.assertFalse(validacoes.email_valido(None))

    def test_email_muito_grande(self):
        email = "a" * 145 + "@x.com"
        self.assertFalse(validacoes.email_valido(email))

    def test_senha_com_8_caracteres(self):
        self.assertTrue(validacoes.senha_valida("12345678"))

    def test_senha_curta(self):
        self.assertFalse(validacoes.senha_valida("1234567"))

    def test_senha_nula(self):
        self.assertFalse(validacoes.senha_valida(None))

    def test_nome_valido(self):
        self.assertTrue(validacoes.nome_valido("Ana"))

    def test_nome_curto(self):
        self.assertFalse(validacoes.nome_valido("Al"))

    def test_nome_so_espacos(self):
        # espacos nao contam como letras
        self.assertFalse(validacoes.nome_valido("     "))

    def test_nome_vazio(self):
        self.assertFalse(validacoes.nome_valido(""))

    def test_nome_muito_grande(self):
        self.assertFalse(validacoes.nome_valido("a" * 101))

    def test_texto_opcional_vazio(self):
        self.assertTrue(validacoes.texto_no_limite(None, 10))
        self.assertTrue(validacoes.texto_no_limite("", 10))

    def test_texto_dentro_do_limite(self):
        self.assertTrue(validacoes.texto_no_limite("a" * 500, 500))

    def test_texto_acima_do_limite(self):
        self.assertFalse(validacoes.texto_no_limite("a" * 501, 500))

    def test_converter_data_valida(self):
        self.assertEqual(
            validacoes.converter_data("2026-12-25"),
            date(2026, 12, 25)
        )

    def test_converter_data_inexistente(self):
        self.assertIsNone(validacoes.converter_data("2026-02-30"))

    def test_converter_data_formato_errado(self):
        self.assertIsNone(validacoes.converter_data("25/12/2026"))
        self.assertIsNone(validacoes.converter_data(None))

    def test_horario_com_e_sem_segundos(self):
        self.assertTrue(validacoes.horario_valido("08:30"))
        self.assertTrue(validacoes.horario_valido("08:30:00"))

    def test_horario_invalido(self):
        self.assertFalse(validacoes.horario_valido("25:00"))
        self.assertFalse(validacoes.horario_valido("abc"))
        self.assertFalse(validacoes.horario_valido(None))

    def test_data_passada(self):
        hoje = date(2026, 11, 9)
        self.assertTrue(validacoes.data_passada(date(2026, 11, 8), hoje))
        self.assertFalse(validacoes.data_passada(date(2026, 11, 9), hoje))
        self.assertFalse(validacoes.data_passada(date(2026, 11, 10), hoje))

    def test_data_passada_usa_dia_atual(self):
        # sem informar o "hoje", a funcao usa a data do computador
        self.assertFalse(validacoes.data_passada(date.today()))


if __name__ == "__main__":
    unittest.main()
