from flask import Flask
from flask_cors import CORS

from controllers.atividade_controller import atividade_bp
from controllers.alocacao_controller import alocacao_bp


app = Flask(__name__)
CORS(app)


@app.route("/")
def inicio():
    return "Sistema de Controle de Recursos Pedagogicos"


# registra as rotas que ficaram separadas
app.register_blueprint(atividade_bp)
app.register_blueprint(alocacao_bp)


if __name__ == "__main__":
    app.run(debug=True)