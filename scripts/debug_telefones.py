# scripts/debug_telefones.py
import sqlite3
from pathlib import Path

DB = Path("data/cnpj.db")

conn = sqlite3.connect(DB.as_posix())
cur = conn.cursor()

# Busca com mais detalhes
cur.execute("""
    SELECT e.razao_social, e.cnpj_basico, 
           es.ddd_1, es.telefone_1, es.ddd_2, es.telefone_2,
           LENGTH(es.telefone_1) as len1,
           LENGTH(es.telefone_2) as len2
    FROM empresas e
    JOIN estabelecimentos es ON e.cnpj_basico = es.cnpj_basico
    WHERE e.razao_social LIKE '%IMOBILI%'
    AND es.cnpj_ordem = '0001'
    LIMIT 30
""")

rows = cur.fetchall()

print("\n🔍 DEBUG - Estrutura dos telefones:\n")
print("=" * 100)

for razao, cnpj, ddd1, tel1, ddd2, tel2, len1, len2 in rows:
    print(f"📋 {razao[:50]}")
    print(f"   CNPJ: {cnpj}")
    print(f"   DDD1: [{ddd1}] Tel1: [{tel1}] (len: {len1})")
    print(f"   DDD2: [{ddd2}] Tel2: [{tel2}] (len: {len2})")
    print()

conn.close()