from flask import Blueprint, jsonify, session
from models.log_model import buscar_logs


log_bp = Blueprint("log", __name__)


@log_bp.route("/logs", methods=["GET"])
def listar_logs():

    if not session.get("usuario_id"):
        return jsonify({"erro": "Usuario nao autenticado"}), 401

    if session.get("perfil") != "coordenador":
        return jsonify({"erro": "Acesso permitido apenas para coordenador"}), 403

    logs = buscar_logs()

    return jsonify(logs), 200