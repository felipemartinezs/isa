"""
Aplica los archivos migrados al proyecto
"""
import os
import shutil

source_dir = "migrated_files"
print("🚀 APLICANDO MIGRACIÓN A FIRESTORE")
print("=" * 60)

# Copiar archivos generados a sus ubicaciones finales
files_to_apply = [
    ("auth.py", "app/auth.py"),
    ("auth_router.py", "app/routers/auth_router.py"),
    ("articles_router.py", "app/routers/articles_router.py"),
    ("main.py", "app/main.py"),
]

print("📋 Archivos a aplicar:")
for src, dest in files_to_apply:
    src_path = os.path.join(source_dir, src)
    if os.path.exists(src_path):
        print(f"   ✅ {src} → {dest}")
    else:
        print(f"   ❌ {src} NO ENCONTRADO")

print("\n⚠️  ADVERTENCIA:")
print("   Esto REEMPLAZARÁ los archivos originales")
print("   (Ya están respaldados en backup_sqlalchemy_*/)")
print("\n" + "=" * 60)

response = input("¿Continuar? (s/n): ")

if response.lower() != 's':
    print("❌ Migración cancelada")
    exit(0)

print("\n📦 Aplicando cambios...")
for src, dest in files_to_apply:
    src_path = os.path.join(source_dir, src)
    if os.path.exists(src_path):
        shutil.copy2(src_path, dest)
        print(f"   ✅ {dest} actualizado")

print("\n" + "=" * 60)
print("✅ MIGRACIÓN APLICADA EXITOSAMENTE")
print("=" * 60)
print("\n📋 Archivos actualizados:")
print("   ✅ app/auth.py")
print("   ✅ app/routers/auth_router.py")
print("   ✅ app/routers/articles_router.py")
print("   ✅ app/main.py")
print("\n🎯 SIGUIENTE PASO:")
print("\n1. Revisar cambios con: git diff")
print("2. Probar backend con: uvicorn app.main:app --reload")
print("3. Si funciona: git add . && git commit -m 'feat: migrate to Firestore'")
print("4. Si falla: git restore .")
