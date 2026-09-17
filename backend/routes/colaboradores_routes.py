from flask import Blueprint, jsonify, request
from backend.database.db_factory import get_repository
from backend.services.auth_service import require_auth

colaboradores_bp = Blueprint("colaboradores", __name__)

@colaboradores_bp.route("/api/colaboradores", methods=["GET"])
@require_auth(["ADMIN", "OPERACIONAL"])
def listar_colaboradores():
    repo = get_repository()
    colaboradores = repo.listar_colaboradores()
    return jsonify(colaboradores), 200

@colaboradores_bp.route("/api/colaboradores", methods=["POST"])
@require_auth(["ADMIN"])
def criar_colaborador():
    dados = request.get_json() or {}
    nome = dados.get("nome")
    funcao = dados.get("funcao")

    if not nome or not funcao:
        return jsonify({"error": "Campos 'nome' e 'funcao' são obrigatórios"}), 400

    try:
        repo = get_repository()
        novo_id = repo.adicionar_colaborador(nome, funcao)
        return jsonify({"id": novo_id, "nome": nome, "funcao": funcao}), 201
    except Exception as e:
        return jsonify({"error": f"Não foi possível cadastrar colaborador: {str(e)}"}), 409

@colaboradores_bp.route("/api/colaboradores/<int:colaborador_id>", methods=["PUT", "DELETE"])
@require_auth(["ADMIN"])
def editar_ou_excluir_colaborador(colaborador_id):
    repo = get_repository()
    if request.method == "DELETE":
        try:
            if not repo.excluir_colaborador(colaborador_id):
                return jsonify({"error": "Colaborador não encontrado"}), 404
            return jsonify({"message": "Colaborador excluído com sucesso"}), 200
        except Exception as e:
            return jsonify({"error": f"Colaborador possui vínculos ativos ou erro: {str(e)}"}), 409

    dados = request.get_json() or {}
    nome = dados.get("nome")
    funcao = dados.get("funcao")
    status = dados.get("status")

    if not nome or funcao not in ("motorista", "ajudante"):
        return jsonify({"error": "'nome' e uma função válida são obrigatórios"}), 400
    if status is not None and status not in ("disponivel", "em_rota", "afastado", "reserva"):
        return jsonify({"error": "Status inválido"}), 400

    try:
        if not repo.atualizar_colaborador(colaborador_id, nome, funcao, status):
            return jsonify({"error": "Colaborador não encontrado"}), 404
        return jsonify({"message": "Colaborador atualizado com sucesso"}), 200
    except Exception as e:
        return jsonify({"error": f"Não foi possível atualizar colaborador: {str(e)}"}), 409

@colaboradores_bp.route("/api/colaboradores/disponiveis/<funcao>", methods=["GET"])
@require_auth(["ADMIN", "OPERACIONAL"])
def listar_disponiveis(funcao):
    if funcao not in ["motorista", "ajudante"]:
        return jsonify({"error": "Função deve ser 'motorista' ou 'ajudante'"}), 400
    repo = get_repository()
    disponiveis = repo.listar_disponiveis(funcao)
    return jsonify(disponiveis), 200

@colaboradores_bp.route("/api/colaboradores/<int:colaborador_id>/historico", methods=["GET"])
@require_auth(["ADMIN", "OPERACIONAL"])
def historico_colaborador(colaborador_id):
    try:
        repo = get_repository()
        dados = repo.obter_historico_colaborador(colaborador_id)
        return jsonify(dados), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@colaboradores_bp.route("/api/colaboradores/reserva", methods=["GET"])
@require_auth(["ADMIN", "OPERACIONAL"])
def listar_reservas():
    repo = get_repository()
    reservas = repo.listar_colaboradores_reserva()
    return jsonify(reservas), 200

@colaboradores_bp.route("/api/colaboradores/<int:colaborador_id>/remover-reserva", methods=["POST"])
@require_auth(["ADMIN", "OPERACIONAL"])
def remover_reserva(colaborador_id):
    try:
        repo = get_repository()
        repo.remover_reserva(colaborador_id)
        return jsonify({"message": "Colaborador disponibilizado com sucesso"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Erro ao remover reserva: {str(e)}"}), 400
