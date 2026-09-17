from flask import Blueprint, jsonify, request
from backend.database.db_factory import get_repository
from backend.services.auth_service import require_auth

afastamentos_bp = Blueprint("afastamentos", __name__)

MOTIVOS_PERMITIDOS = ["Folga", "Falta", "Licença médica", "Demanda interna"]

@afastamentos_bp.route("/api/afastamentos", methods=["GET"])
@require_auth(["ADMIN", "OPERACIONAL"])
def listar_afastamentos():
    repo = get_repository()
    afastamentos = repo.listar_afastamentos_ativos()
    return jsonify(afastamentos), 200

@afastamentos_bp.route("/api/afastamentos", methods=["POST"])
@require_auth(["ADMIN", "OPERACIONAL"])
def registrar_afastamento():
    dados = request.get_json() or {}
    colaborador_id = dados.get("colaborador_id")
    motivo = dados.get("motivo")
    data_inicio = dados.get("data_inicio")
    data_fim_prevista = dados.get("data_fim_prevista")

    if not colaborador_id or not motivo or not data_inicio:
        return jsonify({"error": "Campos 'colaborador_id', 'motivo' e 'data_inicio' são obrigatórios"}), 400

    if motivo not in MOTIVOS_PERMITIDOS:
        return jsonify({"error": f"Motivo inválido. Opções aceitas: {', '.join(MOTIVOS_PERMITIDOS)}"}), 400

    try:
        repo = get_repository()
        novo_id = repo.registrar_afastamento(colaborador_id, motivo, data_inicio, data_fim_prevista)
        return jsonify({"id": novo_id, "message": "Afastamento registrado com sucesso"}), 201
    except Exception as e:
        return jsonify({"error": f"Erro ao registrar afastamento: {str(e)}"}), 400

@afastamentos_bp.route("/api/afastamentos/<int:afastamento_id>/retorno", methods=["POST"])
@require_auth(["ADMIN", "OPERACIONAL"])
def registrar_retorno(afastamento_id):
    dados = request.get_json() or {}
    colaborador_id = dados.get("colaborador_id")
    data_retorno = dados.get("data_retorno")

    if not colaborador_id or not data_retorno:
        return jsonify({"error": "Campos 'colaborador_id' e 'data_retorno' são obrigatórios"}), 400

    try:
        repo = get_repository()
        repo.registrar_retorno(afastamento_id, colaborador_id, data_retorno)
        return jsonify({"afastamento_id": afastamento_id, "message": "Retorno registrado com sucesso"}), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao registrar retorno: {str(e)}"}), 400
