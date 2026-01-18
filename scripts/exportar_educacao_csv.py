# scripts/exportar_educacao_csv.py
import sqlite3
from pathlib import Path
import csv

print("📚 Exportando INSTITUIÇÕES DE ENSINO para CSV...\n")

conn = sqlite3.connect('data/cnpj.db')
cur = conn.cursor()

# FILTRO: APENAS instituições de ENSINO (sem institutos diversos)
query = """
SELECT 
    e.razao_social,
    e.cnpj_basico,
    es.ddd_1,
    es.telefone_1,
    es.ddd_2,
    es.telefone_2,
    es.email,
    m.nome as cidade,
    es.uf
FROM empresas e
JOIN estabelecimentos es ON e.cnpj_basico = es.cnpj_basico
LEFT JOIN municipios m ON es.municipio = m.codigo_ibge
WHERE (
    e.razao_social LIKE '%FACULDADE%' OR
    e.razao_social LIKE '%UNIVERSIDADE%' OR
    e.razao_social LIKE '%CENTRO UNIVERSITARIO%' OR
    (e.razao_social LIKE '%ESCOLA%' AND e.razao_social NOT LIKE '%INSTITUTO%') OR
    (e.razao_social LIKE '%COLEGIO%' AND e.razao_social NOT LIKE '%INSTITUTO%') OR
    e.razao_social LIKE '%POLO EAD%' OR
    e.razao_social LIKE '%POLO EDUCACIONAL%' OR
    e.razao_social LIKE '%POLO UNIVERSITARIO%' OR
    e.razao_social LIKE '%ENSINO SUPERIOR%' OR
    e.razao_social LIKE '%EDUCACAO SUPERIOR%' OR
    e.razao_social LIKE '%UNOPAR%' OR
    e.razao_social LIKE '%ANHANGUERA%' OR
    e.razao_social LIKE '%ESTACIO%' OR
    e.razao_social LIKE '%UNICESUMAR%' OR
    e.razao_social LIKE '%PITAGORAS%'
)
AND es.cnpj_ordem = '0001'
AND (
    (es.ddd_1 IS NOT NULL AND es.telefone_1 IS NOT NULL AND LENGTH(es.ddd_1) >= 2 AND LENGTH(es.telefone_1) >= 8) OR
    (es.ddd_2 IS NOT NULL AND es.telefone_2 IS NOT NULL AND LENGTH(es.ddd_2) >= 2 AND LENGTH(es.telefone_2) >= 8)
)
ORDER BY es.uf, m.nome
"""

print("🔍 Buscando no banco...\n")
cur.execute(query)
leads = cur.fetchall()

print(f"✅ {len(leads):,} instituições encontradas\n")

# Salva CSV
output = Path('data/instituicoes_ensino_completo.csv')
output.parent.mkdir(parents=True, exist_ok=True)

with open(output, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow([
        'Razão Social', 
        'CNPJ', 
        'Telefone 1', 
        'Telefone 2', 
        'Email', 
        'Cidade', 
        'UF'
    ])
    
    for row in leads:
        razao, cnpj, ddd1, tel1, ddd2, tel2, email, cidade, uf = row
        
        telefone1 = f"55{ddd1}{tel1}" if (ddd1 and tel1) else ""
        telefone2 = f"55{ddd2}{tel2}" if (ddd2 and tel2) else ""
        
        writer.writerow([
            razao,
            cnpj,
            telefone1,
            telefone2,
            email or "",
            cidade or uf,
            uf
        ])

conn.close()

print(f"✅ CSV salvo em: {output.absolute()}")
print(f"\n📊 Estatísticas:")
print(f"   Total: {len(leads):,}")

# Mostra distribuição por UF
import pandas as pd
df = pd.read_csv(output)
print(f"\n📍 Top 10 Estados:")
print(df['UF'].value_counts().head(10))

print(f"\n💡 Para importar no Google Sheets:")
print(f"   1. Abra: https://sheets.google.com")
print(f"   2. Arquivo → Importar → Upload")
print(f"   3. Selecione: {output.name}")