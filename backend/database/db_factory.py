import logging
from backend.config import DB_BACKEND, SQLITE_DB_PATH
from backend.database.repository_interface import DataRepository
from backend.database.sqlite_repository import SQLiteRepository

logger = logging.getLogger(__name__)

_active_repo: DataRepository = None

def get_repository() -> DataRepository:
    """Retorna a instância do repositório ativo de acordo com a configuração."""
    global _active_repo
    if _active_repo is not None:
        return _active_repo

    if DB_BACKEND == "firestore":
        try:
            from backend.database.firestore_repository import FirestoreRepository
            _active_repo = FirestoreRepository()
            logger.info("Repositório configurado para: Firebase Firestore")
            return _active_repo
        except Exception as e:
            logger.warning("Falha ao inicializar Firestore (%s). Usando fallback para SQLite.", e)

    _active_repo = SQLiteRepository(db_path=SQLITE_DB_PATH)
    logger.info("Repositório configurado para: SQLite (%s)", SQLITE_DB_PATH)
    return _active_repo
