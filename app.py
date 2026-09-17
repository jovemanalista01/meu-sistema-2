"""
Ponto de compatibilidade do LogiScale.
Redireciona para a nova arquitetura modular em backend.app.
Garante que 'python app.py', 'python run.py' e 'iniciar_agora.bat' continuem funcionando.
"""

from backend.app import app, create_app

if __name__ == "__main__":
    from backend.config import PORT, HOST, DEBUG
    print("=" * 60)
    print("  Iniciando LogiScale Backend...")
    print(f"  Acesse: http://localhost:{PORT}")
    print("=" * 60)
    app.run(host=HOST, port=PORT, debug=DEBUG)