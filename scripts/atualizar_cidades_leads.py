# scripts/atualizar_cidades_leads.py
import sys
sys.path.append('.')

import sqlite3
from pathlib import Path
from database.database import SessionLocal
from database.models import Lead

print("🗺️ Atualizando cidades dos leads...\n")

# Conecta nos dois bancos
cnpj_db = sqlite3.connect(Path("data/cnpj.db"))
prospector_db = SessionLocal()

# Busca todos os leads
leads = prospector_db.query(Lead).all()

print(f"📊 {len(leads)} leads encontrados\n")

atualizados = 0
nao_encontrados = 0

for lead in leads:
    if not lead.cidade or len(lead.cidade) > 10:  # Já tem nome ou inválido
        continue
    
    # Busca nome da cidade no banco CNPJ
    cur = cnpj_db.cursor()
    cur.execute("""
        SELECT nome FROM municipios 
        WHERE codigo_ibge = ?
    """, (lead.cidade,))
    
    result = cur.fetchone()
    
    if result:
        nome_cidade = result[0]
        lead.cidade = nome_cidade
        atualizados += 1
        
        if atualizados % 1000 == 0:
            print(f"  ✅ {atualizados:,} cidades atualizadas...")
            prospector_db.commit()
    else:
        nao_encontrados += 1

prospector_db.commit()
prospector_db.close()
cnpj_db.close()

print(f"\n✅ Atualização concluída!")
print(f"   Atualizados: {atualizados:,}")
print(f"   Não encontrados: {nao_encontrados:,}")