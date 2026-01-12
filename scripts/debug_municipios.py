# scripts/debug_municipios.py
import sqlite3
from pathlib import Path

cnpj_db = sqlite3.connect(Path("data/cnpj.db"))
cur = cnpj_db.cursor()

# Pega 10 municípios do Acre (AC)
cur.execute("""
    SELECT codigo_ibge, nome, uf 
    FROM municipios 
    WHERE uf = 'AC'
    LIMIT 10
""")

print("🗺️ Municípios do Acre no banco:\n")
for codigo, nome, uf in cur.fetchall():
    print(f"  {codigo} - {nome}/{uf}")

cnpj_db.close()