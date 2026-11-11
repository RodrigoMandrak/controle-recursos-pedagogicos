# testes dos models sem PostgreSQL: a conexao e trocada por um objeto falso (MagicMock)
import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from models import atividade_model
from models import dashboard_model
from models import log_model
from models import recuperacao_model


def banco_falso(fetchall=None, fetchone=None):
    banco = MagicMock()
    cursor = banco.cursor.return_value
    cursor.fetchall.return_value = fetchall or []
    cursor.fetchone.return_value = fetchone
    return banco, cursor


class TestAtividadeModel(unittest.TestCase):

    def test_salvar_atividade_faz_commit(self):
        banco, cursor = banco_falso()
        with patch.object(atividade_model, "conectar", return_value=banco):
            atividade_model.salvar_atividade(1, 2, 3, "Aula", "2026-12-01", "08:00", "10:00", 9)

        parametros = cursor.execute.call_args[0][1]
        self.assertEqual(parametros[-1], 9)
        banco.commit.assert_called_once()
        banco.close.assert_called_once()

    def test_professor_so_busca_as_proprias_atividades(self):
        linha = (1, "IA", "ES A", "Prof. Ana", "Aula", date(2026, 12, 1), "08:00:00", "10:00:00")
        banco, cursor = banco_falso(fetchall=[linha])
        with patch.object(atividade_model, "conectar", return_value=banco):
            lista = atividade_model.buscar_atividades(9, "professor")

        sql, parametros = cursor.execute.call_args[0]
        self.assertIn("WHERE a.usuario_id", sql)
        self.assertEqual(parametros, (9,))
        self.assertEqual(lista[0]["data"], "2026-12-01")

    def test_coordenador_busca_todas(self):
        banco, cursor = banco_falso()
        with patch.object(atividade_model, "conectar", return_value=banco):
            atividade_model.buscar_atividades(1, "coordenador")

        sql = cursor.execute.call_args[0][0]
        self.assertNotIn("WHERE", sql)

    def test_listas_de_apoio(self):
        for funcao in (
            atividade_model.buscar_disciplinas,
            atividade_model.buscar_turmas,
            atividade_model.buscar_professores,
        ):
            banco, _ = banco_falso(fetchall=[(1, "Item")])
            with patch.object(atividade_model, "conectar", return_value=banco):
                self.assertEqual(funcao(), [{"id": 1, "nome": "Item"}])


class TestLogModel(unittest.TestCase):

    def test_registrar_log(self):
        banco, cursor = banco_falso()
        with patch.object(log_model, "conectar", return_value=banco):
            log_model.registrar_log(1, "LOGIN", "detalhe")

        self.assertEqual(cursor.execute.call_args[0][1], (1, "LOGIN", "detalhe"))
        banco.commit.assert_called_once()

    def test_buscar_logs(self):
        banco, _ = banco_falso(fetchall=[(5, "Ana", "LOGIN", "entrou", "2026-11-09 10:00:00")])
        with patch.object(log_model, "conectar", return_value=banco):
            logs = log_model.buscar_logs()

        self.assertEqual(logs[0]["usuario"], "Ana")
        self.assertEqual(logs[0]["acao"], "LOGIN")


