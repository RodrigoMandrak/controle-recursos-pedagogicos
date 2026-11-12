import os

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from controllers.feriado_controller import feriado_bp
from controllers.atividade_controller import atividade_bp
from controllers.alocacao_controller import alocacao_bp
from controllers.usuario_controller import usuario_bp
from controllers.recuperacao_controller import recuperacao_bp
from controllers.log_controller import log_bp
from controllers.dashboard_controller import dashboard_bp
from controllers.recurso_controller import recurso_bp
from controllers.solicitacao_controller import solicitacao_bp
from banco import atualizar_estrutura

load_dotenv()


app = Flask(__name__)

# chave usada pela sessao do usuario
app.secret_key = os.getenv("SECRET_KEY")

# permite que o front envie e receba a sessao
CORS(app, supports_credentials=True)


@app.route("/")
def inicio():
    return "Sistema de Controle de Recursos Pedagogicos"


# registra as rotas

app.register_blueprint(atividade_bp)
app.register_blueprint(alocacao_bp)
app.register_blueprint(usuario_bp)
app.register_blueprint(feriado_bp)
app.register_blueprint(recuperacao_bp)
app.register_blueprint(log_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(recurso_bp)
app.register_blueprint(solicitacao_bp)

# confere se o banco tem as colunas novas (ex.: quantidade do recurso)
try:
    atualizar_estrutura()
except Exception as erro:
    print("Nao foi possivel atualizar a estrutura do banco:", erro)

if __name__ == "__main__":
    app.run(debug=True)