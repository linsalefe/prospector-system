# scripts/extrair_imobiliarias.py
import sqlite3
from pathlib import Path
import csv

DB = Path("data/cnpj.db")
OUTPUT = Path("data/imobiliarias_brasil.csv")

print("🏢 Extraindo TODAS as imobiliárias do Brasil...\n")

conn = sqlite3.connect(DB.as_posix())
cur = conn.cursor()

# Busca TODAS as imobiliárias com JOIN na tabela de municípios
cur.execute("""
    SELECT 
        e.razao_social,
        e.cnpj_basico,
        es.ddd_1,
        es.telefone_1,
        es.ddd_2,
        es.telefone_2,
        es.email,
        COALESCE(m.nome, es.municipio) as municipio,
        es.uf
    FROM empresas e
    JOIN estabelecimentos es ON e.cnpj_basico = es.cnpj_basico
    LEFT JOIN municipios m ON es.municipio = m.codigo_ibge
    WHERE e.razao_social LIKE '%IMOBILI%'
    AND es.cnpj_ordem = '0001'
    ORDER BY es.uf, municipio
""")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Razão Social', 'CNPJ', 'Telefone 1', 'Telefone 2', 'Email', 'Cidade', 'UF'])
    
    total = 0
    com_telefone = 0
    
    for row in cur:
        razao, cnpj, ddd1, tel1, ddd2, tel2, email, municipio, uf = row
        
        # Formata telefones
        telefone1 = f"55{ddd1}{tel1}" if (ddd1 and tel1) else ""
        telefone2 = f"55{ddd2}{tel2}" if (ddd2 and tel2) else ""
        
        writer.writerow([razao, cnpj, telefone1, telefone2, email, municipio, uf])
        
        total += 1
        if telefone1 or telefone2:
            com_telefone += 1
        
        if total % 1000 == 0:
            print(f"  Processadas: {total:,} | Com telefone: {com_telefone:,}")

conn.close()

print(f"\n✅ Extração concluída!")
print(f"   Total: {total:,} imobiliárias")
print(f"   Com telefone: {com_telefone:,} ({com_telefone/total*100:.1f}%)")
print(f"   Arquivo: {OUTPUT.absolute()}")