from flask import Blueprint, jsonify, request, session

from models.log_model import buscar_logs
from models.log_model import contar_logs
from models.log_model import buscar_acoes
from validacoes import converter_data


log_bp = Blueprint("log", __name__)

# registros por pagina na tela de auditoria
POR_PAGINA = 20


def somente_coordenador():
    if not session.get("usuario_id"):
        return jsonify({"erro": "Usuario nao autenticado"}), 401

    if session.get("perfil") != "coordenador":
        return jsonify({"erro": "Acesso permitido apenas para coordenador"}), 403

    return None


@log_bp.route("/logs", methods=["GET"])
def listar_logs():

    bloqueio = somente_coordenador()
    if bloqueio:
        return bloqueio

    data_inicio = request.args.get("data_inicio") or None
    data_fim = request.args.get("data_fim") or None

    for valor in (data_inicio, data_fim):
        if valor and not converter_data(valor):
            return jsonify({"erro": "Data invalida no filtro"}), 400

    if data_inicio and data_fim and data_inicio > data_fim:
        return jsonify({"erro": "A data inicial deve ser antes da data final"}), 400

    filtros = {
        "acao": (request.args.get("acao") or "").strip() or None,
        "usuario": (request.args.get("usuario") or "").strip()[:100] or None,
        "texto": (request.args.get("texto") or "").strip()[:100] or None,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
    }

    try:
        pagina = max(1, int(request.args.get("pagina", 1)))
    except ValueError:
        pagina = 1

    total = contar_logs(**filtros)
    paginas = max(1, -(-total // POR_PAGINA))
    pagina = min(pagina, paginas)

    logs = buscar_logs(limite=POR_PAGINA, deslocamento=(pagina - 1) * POR_PAGINA, **filtros)

    return jsonify({
        "logs": logs,
        "total": total,
        "pagina": pagina,
        "paginas": paginas,
    }), 200


@log_bp.route("/logs/acoes", methods=["GET"])
def listar_acoes():

    bloqueio = somente_coordenador()
    if bloqueio:
        return bloqueio

    return jsonify(buscar_acoes()), 200
