# scripts/importar_leads_para_zoho.py
import sys
sys.path.append('.')

from crm.zoho_crm import ZohoCRM
from database.database import SessionLocal
from database.models import Lead
from dotenv import load_dotenv
import time

load_dotenv()

print("📤 Importando leads para Zoho CRM...\n")

zoho = ZohoCRM()
db = SessionLocal()

# Busca leads com telefone e score >= 7
leads = db.query(Lead).filter(
    Lead.telefone.isnot(None),
    Lead.score >= 7
).order_by(Lead.score.desc()).limit(100).all()

print(f"📊 {len(leads)} leads encontrados (score ≥ 7, com telefone)\n")
print("Importando primeiros 100 leads...\n")

importados = 0
erros = 0

for lead in leads:
    print(f"[{importados + erros + 1}/{len(leads)}] {lead.nome[:50]}...", end=" ")
    
    lead_data = {
        'nome': lead.nome,
        'contato_nome': lead.contato_nome,
        'telefone': lead.telefone,
        'email': lead.email,
        'cidade': lead.cidade,
        'estado': lead.estado,
        'score': lead.score
    }
    
    lead_id = zoho.criar_lead(lead_data)
    
    if lead_id:
        print("✅")
        importados += 1
    else:
        print("❌")
        erros += 1
    
    # Rate limit: 1 request por segundo
    time.sleep(1)

db.close()

print(f"\n✅ Importação concluída!")
print(f"   Importados: {importados}")
print(f"   Erros: {erros}")
print(f"\nAcesse: https://crm.zoho.com/crm/tab/Leads")