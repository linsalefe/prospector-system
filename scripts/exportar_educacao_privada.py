# scripts/exportar_educacao_privada.py
import sqlite3
from pathlib import Path
import csv

print("📚 Exportando APENAS INSTITUIÇÕES PRIVADAS...\n")

conn = sqlite3.connect('data/cnpj.db')
cur = conn.cursor()

# FILTRO: Apenas privadas (exclui municipal, estadual, pública)
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
    e.razao_social LIKE '%ESCOLA%' OR
    e.razao_social LIKE '%COLEGIO%' OR
    e.razao_social LIKE '%CURSO%' OR
    e.razao_social LIKE '%IDIOMA%'
)
AND es.cnpj_ordem = '0001'
AND (
    (es.ddd_1 IS NOT NULL AND es.telefone_1 IS NOT NULL AND LENGTH(es.ddd_1) >= 2 AND LENGTH(es.telefone_1) >= 8) OR
    (es.ddd_2 IS NOT NULL AND es.telefone_2 IS NOT NULL AND LENGTH(es.ddd_2) >= 2 AND LENGTH(es.telefone_2) >= 8)
)
AND e.razao_social NOT LIKE '%MUNICIPAL%'
AND e.razao_social NOT LIKE '%ESTADUAL%'
AND e.razao_social NOT LIKE '%PUBLICA%'
AND e.razao_social NOT LIKE '%E.M.%'
AND e.razao_social NOT LIKE '%E.E.%'
AND e.razao_social NOT LIKE '%EMEF%'
AND e.razao_social NOT LIKE '%EMEI%'
AND e.razao_social NOT LIKE '%EMEIF%'
AND e.razao_social NOT LIKE '%PREFEITURA%'
AND e.razao_social NOT LIKE '%GOVERNO%'
AND e.razao_social NOT LIKE '%ESTADO DO%'
AND e.razao_social NOT LIKE '%SECRETARIA%'
ORDER BY es.uf, m.nome
"""

print("🔍 Buscando instituições PRIVADAS...\n")
cur.execute(query)
leads = cur.fetchall()

print(f"✅ {len(leads):,} instituições PRIVADAS encontradas\n")

# Salva CSV
output = Path('data/educacao_privada.csv')
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
    
    com_telefone = 0
    com_email = 0
    
    for row in leads:
        razao, cnpj, ddd1, tel1, ddd2, tel2, email, cidade, uf = row
        
        telefone1 = f"55{ddd1}{tel1}" if (ddd1 and tel1) else ""
        telefone2 = f"55{ddd2}{tel2}" if (ddd2 and tel2) else ""
        
        if telefone1 or telefone2:
            com_telefone += 1
        if email:
            com_email += 1
        
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
print(f"   Total: {len(leads):,} instituições PRIVADAS")
print(f"   Com telefone: {com_telefone:,} ({com_telefone/len(leads)*100:.1f}%)")
print(f"   Com email: {com_email:,} ({com_email/len(leads)*100:.1f}%)")

import pandas as pd
df = pd.read_csv(output)
print(f"\n📍 Top 10 Estados:")
print(df['UF'].value_counts().head(10))

print(f"\n💰 Potencial de receita:")
print(f"   R$ 2/lead: R$ {com_telefone * 2:,}")
print(f"   R$ 5/lead: R$ {com_telefone * 5:,}")

print(f"\n💡 Para Google Sheets:")
print(f"   https://sheets.google.com → Importar → {output.name}")
