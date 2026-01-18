# scripts/exportar_educacao_csv_v2.py
import sqlite3
from pathlib import Path
import csv

print("📚 Exportando FACULDADES, ESCOLAS e CURSOS...\n")

conn = sqlite3.connect('data/cnpj.db')
cur = conn.cursor()

# FILTRO SIMPLIFICADO: Apenas faculdades, escolas, cursos, idiomas
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
ORDER BY es.uf, m.nome
"""

print("🔍 Buscando no banco...\n")
cur.execute(query)
leads = cur.fetchall()

print(f"✅ {len(leads):,} instituições encontradas\n")

# Salva CSV
output = Path('data/educacao_faculdades_escolas_cursos.csv')
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
print(f"   Total: {len(leads):,}")
print(f"   Com telefone: {com_telefone:,} ({com_telefone/len(leads)*100:.1f}%)")
print(f"   Com email: {com_email:,} ({com_email/len(leads)*100:.1f}%)")

# Mostra distribuição por UF
import pandas as pd
df = pd.read_csv(output)
print(f"\n📍 Top 10 Estados:")
print(df['UF'].value_counts().head(10))

print(f"\n💰 Potencial de receita (R$ 2/lead): R$ {com_telefone * 2:,}")

print(f"\n💡 Para importar no Google Sheets:")
print(f"   1. Abra: https://sheets.google.com")
print(f"   2. Arquivo → Importar → Upload")
print(f"   3. Selecione: {output.name}")