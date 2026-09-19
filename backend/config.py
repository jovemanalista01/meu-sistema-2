import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env caso exista
env_path = os.path.join(os.path.dirname(__file__), "..", "config", ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Configuração do banco de dados ('sqlite' ou 'firestore')
DB_BACKEND = os.getenv("DB_BACKEND", "sqlite").strip().lower()

# Caminho do banco SQLite
SQLITE_DB_PATH = os.getenv(
    "SQLITE_DB_PATH",
    os.path.join(BASE_DIR, "escala.db")
)

# Caminho para chave privada da conta de serviço do Firebase
FIREBASE_CREDENTIALS_PATH = os.getenv(
    "FIREBASE_CREDENTIALS_PATH",
    os.path.join(BASE_DIR, "config", "firebase_credentials.json")
)

# Controle de autenticação (se True, exige token JWT Bearer do Firebase)
AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "false").strip().lower() in ("true", "1", "yes")

# Configurações do servidor Flask
PORT = int(os.getenv("PORT", "5000"))
HOST = os.getenv("HOST", "0.0.0.0")
DEBUG = os.getenv("DEBUG", "true").strip().lower() in ("true", "1", "yes")
FIREBASE_CREDENTIALS_JSON = os.getenv("FIREBASE_CREDENTIALS_JSON", "")

if FIREBASE_CREDENTIALS_JSON and not os.path.exists(FIREBASE_CREDENTIALS_PATH):
    import json
    import tempfile
    _tmp = os.path.join(tempfile.gettempdir(), "firebase_credentials.json")
    with open(_tmp, "w") as f:
        f.write(FIREBASE_CREDENTIALS_JSON)
    FIREBASE_CREDENTIALS_PATH = _tmp