import os
import sys

# Garante que o diretório raiz esteja no path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from backend.config import PORT, HOST, DEBUG
from backend.database.db_factory import get_repository

# Importação dos Blueprints
from backend.routes.colaboradores_routes import colaboradores_bp
from backend.routes.frota_routes import frota_bp
from backend.routes.rotas_routes import rotas_bp
from backend.routes.escalas_routes import escalas_bp
from backend.routes.afastamentos_routes import afastamentos_bp
from backend.routes.auditoria_routes import auditoria_bp
from backend.routes.importacao_routes import importacao_bp
from backend.routes.auth_routes import auth_bp

def create_app():
    """Fábrica de aplicação Flask com suporte a CORS e arquitetura modular."""
    frontend_dir = os.path.join(root_dir, "frontend")
    app = Flask(__name__, static_folder=frontend_dir, static_url_path="")

    # Habilita CORS para todas as rotas da API (permite deploy no Netlify consumindo a API)
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
        }
    })

    # Inicializa repositório de dados ativo
    get_repository()

    # Registro de Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(colaboradores_bp)
    app.register_blueprint(frota_bp)
    app.register_blueprint(rotas_bp)
    app.register_blueprint(escalas_bp)
    app.register_blueprint(afastamentos_bp)
    app.register_blueprint(auditoria_bp)
    app.register_blueprint(importacao_bp)

    # Health Check da API
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "online",
            "service": "LogiScale API",
            "version": "2.0.0"
        }), 200

    # Rota raiz para servir o frontend desacoplado em ambiente local
    @app.route("/", methods=["GET"])
    def index():
        if os.path.exists(os.path.join(frontend_dir, "index.html")):
            return send_from_directory(frontend_dir, "index.html")
        return jsonify({"message": "LogiScale API pronta. Frontend hospedado separadamente."}), 200

    # Manipuladores de erro padronizados
    @app.errorhandler(404)
    def nao_encontrado(e):
        return jsonify({"error": "Recurso não encontrado"}), 404

    @app.errorhandler(500)
    def erro_servidor(e):
        return jsonify({"error": "Erro interno no servidor"}), 500

    return app

app = create_app()

if __name__ == "__main__":
    print("=" * 60)
    print("  LogiScale API Backend v2.0")
    print(f"  Iniciando em http://{HOST}:{PORT}")
    print("=" * 60)
    app.run(host=HOST, port=PORT, debug=DEBUG)
