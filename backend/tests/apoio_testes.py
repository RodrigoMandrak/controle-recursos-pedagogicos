# funcoes de apoio para os testes unitarios dos controllers
# cria um Flask so com a rota testada, sem precisar do banco
from flask import Flask


def criar_cliente(blueprint, usuario_id=None, perfil="professor", nome="Teste"):
    app = Flask(__name__)
    app.secret_key = "chave-dos-testes"
    app.config["TESTING"] = True
    app.register_blueprint(blueprint)

    cliente = app.test_client()

    # simula um usuario logado
    if usuario_id is not None:
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = usuario_id
            sessao["perfil"] = perfil
            sessao["nome"] = nome

    return cliente
