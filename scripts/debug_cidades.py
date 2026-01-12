# scripts/debug_cidades.py
import sys
sys.path.append('.')

from database.database import SessionLocal
from database.models import Lead
import sqlite3
from pathlib import Path

db = SessionLocal()
cnpj_db = sqlite3.connect(Path("data/cnpj.db"))

# Pega 10 leads para debug
leads = db.query(Lead).limit(10).all()

print("🔍 DEBUG - Códigos de cidade:\n")

for lead in leads:
    print(f"📋 {lead.nome[:40]}")
    print(f"   Código atual: [{lead.cidade}] (len: {len(lead.cidade) if lead.cidade else 0})")
    
    # Tenta buscar com código exato
    cur = cnpj_db.cursor()
    cur.execute("SELECT nome FROM municipios WHERE codigo_ibge = ?", (lead.cidade,))
    result1 = cur.fetchone()
    
    # Tenta buscar com código formatado (7 dígitos)
    codigo_7digitos = lead.cidade.zfill(7) if lead.cidade else None
    cur.execute("SELECT nome FROM municipios WHERE codigo_ibge = ?", (codigo_7digitos,))
    result2 = cur.fetchone()
    
    print(f"   Busca exata: {result1}")
    print(f"   Busca 7 dígitos ({codigo_7digitos}): {result2}")
    print()

db.close()
cnpj_db.close()