from flask import Blueprint, jsonify
from backend.database.db_factory import get_repository
from backend.services.auth_service import require_auth

auditoria_bp = Blueprint("auditoria", __name__)

@auditoria_bp.route("/api/historico", methods=["GET"])
@require_auth(["ADMIN", "OPERACIONAL"])
def listar_historico():
    repo = get_repository()
    historico = repo.listar_historico()
    return jsonify(historico), 200

@auditoria_bp.route("/api/indicadores", methods=["GET"])
@require_auth(["ADMIN", "OPERACIONAL"])
def obter_indicadores():
    repo = get_repository()
    indicadores = repo.obter_indicadores()
    return jsonify(indicadores), 200

@auditoria_bp.route("/api/lotes-importacao", methods=["GET"])
@require_auth(["ADMIN", "OPERACIONAL"])
def listar_lotes_importacao():
    repo = get_repository()
    lotes = repo.listar_lotes_importacao()
    return jsonify(lotes), 200
