# scripts/importar_nordeste_para_zoho.py
import sys
sys.path.append('.')

from crm.zoho_crm import ZohoCRM
from database.database import SessionLocal
from database.models import Lead
from dotenv import load_dotenv
import time
import json
from pathlib import Path

load_dotenv()

# Estados do Nordeste (ORDEM DE PRIORIDADE)
NORDESTE = ['PB', 'PE', 'RN', 'AL', 'SE', 'BA', 'CE', 'PI', 'MA']

PROGRESSO_FILE = Path('data/progresso_importacao.json')
LIMITE_DIARIO = 1000

def carregar_progresso():
    """Carrega leads já importados"""
    if PROGRESSO_FILE.exists():
        with open(PROGRESSO_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def salvar_progresso(importados):
    """Salva leads importados"""
    PROGRESSO_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESSO_FILE, 'w') as f:
        json.dump(list(importados), f)

print("📤 Importando leads do NORDESTE para Zoho CRM\n")
print(f"🎯 Prioridade: {' → '.join(NORDESTE)}")
print(f"📊 Limite diário: {LIMITE_DIARIO} leads\n")

zoho = ZohoCRM()
db = SessionLocal()

# Carrega progresso anterior
ja_importados = carregar_progresso()
print(f"✅ {len(ja_importados):,} leads já importados anteriormente\n")

# Busca leads por ordem de prioridade dos estados
from sqlalchemy import case

# Cria ordenação customizada por estado
order_case = case(
    {estado: i for i, estado in enumerate(NORDESTE)},
    value=Lead.estado
)

leads = db.query(Lead).filter(
    Lead.estado.in_(NORDESTE),
    Lead.telefone.isnot(None),
    ~Lead.id.in_(ja_importados)
).order_by(
    order_case,
    Lead.score.desc()
).limit(LIMITE_DIARIO).all()

print(f"📊 {len(leads)} leads para importar hoje\n")

if len(leads) == 0:
    print("✅ Todos os leads do Nordeste já foram importados!")
    db.close()
    exit()

# Mostra distribuição por estado
from collections import Counter
distribuicao = Counter([l.estado for l in leads])
print("📍 Distribuição por estado:")
for estado in NORDESTE:
    if estado in distribuicao:
        print(f"   {estado}: {distribuicao[estado]} leads")
print()

importados_hoje = 0
erros = 0

for i, lead in enumerate(leads, 1):
    nome_display = lead.nome[:40] + "..." if len(lead.nome) > 40 else lead.nome
    
    print(f"[{i}/{len(leads)}] {lead.estado} | {nome_display}", end=" | ")
    
    lead_data = {
        'nome': lead.nome,
        'contato_nome': lead.contato_nome or 'Proprietário',
        'telefone': lead.telefone,
        'email': lead.email,
        'cidade': lead.cidade,
        'estado': lead.estado,
        'score': lead.score
    }
    
    try:
        lead_id = zoho.criar_lead(lead_data)
        
        if lead_id:
            print("✅")
            importados_hoje += 1
            ja_importados.add(lead.id)
            
            if importados_hoje % 10 == 0:
                salvar_progresso(ja_importados)
        else:
            print("❌")
            erros += 1
    
    except Exception as e:
        print(f"⚠️ Erro: {str(e)[:50]}")
        erros += 1
        time.sleep(5)  # Aguarda 5s antes de continuar
    
    time.sleep(1)

salvar_progresso(ja_importados)
db.close()

print(f"\n✅ Importação de hoje concluída!")
print(f"   Importados hoje: {importados_hoje}")
print(f"   Erros: {erros}")
print(f"   Total acumulado: {len(ja_importados):,}")
print(f"\n💡 Execute novamente amanhã para continuar!")
print(f"   Acesse: https://crm.zoho.com/crm/tab/Leads")