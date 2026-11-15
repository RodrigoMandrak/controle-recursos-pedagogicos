import unittest
import pytest
from unittest.mock import patch, Mock

from models import feriado_model


class TestFeriadoModel(unittest.TestCase):

    def setUp(self):
        feriado_model.limpar_cache()

    def test_data_invalida(self):
        resultado = feriado_model.verificar_feriado("2026-02-30")
        self.assertTrue(resultado.get("erro_data"))

    def test_ano_fora_da_faixa(self):
        resultado = feriado_model.verificar_feriado("0002-01-01")
        self.assertTrue(resultado.get("erro_data"))

    @patch("models.feriado_model.requests.get")
    def test_encontra_feriado(self, mock_get):
        resposta = Mock()
        resposta.status_code = 200
        resposta.json.return_value = [
            {
                "date": "2026-12-25",
                "name": "Natal",
                "type": "national"
            }
        ]
        mock_get.return_value = resposta

        resultado = feriado_model.verificar_feriado("2026-12-25")

        self.assertTrue(resultado["feriado"])
        self.assertEqual(resultado["nome"], "Natal")
        self.assertEqual(resultado["origem"], "api")

    @patch("models.feriado_model.requests.get")
    def test_data_que_nao_e_feriado(self, mock_get):
        resposta = Mock()
        resposta.status_code = 200
        resposta.json.return_value = [
            {
                "date": "2026-12-25",
                "name": "Natal",
                "type": "national"
            }
        ]
        mock_get.return_value = resposta

        resultado = feriado_model.verificar_feriado("2026-10-20")

        self.assertFalse(resultado["feriado"])
        self.assertIsNone(resultado["nome"])

    @patch("models.feriado_model.requests.get")
    def test_cache_evitar_nova_consulta(self, mock_get):
        resposta = Mock()
        resposta.status_code = 200
        resposta.json.return_value = [
            {
                "date": "2026-12-25",
                "name": "Natal",
                "type": "national"
            }
        ]
        mock_get.return_value = resposta

        primeira = feriado_model.verificar_feriado("2026-12-25")
        segunda = feriado_model.verificar_feriado("2026-01-01")

        self.assertEqual(primeira["origem"], "api")
        self.assertEqual(segunda["origem"], "cache")
        self.assertEqual(mock_get.call_count, 1)

    @patch("models.feriado_model.requests.get")
    def test_api_indisponivel(self, mock_get):
        mock_get.side_effect = feriado_model.requests.RequestException(
            "API indisponivel"
        )

        resultado = feriado_model.verificar_feriado("2026-12-25")

        self.assertTrue(resultado.get("erro_api"))


@pytest.mark.parametrize(
    "data, esperado",
    [
        ("2000-01-01", True),
        ("2100-12-31", True),
        ("1999-12-31", False),
        ("2101-01-01", False),
    ]
)
def test_validar_data_nos_limites(data, esperado):
    resultado = feriado_model.validar_data(data)

    assert resultado is esperado


@patch("models.feriado_model.requests.get")
def test_data_invalida_nao_consulta_api(mock_get):
    resultado = feriado_model.verificar_feriado("2026-02-30")

    assert resultado["erro_data"] is True
    mock_get.assert_not_called()


if __name__ == "__main__":
    unittest.main()