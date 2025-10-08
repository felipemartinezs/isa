"""
Cliente Firestore para producción en Google Cloud
"""
import os
from google.cloud import firestore
from typing import Optional, Dict, List
from functools import lru_cache
from .config import get_settings

settings = get_settings()
_firestore_client = None


def get_firestore_client() -> firestore.Client:
    """
    Singleton para el cliente Firestore en producción.
    """
    global _firestore_client
    
    if _firestore_client is not None:
        return _firestore_client
    
    # Configurar credenciales desde .env
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'credentials/service-account.json')
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    
    # Conectar a Firestore en producción
    _firestore_client = firestore.Client(project=settings.FIRESTORE_PROJECT_ID)
    print(f"☁️  Firestore conectado a producción: {settings.FIRESTORE_PROJECT_ID}")
    
    return _firestore_client


# Helper functions para operaciones comunes
def get_collection(collection_name: str):
    """Obtiene referencia a una colección"""
    db = get_firestore_client()
    return db.collection(collection_name)


def create_document(collection_name: str, data: dict) -> str:
    """
    Crea un documento con ID autogenerado.
    Retorna el ID del documento creado.
    """
    db = get_firestore_client()
    _, doc_ref = db.collection(collection_name).add(data)
    return doc_ref.id


def create_document_with_id(collection_name: str, doc_id: str, data: dict):
    """Crea un documento con ID específico"""
    db = get_firestore_client()
    db.collection(collection_name).document(doc_id).set(data)


def get_document(collection_name: str, doc_id: str) -> Optional[Dict]:
    """Obtiene un documento por ID"""
    db = get_firestore_client()
    doc = db.collection(collection_name).document(doc_id).get()
    if doc.exists:
        return {"id": doc.id, **doc.to_dict()}
    return None


def update_document(collection_name: str, doc_id: str, data: dict):
    """Actualiza un documento"""
    db = get_firestore_client()
    db.collection(collection_name).document(doc_id).update(data)


def delete_document(collection_name: str, doc_id: str):
    """Elimina un documento"""
    db = get_firestore_client()
    db.collection(collection_name).document(doc_id).delete()


def query_where(collection_name: str, field: str, operator: str, value) -> List[Dict]:
    """
    Query simple con where clause.
    Retorna lista de documentos que cumplen la condición.
    """
    db = get_firestore_client()
    docs = db.collection(collection_name).where(field, operator, value).stream()
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]


def delete_collection(collection_ref, batch_size: int = 100):
    """
    Elimina todos los documentos de una colección en batches.
    Útil para cascades manuales.
    """
    docs = collection_ref.limit(batch_size).stream()
    deleted = 0

    for doc in docs:
        doc.reference.delete()
        deleted += 1

    if deleted >= batch_size:
        return delete_collection(collection_ref, batch_size)


# Dependency para FastAPI
async def get_db():
    """
    Dependency para usar en FastAPI routers.
    Reemplaza al get_db() de SQLAlchemy.
    """
    try:
        yield get_firestore_client()
    finally:
        pass  # Firestore no requiere close()
