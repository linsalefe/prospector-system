# scripts/criar_tabela_municipios.py
import requests
import sqlite3
from pathlib import Path

print("🗺️ Baixando tabela de municípios do IBGE...\n")

# API do IBGE com todos os municípios
url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

response = requests.get(url, timeout=30)
municipios = response.json()

print(f"✅ {len(municipios)} municípios baixados\n")

# Cria tabela no banco de CNPJs
DB = Path("data/cnpj.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Cria tabela
cur.execute("""
    CREATE TABLE IF NOT EXISTS municipios (
        codigo_ibge TEXT PRIMARY KEY,
        nome TEXT,
        uf TEXT
    )
""")

# Insere municípios
print("💾 Salvando no banco...")
salvos = 0
erros = 0

for m in municipios:
    try:
        codigo = str(m['id'])
        nome = m['nome']
        
        # Tenta pegar UF de várias formas
        if 'microrregiao' in m and m['microrregiao']:
            uf = m['microrregiao']['mesorregiao']['UF']['sigla']
        elif 'regiao-imediata' in m and m['regiao-imediata']:
            uf = m['regiao-imediata']['regiao-intermediaria']['UF']['sigla']
        else:
            # Pega da própria API (formato alternativo)
            continue
        
        cur.execute("""
            INSERT OR REPLACE INTO municipios (codigo_ibge, nome, uf)
            VALUES (?, ?, ?)
        """, (codigo, nome, uf))
        
        salvos += 1
        
    except Exception as e:
        erros += 1
        continue

conn.commit()
conn.close()

print(f"✅ {salvos} municípios salvos")
if erros > 0:
    print(f"⚠️ {erros} municípios com erro (ignorados)")