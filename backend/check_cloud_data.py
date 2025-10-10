from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.database import SessionLocal, engine

print(f"🔍 Conectado a: {engine.url}")
print(f"   Dialecto: {engine.dialect.name}")

db = SessionLocal()

# Contar scan_records
scan_count = db.execute(text("SELECT COUNT(*) FROM scan_records")).scalar()
print(f"\n✅ Total scan_records: {scan_count}")

# Ver últimos 5
result = db.execute(text("""
    SELECT id, sap_article, quantity, scanned_at 
    FROM scan_records 
    ORDER BY scanned_at DESC 
    LIMIT 5
""")).fetchall()

if result:
    print("\n📋 Últimos 5 escaneos:")
    for row in result:
        print(f"  ID: {row[0]}, SAP: {row[1]}, Qty: {row[2]}, Fecha: {row[3]}")
else:
    print("\n  (No hay escaneos aún)")

db.close()
