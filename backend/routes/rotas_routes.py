from flask import Blueprint, jsonify, request
from backend.database.db_factory import get_repository
from backend.services.auth_service import require_auth

rotas_bp = Blueprint("rotas", __name__)

@rotas_bp.route("/api/rotas", methods=["GET"])
@require_auth(["ADMIN", "OPERACIONAL"])
def listar_rotas():
    repo = get_repository()
    rotas = repo.listar_rotas()
    return jsonify(rotas), 200

@rotas_bp.route("/api/rotas", methods=["POST"])
@require_auth(["ADMIN"])
def criar_rota():
    dados = request.get_json() or {}
    nome_rota = dados.get("nome_rota")
    duracao_media_dias = dados.get("duracao_media_dias")

    if not nome_rota:
        return jsonify({"error": "Campo 'nome_rota' é obrigatório"}), 400

    try:
        duracao_media_dias = int(duracao_media_dias) if duracao_media_dias else None
        repo = get_repository()
        novo_id = repo.adicionar_rota(nome_rota, duracao_media_dias)
        return jsonify({"id": novo_id, "nome_rota": nome_rota, "duracao_media_dias": duracao_media_dias}), 201
    except Exception as e:
        return jsonify({"error": f"Erro ao adicionar rota: {str(e)}"}), 400

@rotas_bp.route("/api/rotas/<int:rota_id>", methods=["PUT", "DELETE"])
@require_auth(["ADMIN"])
def editar_ou_excluir_rota(rota_id):
    repo = get_repository()
    if request.method == "DELETE":
        try:
            if not repo.excluir_rota(rota_id):
                return jsonify({"error": "Rota não encontrada"}), 404
            return jsonify({"message": "Rota excluída com sucesso"}), 200
        except Exception as e:
            return jsonify({"error": f"Rota possui escalas relacionadas: {str(e)}"}), 409

    dados = request.get_json() or {}
    nome_rota = dados.get("nome_rota")
    if not nome_rota:
        return jsonify({"error": "'nome_rota' é obrigatório"}), 400
    try:
        duracao = dados.get("duracao_media_dias")
        duracao = int(duracao) if duracao is not None and duracao != "" else None
        if not repo.atualizar_rota(rota_id, nome_rota, duracao):
            return jsonify({"error": "Rota não encontrada"}), 404
        return jsonify({"message": "Rota atualizada com sucesso"}), 200
    except Exception as e:
        return jsonify({"error": f"Não foi possível atualizar rota: {str(e)}"}), 400
