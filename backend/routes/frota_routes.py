from flask import Blueprint, jsonify, request
from backend.database.db_factory import get_repository
from backend.services.auth_service import require_auth

frota_bp = Blueprint("frota", __name__)

@frota_bp.route("/api/frota", methods=["GET"])
@require_auth(["ADMIN", "OPERACIONAL"])
def listar_frota():
    repo = get_repository()
    frota = repo.listar_frota()
    return jsonify(frota), 200

@frota_bp.route("/api/frota", methods=["POST"])
@require_auth(["ADMIN"])
def criar_frota():
    dados = request.get_json() or {}
    numero_frota = dados.get("numero_frota")
    placa = dados.get("placa")

    if not numero_frota or not placa:
        return jsonify({"error": "Campos 'numero_frota' e 'placa' são obrigatórios"}), 400

    try:
        repo = get_repository()
        novo_id = repo.adicionar_frota(numero_frota, placa)
        return jsonify({"id": novo_id, "numero_frota": numero_frota, "placa": placa}), 201
    except Exception as e:
        return jsonify({"error": f"Erro ao adicionar frota: {str(e)}"}), 400

@frota_bp.route("/api/frota/<int:frota_id>", methods=["PUT", "DELETE"])
@require_auth(["ADMIN"])
def editar_ou_excluir_frota(frota_id):
    repo = get_repository()
    if request.method == "DELETE":
        try:
            if not repo.excluir_frota(frota_id):
                return jsonify({"error": "Frota não encontrada"}), 404
            return jsonify({"message": "Frota excluída com sucesso"}), 200
        except Exception as e:
            return jsonify({"error": f"Frota possui escalas relacionadas: {str(e)}"}), 409

    dados = request.get_json() or {}
    numero_frota = dados.get("numero_frota")
    placa = dados.get("placa")
    if not numero_frota or not placa:
        return jsonify({"error": "'numero_frota' e 'placa' são obrigatórios"}), 400
    try:
        if not repo.atualizar_frota(frota_id, numero_frota, placa):
            return jsonify({"error": "Frota não encontrada"}), 404
        return jsonify({"message": "Frota atualizada com sucesso"}), 200
    except Exception as e:
        return jsonify({"error": f"Não foi possível atualizar frota: {str(e)}"}), 409

@frota_bp.route("/api/frotas/status", methods=["GET"])
@require_auth(["ADMIN", "OPERACIONAL"])
def frotas_status():
    repo = get_repository()
    frotas = repo.listar_frotas_com_status()
    return jsonify(frotas), 200

@frota_bp.route("/api/frotas/disponiveis", methods=["GET"])
@require_auth(["ADMIN", "OPERACIONAL"])
def frotas_disponiveis():
    repo = get_repository()
    todas = repo.listar_frotas_com_status()
    disponiveis = [f for f in todas if f["status_frota"] == "livre"]
    return jsonify(disponiveis), 200

@frota_bp.route("/api/frotas/<int:frota_id>/historico", methods=["GET"])
@require_auth(["ADMIN", "OPERACIONAL"])
def historico_frota(frota_id):
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    repo = get_repository()
    resultado = repo.obter_historico_frota(
        frota_id=frota_id,
        data_inicio=data_inicio,
        data_fim=data_fim
    )
    if resultado is None:
        return jsonify({"erro": "Frota não encontrada"}), 404
    return jsonify(resultado), 200
