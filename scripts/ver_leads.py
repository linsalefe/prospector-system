# scripts/ver_leads.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.database import SessionLocal
from database.models import Lead
from sqlalchemy import func

db = SessionLocal()

# Total
total = db.query(func.count(Lead.id)).scalar()
print(f"\n📊 Total de leads: {total}\n")

# Por cidade
por_cidade = db.query(Lead.cidade, func.count(Lead.id)).group_by(Lead.cidade).all()
print("Por cidade:")
for cidade, count in por_cidade:
    print(f"  {cidade}: {count}")

# Por score
por_score = db.query(Lead.score, func.count(Lead.id)).group_by(Lead.score).order_by(Lead.score.desc()).all()
print("\nPor score:")
for score, count in por_score:
    print(f"  Score {score}: {count} leads")

# Top 10 melhores leads
print("\n🏆 Top 10 melhores leads (score >= 7):")
top_leads = db.query(Lead).filter(Lead.score >= 7).order_by(Lead.score.desc()).limit(10).all()
for lead in top_leads:
    tel = lead.telefone if lead.telefone else "Sem telefone"
    print(f"  ⭐ {lead.score} - {lead.nome} ({lead.cidade}) - {tel}")

# Leads com WhatsApp
com_whatsapp = db.query(func.count(Lead.id)).filter(Lead.telefone.isnot(None)).scalar()
print(f"\n📱 Leads com WhatsApp: {com_whatsapp}")

db.close()