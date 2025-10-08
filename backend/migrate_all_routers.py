"""
Script automatizado para migrar todos los routers de SQLAlchemy a Firestore
"""
import os
import shutil
from datetime import datetime

print("🚀 Iniciando migración completa a Firestore...\n")

# Backup de archivos originales
backup_dir = f"backup_sqlalchemy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
os.makedirs(backup_dir, exist_ok=True)

files_to_backup = [
    "app/auth.py",
    "app/routers/auth_router.py",
    "app/routers/articles_router.py",
    "app/routers/bom_router.py",
    "app/routers/scan_router.py",
    "app/routers/reports_router.py",
    "app/main.py"
]

print("📦 Creando backup de archivos originales...")
for file in files_to_backup:
    if os.path.exists(file):
        shutil.copy2(file, os.path.join(backup_dir, os.path.basename(file)))
        print(f"   ✅ {file} respaldado")

print(f"\n✅ Backup completo en: {backup_dir}/\n")
print("=" * 60)
print("IMPORTANTE: Este script creará nuevos archivos migrados.")
print("Los archivos originales están respaldados en:", backup_dir)
print("=" * 60)
print("\n¿Continuar con la migración? (s/n): ", end="")

