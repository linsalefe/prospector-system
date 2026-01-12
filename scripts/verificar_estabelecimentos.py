# scripts/verificar_estabelecimentos.py
import sqlite3
from pathlib import Path

cnpj_db = sqlite3.connect(Path("data/cnpj.db"))
cur = cnpj_db.cursor()

# Pega 10 estabelecimentos do Acre
cur.execute("""
    SELECT cnpj_basico, municipio, uf
    FROM estabelecimentos
    WHERE uf = 'AC'
    LIMIT 10
""")

print("📋 Estabelecimentos do Acre:\n")
for cnpj, municipio, uf in cur.fetchall():
    print(f"  CNPJ: {cnpj} | Município: [{municipio}] | UF: {uf}")

cnpj_db.close()