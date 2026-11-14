# configuracao dos testes unitarios (os de integracao tem o proprio conftest)
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def textos_do_log_sem_banco(request):
    # o texto legivel do log ("Projetor reservado para Banco de Dados · 7A ...")
    # busca nomes no banco. Nos testes unitarios isso nao e o foco, entao vira um texto fixo.
    if "integracao" in str(request.node.fspath):
        yield
        return

    with patch("controllers.alocacao_controller.descrever_atividade", return_value="Atividade teste"), \
         patch("controllers.alocacao_controller.nome_recurso", return_value="Recurso teste"), \
         patch("controllers.recurso_controller.nome_recurso", return_value="Recurso teste"), \
         patch("controllers.atividade_controller.descrever_atividade", return_value="Atividade teste"):
        yield
