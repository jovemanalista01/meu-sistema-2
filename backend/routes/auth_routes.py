from flask import Blueprint, jsonify, request, g
from backend.services.auth_service import require_auth
from backend.database.db_factory import get_repository

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/api/auth/me", methods=["GET"])
@require_auth(["ADMIN", "OPERACIONAL"])
def obter_usuario_atual():
    """Retorna dados do usuário autenticado no contexto da requisição."""
    current_user = getattr(g, "current_user", {
        "uid": "dev-user",
        "email": "operacional@logiscale.com",
        "role": "ADMIN"
    })
    return jsonify({
        "status": "autenticado",
        "usuario": current_user
    }), 200

@auth_bp.route("/api/auth/usuarios", methods=["GET"])
@require_auth(["ADMIN"])
def listar_usuarios():
    """Lista usuários cadastrados (somente ADMIN)."""
    repo = get_repository()
    usuarios = []
    if hasattr(repo, "db") and repo.db is not None:
        docs = repo.db.collection("usuarios").stream()
        usuarios = [dict(d.to_dict(), uid=d.id) for d in docs]
    else:
        # Modo SQLite / local fallback
        usuarios = [
            {"uid": "admin-1", "email": "admin@logiscale.com", "nome": "Administrador", "role": "ADMIN"},
            {"uid": "oper-1", "email": "operacional@logiscale.com", "nome": "Operador", "role": "OPERACIONAL"}
        ]
    return jsonify(usuarios), 200
