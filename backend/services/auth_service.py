from functools import wraps
from flask import request, jsonify, g
import logging
from backend.config import AUTH_REQUIRED
from backend.firebase.firebase_admin_client import get_firebase_app

logger = logging.getLogger(__name__)

def require_auth(roles=None):
    """
    Decorator para proteção de rotas via Firebase Authentication e RBAC.
    Permite acesso transparente em modo de desenvolvimento se AUTH_REQUIRED=False.
    """
    if roles is None:
        roles = ["ADMIN", "OPERACIONAL"]
    elif isinstance(roles, str):
        roles = [roles]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Se a autenticação estiver desativada (ex: desenvolvimento local / testes)
            if not AUTH_REQUIRED:
                g.current_user = {
                    "uid": "dev-user",
                    "email": "operacional@logiscale.com",
                    "role": "ADMIN"
                }
                return f(*args, **kwargs)

            # Verifica cabeçalho Authorization
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "Autenticação necessária. Token ausente."}), 401

            token = auth_header.split(" ", 1)[1].strip()
            app = get_firebase_app()
            if not app:
                return jsonify({"error": "Serviço de autenticação temporariamente indisponível."}), 503

            try:
                from firebase_admin import auth
                decoded_token = auth.verify_id_token(token)
                uid = decoded_token.get("uid")
                email = decoded_token.get("email", "")

                # Obtém perfil (role) do custom claim ou do Firestore
                user_role = decoded_token.get("role")
                if not user_role:
                    # Tenta consultar na coleção usuarios
                    try:
                        from backend.database.db_factory import get_repository
                        repo = get_repository()
                        if hasattr(repo, "db") and repo.db is not None:
                            user_doc = repo.db.collection("usuarios").document(uid).get()
                            if user_doc.exists:
                                user_role = user_doc.to_dict().get("role", "OPERACIONAL")
                    except Exception:
                        pass

                if not user_role:
                    user_role = "OPERACIONAL"

                g.current_user = {
                    "uid": uid,
                    "email": email,
                    "role": user_role
                }

                # Checagem de permissão RBAC
                if roles and user_role not in roles:
                    return jsonify({
                        "error": "Acesso não autorizado para o seu perfil de usuário.",
                        "perfil_atual": user_role,
                        "perfis_permitidos": roles
                    }), 403

            except Exception as e:
                logger.error("Erro ao validar token Firebase: %s", e)
                return jsonify({"error": f"Token de autenticação inválido ou expirado: {str(e)}"}), 401

            return f(*args, **kwargs)
        return decorated_function
    return decorator
