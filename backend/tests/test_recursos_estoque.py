import unittest
from unittest.mock import patch, MagicMock

from apoio_testes import criar_cliente
from controllers.recurso_controller import recurso_bp
from controllers.alocacao_controller import alocacao_bp
import models.alocacao_model as alocacao_model

CAMINHO = "controllers.recurso_controller."


def banco_falso(fetchone=None):
    banco = MagicMock()
    cursor = banco.cursor.return_value
    if isinstance(fetchone, list):
        cursor.fetchone.side_effect = fetchone
    else:
        cursor.fetchone.return_value = fetchone
    return banco, cursor


class TestCadastroDeRecurso(unittest.TestCase):

    def test_precisa_estar_logado(self):
        cliente = criar_cliente(recurso_bp)
        resposta = cliente.post("/recursos", json={"nome": "Notebooks", "tipo": "equipamento", "quantidade": 3})
        self.assertEqual(resposta.status_code, 401)

    def test_professor_nao_pode_cadastrar(self):
        cliente = criar_cliente(recurso_bp, usuario_id=2, perfil="professor")
        resposta = cliente.post("/recursos", json={"nome": "Notebooks", "tipo": "equipamento", "quantidade": 3})
        self.assertEqual(resposta.status_code, 403)

    @patch(CAMINHO + "registrar_log")
    @patch(CAMINHO + "cadastrar_recurso", return_value=10)
    @patch(CAMINHO + "buscar_recurso_por_nome", return_value=None)
    def test_coordenador_cadastra_com_quantidade(self, mock_nome, mock_cadastrar, mock_log):
        cliente = criar_cliente(recurso_bp, usuario_id=1, perfil="coordenador")
        resposta = cliente.post("/recursos", json={"nome": " Notebooks ", "tipo": "Equipamento", "quantidade": "3"})

        self.assertEqual(resposta.status_code, 201)
        mock_cadastrar.assert_called_once_with("Notebooks", "equipamento", 3)
        self.assertEqual(mock_log.call_args[0][1], "CADASTRO_RECURSO")

    def test_quantidade_invalida(self):
        cliente = criar_cliente(recurso_bp, usuario_id=1, perfil="coordenador")
        for quantidade in [0, -1, 1000, "abc", None]:
            resposta = cliente.post("/recursos", json={"nome": "Notebooks", "tipo": "equipamento", "quantidade": quantidade})
            self.assertEqual(resposta.status_code, 400, quantidade)

    def test_tipo_invalido(self):
        cliente = criar_cliente(recurso_bp, usuario_id=1, perfil="coordenador")
        resposta = cliente.post("/recursos", json={"nome": "Notebooks", "tipo": "carro", "quantidade": 1})
        self.assertEqual(resposta.status_code, 400)

    @patch(CAMINHO + "buscar_recurso_por_nome", return_value=(4,))
    def test_nome_repetido(self, mock_nome):
        cliente = criar_cliente(recurso_bp, usuario_id=1, perfil="coordenador")
        resposta = cliente.post("/recursos", json={"nome": "Projetor 01", "tipo": "equipamento", "quantidade": 1})
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.get_json()["erro"], "Ja existe um recurso com esse nome")


class TestAlteracaoDeRecurso(unittest.TestCase):

    @patch(CAMINHO + "registrar_log")
    @patch(CAMINHO + "alterar_recurso", return_value=True)
    @patch(CAMINHO + "buscar_recurso_por_nome", return_value=None)
    def test_coloca_em_manutencao(self, mock_nome, mock_alterar, mock_log):
        cliente = criar_cliente(recurso_bp, usuario_id=1, perfil="coordenador")
        resposta = cliente.put("/recursos/5", json={"nome": "Projetor 01", "tipo": "equipamento",
                                                    "quantidade": 2, "status": "manutencao"})
        self.assertEqual(resposta.status_code, 200)
        mock_alterar.assert_called_once_with(5, "Projetor 01", "equipamento", 2, "manutencao")

    @patch(CAMINHO + "buscar_recurso_por_nome", return_value=None)
    def test_status_invalido(self, mock_nome):
        cliente = criar_cliente(recurso_bp, usuario_id=1, perfil="coordenador")
        resposta = cliente.put("/recursos/5", json={"nome": "Projetor 01", "tipo": "equipamento",
                                                    "quantidade": 2, "status": "quebrado"})
        self.assertEqual(resposta.status_code, 400)

    @patch(CAMINHO + "alterar_recurso", return_value=False)
    @patch(CAMINHO + "buscar_recurso_por_nome", return_value=None)
    def test_recurso_inexistente(self, mock_nome, mock_alterar):
        cliente = criar_cliente(recurso_bp, usuario_id=1, perfil="coordenador")
        resposta = cliente.put("/recursos/99", json={"nome": "Projetor 09", "tipo": "equipamento", "quantidade": 1})
        self.assertEqual(resposta.status_code, 404)


