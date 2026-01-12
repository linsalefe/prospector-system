# scripts/importar_imobiliarias_para_prospector.py

import sys
sys.path.append('.')

import csv
import uuid
from pathlib import Path
from database.database import SessionLocal, init_db
from database.crud import LeadCRUD
from sqlalchemy import text

CSV_FILE = Path("data/imobiliarias_brasil.csv")

print("📥 Importando imobiliárias para o banco do Prospector...\n")

# Inicializa banco
init_db()
db = SessionLocal()

# Limpa leads antigos (opcional)
print("🗑️ Limpando leads antigos...")
db.execute(text("DELETE FROM leads"))
db.commit()

with open(CSV_FILE, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    importados = 0
    com_telefone = 0
    
    for row in reader:
        razao = row['Razão Social']
        cnpj = row['CNPJ']
        telefone1 = row['Telefone 1']
        telefone2 = row['Telefone 2']
        email = row['Email']
        cidade = row['Cidade']
        uf = row['UF']
        
        # Pega o melhor telefone
        telefone = telefone1 if telefone1 else telefone2
        
        # Score baseado em ter telefone e email
        score = 5
        if telefone:
            score += 3
            com_telefone += 1
        if email:
            score += 2
        
        # Cria lead
        lead_data = {
            'id': str(uuid.uuid4()),
            'nome': razao,
            'telefone': telefone if telefone else None,
            'email': email if email else None,
            'cidade': cidade,
            'estado': uf,
            'score': score,
            'status': 'novo'
        }
        
        try:
            LeadCRUD.criar_lead(db, lead_data)
            importados += 1
            
            if importados % 1000 == 0:
                print(f"  ✅ {importados:,} importados | Com telefone: {com_telefone:,}")
        except:
            pass  # Ignora duplicados

db.close()

print(f"\n✅ Importação concluída!")
print(f"   Total importado: {importados:,}")
print(f"   Com telefone: {com_telefone:,}")
print(f"   Abra o dashboard: streamlit run dashboard.py")