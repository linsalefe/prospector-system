# scripts/testar_zoho.py
import sys
sys.path.append('.')

from crm.zoho_crm import ZohoCRM
from dotenv import load_dotenv

load_dotenv()

print("🧪 Testando criação de lead no Zoho CRM...\n")

zoho = ZohoCRM()

# Lead de teste
lead_teste = {
    'nome': 'Imobiliária Teste SP',
    'contato_nome': 'João',
    'telefone': '5511999887766',
    'email': 'contato@imobteste.com.br',
    'cidade': 'São Paulo',
    'estado': 'SP',
    'score': 8
}

print("📋 Criando lead:")
print(f"   Empresa: {lead_teste['nome']}")
print(f"   Contato: {lead_teste['contato_nome']}")
print(f"   Telefone: {lead_teste['telefone']}")
print(f"   Email: {lead_teste['email']}")
print(f"   Cidade: {lead_teste['cidade']}/{lead_teste['estado']}")
print(f"   Score: {lead_teste['score']}/10\n")

lead_id = zoho.criar_lead(lead_teste)

if lead_id:
    print(f"✅ Lead criado com sucesso!")
    print(f"   ID: {lead_id}")
    print(f"   Acesse: https://crm.zoho.com/crm/org20101280338/tab/Leads/{lead_id}")
else:
    print("❌ Erro ao criar lead")