class TestDashboardModel(unittest.TestCase):

    def test_filtro_do_coordenador(self):
        self.assertEqual(dashboard_model.montar_filtro(1, "coordenador"), ("", ()))

    def test_filtro_do_professor(self):
        filtro, parametros = dashboard_model.montar_filtro(7, "professor")
        self.assertIn("a.usuario_id", filtro)
        self.assertEqual(parametros, (7,))

    def test_indicadores(self):
        banco, cursor = banco_falso()
        cursor.fetchone.side_effect = [(10,), (6,), (2,), (4,), (5,), (3,)]
        with patch.object(dashboard_model, "conectar", return_value=banco):
            indicadores = dashboard_model.buscar_indicadores(7, "professor")

        self.assertEqual(indicadores, {
            "total_atividades": 10,
            "total_alocacoes": 6,
            "atividades_hoje": 2,
            "sem_recurso": 4,
            "total_recursos": 5,
            "recursos_usados": 3,
        })

    def test_indicadores_do_coordenador_sem_filtro(self):
        banco, cursor = banco_falso(fetchone=(0,))
        with patch.object(dashboard_model, "conectar", return_value=banco):
            dashboard_model.buscar_indicadores(1, "coordenador")

        primeira_consulta = cursor.execute.call_args_list[0][0][0]
        self.assertNotIn("usuario_id", primeira_consulta)

    def test_recursos_mais_usados(self):
        banco, _ = banco_falso(fetchall=[("Laboratorio 1", "laboratorio", 4)])
        with patch.object(dashboard_model, "conectar", return_value=banco):
            lista = dashboard_model.buscar_recursos_mais_usados(1, "coordenador")

        self.assertEqual(lista, [{"recurso": "Laboratorio 1", "tipo": "laboratorio", "total": 4}])

    def test_por_disciplina(self):
        banco, _ = banco_falso(fetchall=[("IA", 3)])
        with patch.object(dashboard_model, "conectar", return_value=banco):
            lista = dashboard_model.buscar_atividades_por_disciplina(1, "coordenador")

        self.assertEqual(lista, [{"disciplina": "IA", "total": 3}])

    def test_por_mes_formata_ano_e_mes(self):
        banco, cursor = banco_falso(fetchall=[(date(2026, 11, 1), 2), (date(2026, 12, 1), 0)])
        with patch.object(dashboard_model, "conectar", return_value=banco):
            lista = dashboard_model.buscar_atividades_por_mes(7, "professor")

        self.assertEqual(lista[0], {"mes": "2026-11", "total": 2})
        self.assertEqual(lista[1]["total"], 0)
        self.assertIn("a.usuario_id = %s", cursor.execute.call_args[0][0])


    def test_filtro_com_periodo_e_disciplina(self):
        filtros = {"inicio": date(2026, 9, 1), "fim": date(2026, 11, 30), "disciplina": 2}
        filtro, parametros = dashboard_model.montar_filtro(7, "professor", filtros)
        self.assertEqual(filtro, "WHERE a.usuario_id = %s AND a.data >= %s AND a.data <= %s AND a.disciplina_id = %s")
        self.assertEqual(parametros, (7, date(2026, 9, 1), date(2026, 11, 30), 2))

    def test_filtro_sem_periodo_para_atividades_de_hoje(self):
        filtros = {"inicio": date(2026, 9, 1), "fim": date(2026, 11, 30), "disciplina": None}
        filtro, parametros = dashboard_model.montar_filtro(1, "coordenador", filtros, com_periodo=False)
        self.assertEqual((filtro, parametros), ("", ()))

    def test_meses_do_grafico_com_periodo(self):
        filtros = {"inicio": date(2026, 9, 15), "fim": date(2026, 11, 3)}
        self.assertEqual(dashboard_model.meses_do_grafico(filtros), (date(2026, 9, 1), date(2026, 11, 1)))

    def test_meses_do_grafico_virando_o_ano(self):
        self.assertEqual(dashboard_model.somar_meses(date(2026, 11, 1), 3), date(2027, 2, 1))
        self.assertEqual(dashboard_model.somar_meses(date(2026, 2, 1), -4), date(2025, 10, 1))

    def test_meses_do_grafico_sem_filtro_mostra_6_meses(self):
        primeiro, ultimo = dashboard_model.meses_do_grafico()
        meses = (ultimo.year - primeiro.year) * 12 + ultimo.month - primeiro.month + 1
        self.assertEqual(meses, 6)

    def test_por_mes_usa_o_filtro_no_join(self):
        banco, cursor = banco_falso(fetchall=[])
        filtros = {"inicio": date(2026, 9, 1), "fim": date(2026, 11, 30), "disciplina": 2}
        with patch.object(dashboard_model, "conectar", return_value=banco):
            dashboard_model.buscar_atividades_por_mes(1, "coordenador", filtros)

        sql, valores = cursor.execute.call_args[0]
        self.assertIn("a.disciplina_id = %s", sql)
        self.assertEqual(valores, (date(2026, 9, 1), date(2026, 11, 1), date(2026, 9, 1), date(2026, 11, 30), 2))

class TestRecuperacaoModel(unittest.TestCase):

    def test_token_criado_nao_vai_puro_para_o_banco(self):
        banco, cursor = banco_falso()
        with patch.object(recuperacao_model, "conectar", return_value=banco):
            token = recuperacao_model.criar_token_recuperacao(3)

        # o segundo execute grava o token; no banco fica so o hash
        token_gravado = cursor.execute.call_args_list[1][0][1][1]
        self.assertNotEqual(token_gravado, token)
        self.assertEqual(len(token_gravado), 64)
        banco.commit.assert_called_once()

    def test_buscar_token_usa_hash(self):
        banco, cursor = banco_falso(fetchone=(10, 3))
        with patch.object(recuperacao_model, "conectar", return_value=banco):
            resultado = recuperacao_model.buscar_token_valido("abc")

        self.assertEqual(resultado, (10, 3))
        self.assertNotEqual(cursor.execute.call_args[0][1][0], "abc")

    def test_marcar_token_utilizado(self):
        banco, cursor = banco_falso()
        with patch.object(recuperacao_model, "conectar", return_value=banco):
            recuperacao_model.marcar_token_utilizado(10)

        self.assertEqual(cursor.execute.call_args[0][1], (10,))
        banco.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
