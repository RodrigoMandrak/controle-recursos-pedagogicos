import unittest
from unittest.mock import patch

from models import alocacao_model


class TestAlocacaoModel(unittest.TestCase):

    def test_atividade_nao_encontrada(self):
        with patch.object(
            alocacao_model,
            "pegar_atividade",
            return_value=None
        ):
            resultado = alocacao_model.validar_conflitos(999, 1)

        self.assertEqual(
            resultado,
            "Atividade nao encontrada"
        )

    def test_conflito_de_recurso(self):
        atividade = (
            "2026-10-10",
            "08:00",
            "09:00",
            1,
            1
        )

        with patch.object(
            alocacao_model,
            "pegar_atividade",
            return_value=atividade
        ), patch.object(
            alocacao_model,
            "procurar_conflito_recurso",
            return_value=(1,)
        ), patch.object(
            alocacao_model,
            "procurar_conflito_professor"
        ) as mock_professor, patch.object(
            alocacao_model,
            "procurar_conflito_turma"
        ) as mock_turma:

            resultado = alocacao_model.validar_conflitos(1, 5)

        self.assertEqual(
            resultado,
            "Esse recurso ja esta sendo usado nesse horario"
        )

        # se ja encontrou conflito de recurso,
        # nao precisa testar professor e turma
        mock_professor.assert_not_called()
        mock_turma.assert_not_called()

    def test_conflito_de_professor(self):
        atividade = (
            "2026-10-10",
            "08:00",
            "09:00",
            3,
            2
        )

        with patch.object(
            alocacao_model,
            "pegar_atividade",
            return_value=atividade
        ), patch.object(
            alocacao_model,
            "procurar_conflito_recurso",
            return_value=None
        ), patch.object(
            alocacao_model,
            "procurar_conflito_professor",
            return_value=(1,)
        ), patch.object(
            alocacao_model,
            "procurar_conflito_turma"
        ) as mock_turma:

            resultado = alocacao_model.validar_conflitos(1, 5)

        self.assertEqual(
            resultado,
            "Esse professor ja possui uma atividade nesse horario"
        )

        mock_turma.assert_not_called()

    def test_conflito_de_turma(self):
        atividade = (
            "2026-10-10",
            "08:00",
            "09:00",
            3,
            2
        )

        with patch.object(
            alocacao_model,
            "pegar_atividade",
            return_value=atividade
        ), patch.object(
            alocacao_model,
            "procurar_conflito_recurso",
            return_value=None
        ), patch.object(
            alocacao_model,
            "procurar_conflito_professor",
            return_value=None
        ), patch.object(
            alocacao_model,
            "procurar_conflito_turma",
            return_value=(1,)
        ):

            resultado = alocacao_model.validar_conflitos(1, 5)

        self.assertEqual(
            resultado,
            "Essa turma ja possui uma atividade nesse horario"
        )

    def test_sem_conflito(self):
        atividade = (
            "2026-10-10",
            "08:00",
            "09:00",
            3,
            2
        )

        with patch.object(
            alocacao_model,
            "pegar_atividade",
            return_value=atividade
        ), patch.object(
            alocacao_model,
            "procurar_conflito_recurso",
            return_value=None
        ), patch.object(
            alocacao_model,
            "procurar_conflito_professor",
            return_value=None
        ), patch.object(
            alocacao_model,
            "procurar_conflito_turma",
            return_value=None
        ):

            resultado = alocacao_model.validar_conflitos(1, 5)

        self.assertIsNone(resultado)

    def test_excecao_quando_banco_indisponivel(self):
        with patch(
            "models.alocacao_model.conectar",
            side_effect=ConnectionError("Banco indisponivel")
        ):
            with self.assertRaisesRegex(
                ConnectionError,
                "Banco indisponivel"
            ):
                alocacao_model.salvar_alocacao(1, 1)


if __name__ == "__main__":
    unittest.main()