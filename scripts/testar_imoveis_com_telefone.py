# scripts/testar_imoveis_com_telefone.py
import sqlite3
from pathlib import Path

DB = Path("data/cnpj.db")

conn = sqlite3.connect(DB.as_posix())
cur = conn.cursor()

# Busca imobiliárias que TÊM telefone
cur.execute("""
    SELECT e.razao_social, e.cnpj_basico, 
           es.ddd_1, es.telefone_1, es.email, es.municipio, es.uf
    FROM empresas e
    JOIN estabelecimentos es ON e.cnpj_basico = es.cnpj_basico
    WHERE e.razao_social LIKE '%IMOBILI%'
    AND es.cnpj_ordem = '0001'
    AND es.ddd_1 IS NOT NULL
    AND es.telefone_1 IS NOT NULL
    LIMIT 20
""")

rows = cur.fetchall()

print(f"\n🏢 {len(rows)} imobiliárias encontradas COM TELEFONE:\n")
print("=" * 80)

for razao, cnpj_basico, ddd, tel, email, municipio, uf in rows:
    telefone = f"55{ddd}{tel}"
    print(f"📋 {razao}")
    print(f"   CNPJ: {cnpj_basico}")
    print(f"   📱 {telefone}")
    if email:
        print(f"   📧 {email}")
    print(f"   📍 {municipio}/{uf}")
    print()

conn.close()