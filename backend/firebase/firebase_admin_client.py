import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_firebase_app = None
_firestore_db = None

def get_firebase_app():
    """Inicializa e retorna o aplicativo Firebase Admin de forma singleton."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    import firebase_admin
    from firebase_admin import credentials
    from backend.config import FIREBASE_CREDENTIALS_PATH

    if os.path.exists(FIREBASE_CREDENTIALS_PATH):
        try:
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin inicializado com credencial de serviço: %s", FIREBASE_CREDENTIALS_PATH)
        except Exception as e:
            logger.error("Falha ao inicializar Firebase com credencial: %s", e)
            _firebase_app = None
    else:
        # Tenta inicializar com Application Default Credentials ou sem parâmetros se já inicializado
        try:
            _firebase_app = firebase_admin.get_app()
        except ValueError:
            logger.warning(
                "Arquivo de credenciais do Firebase não encontrado em %s. "
                "Operando em modo local/desenvolvimento.",
                FIREBASE_CREDENTIALS_PATH
            )
            _firebase_app = None

    return _firebase_app


def get_firestore_client():
    """Retorna o cliente do Firestore se o Firebase estiver configurado."""
    global _firestore_db
    if _firestore_db is not None:
        return _firestore_db

    app = get_firebase_app()
    if app is None:
        return None

    try:
        from firebase_admin import firestore
        _firestore_db = firestore.client(app=app)
        return _firestore_db
    except Exception as e:
        logger.error("Erro ao obter cliente Firestore: %s", e)
        return None