class TestExclusaoDeRecurso(unittest.TestCase):

    def test_professor_nao_pode_excluir(self):
        cliente = criar_cliente(recurso_bp, usuario_id=2, perfil="professor")
        self.assertEqual(cliente.delete("/recursos/5").status_code, 403)

    @patch(CAMINHO + "excluir_recurso")
    @patch(CAMINHO + "contar_alocacoes_do_recurso", return_value=(2, 5))
    def test_nao_exclui_com_reserva_futura(self, mock_contar, mock_excluir):
        cliente = criar_cliente(recurso_bp, usuario_id=1, perfil="coordenador")
        resposta = cliente.delete("/recursos/5")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("ainda vao acontecer", resposta.get_json()["erro"])
        mock_excluir.assert_not_called()

    @patch(CAMINHO + "registrar_log")
    @patch(CAMINHO + "excluir_recurso", return_value=True)
    @patch(CAMINHO + "contar_alocacoes_do_recurso", return_value=(0, 3))
    def test_arquiva_quando_so_tem_aulas_antigas(self, mock_contar, mock_excluir, mock_log):
        cliente = criar_cliente(recurso_bp, usuario_id=1, perfil="coordenador")
        resposta = cliente.delete("/recursos/5")
        self.assertEqual(resposta.status_code, 200)
        mock_excluir.assert_called_once_with(5, arquivar=True)

    @patch(CAMINHO + "registrar_log")
    @patch(CAMINHO + "excluir_recurso", return_value=True)
    @patch(CAMINHO + "contar_alocacoes_do_recurso", return_value=(0, 0))
    def test_apaga_de_vez_quando_nunca_foi_usado(self, mock_contar, mock_excluir, mock_log):
        cliente = criar_cliente(recurso_bp, usuario_id=1, perfil="coordenador")
        resposta = cliente.delete("/recursos/5")
        self.assertEqual(resposta.status_code, 200)
        mock_excluir.assert_called_once_with(5, arquivar=False)
        self.assertEqual(mock_log.call_args[0][1], "EXCLUSAO_RECURSO")


class TestProximasReservas(unittest.TestCase):

    def test_professor_nao_ve(self):
        cliente = criar_cliente(recurso_bp, usuario_id=2, perfil="professor")
        self.assertEqual(cliente.get("/recursos/5/reservas").status_code, 403)

    @patch(CAMINHO + "buscar_proximas_reservas", return_value=[
        {"data": "2026-11-12", "hora_inicio": "10:00", "hora_fim": "11:30",
         "disciplina": "Banco de Dados", "turma": "7A", "professor": "Carlos Silva"}])
    def test_coordenador_ve_os_dias(self, mock_reservas):
        cliente = criar_cliente(recurso_bp, usuario_id=1, perfil="coordenador")
        resposta = cliente.get("/recursos/5/reservas")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()[0]["data"], "2026-11-12")
        mock_reservas.assert_called_once_with(5)


class TestEstoqueNoConflito(unittest.TestCase):

    def test_ainda_tem_unidade_livre(self):
        # 3 notebooks, 2 reservados no horario: pode alocar
        banco, cursor = banco_falso(fetchone=(3, "disponivel", 2))
        with patch.object(alocacao_model, "conectar", return_value=banco):
            self.assertIsNone(alocacao_model.procurar_conflito_recurso(6, "2026-11-12", "08:00", "10:00"))

    def test_todas_as_unidades_reservadas(self):
        banco, cursor = banco_falso(fetchone=(3, "disponivel", 3))
        with patch.object(alocacao_model, "conectar", return_value=banco):
            conflito = alocacao_model.procurar_conflito_recurso(6, "2026-11-12", "08:00", "10:00")
        self.assertEqual(conflito, (3, 3, "disponivel"))
        self.assertEqual(alocacao_model.mensagem_recurso_indisponivel(conflito),
                         "Recurso indisponivel nesse horario: as 3 unidades ja estao reservadas")

    def test_recurso_unico_mantem_a_mensagem_antiga(self):
        self.assertEqual(alocacao_model.mensagem_recurso_indisponivel((1, 1, "disponivel")),
                         "Esse recurso ja esta sendo usado nesse horario")

    def test_recurso_em_manutencao(self):
        banco, cursor = banco_falso(fetchone=(5, "manutencao", 0))
        with patch.object(alocacao_model, "conectar", return_value=banco):
            conflito = alocacao_model.procurar_conflito_recurso(6, "2026-11-12", "08:00", "10:00")
        self.assertIn("manutencao", alocacao_model.mensagem_recurso_indisponivel(conflito))

    def test_salvar_bloqueia_se_o_estoque_acabou_no_mesmo_instante(self):
        # quantidade 1 e ja tem 1 reserva: nao insere e desfaz a transacao
        banco, cursor = banco_falso(fetchone=[(1,), (1,)])
        with patch.object(alocacao_model, "conectar", return_value=banco):
            self.assertFalse(alocacao_model.salvar_alocacao(10, 5))
        banco.rollback.assert_called_once()
        banco.commit.assert_not_called()
        self.assertIn("FOR UPDATE", cursor.execute.call_args_list[0][0][0])

    def test_salvar_com_unidade_livre(self):
        banco, cursor = banco_falso(fetchone=[(2,), (1,)])
        with patch.object(alocacao_model, "conectar", return_value=banco):
            self.assertTrue(alocacao_model.salvar_alocacao(10, 5))
        banco.commit.assert_called_once()


class TestAlocacaoComEstoque(unittest.TestCase):

    @patch("controllers.alocacao_controller.salvar_alocacao", return_value=False)
    @patch("controllers.alocacao_controller.validar_conflitos", return_value=None)
    @patch("controllers.alocacao_controller.buscar_recurso", return_value=(5,))
    @patch("controllers.alocacao_controller.buscar_usuario_atividade", return_value=(1,))
    def test_duas_pessoas_ao_mesmo_tempo(self, mock_atividade, mock_recurso, mock_conflito, mock_salvar):
        cliente = criar_cliente(alocacao_bp, usuario_id=1, perfil="coordenador")
        resposta = cliente.post("/alocacoes", json={"atividade_id": 10, "recurso_id": 5})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("acabou de ser reservado", resposta.get_json()["erro"])


if __name__ == "__main__":
    unittest.main()
