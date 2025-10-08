"""
Test de conexión a Firestore en producción
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("🔍 Verificando configuración...")
print(f"   FIRESTORE_PROJECT_ID: {os.getenv('FIRESTORE_PROJECT_ID')}")
print(f"   GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
print(f"   Archivo existe: {os.path.exists(os.getenv('GOOGLE_APPLICATION_CREDENTIALS', ''))}")

print("\n🚀 Conectando a Firestore...")

try:
    from app.firestore_client import get_firestore_client
    
    # Obtener cliente
    db = get_firestore_client()
    
    # Test: Crear un documento de prueba
    print("\n✅ Conexión exitosa!")
    print(f"   Cliente: {db}")
    print(f"   Project: {db.project}")
    
    # Test de escritura/lectura
    print("\n📝 Probando escritura...")
    test_ref = db.collection('_test').document('connection_test')
    test_ref.set({'test': 'success', 'timestamp': 'now'})
    print("   ✅ Escritura exitosa")
    
    print("\n�� Probando lectura...")
    doc = test_ref.get()
    if doc.exists:
        print(f"   ✅ Lectura exitosa: {doc.to_dict()}")
    
    print("\n🗑️  Limpiando...")
    test_ref.delete()
    print("   ✅ Documento de prueba eliminado")
    
    print("\n" + "="*60)
    print("✅ FIRESTORE FUNCIONANDO PERFECTAMENTE")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nVerifica:")
    print("1. Que el archivo credentials/service-account.json existe")
    print("2. Que el Project ID en .env es correcto (qtsisa)")
    print("3. Que Firestore está habilitado en Google Cloud Console")
