# test_cnae.py
from dotenv import load_dotenv
from scrapers.cnae_search import CNAESearcher
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)

print("🏢 Testando busca por CNAE...")
print("=" * 50)

# Testa Campina Grande
leads = CNAESearcher.buscar_por_cnae('Campina Grande', 'PB', limite=10)

print(f"\n✅ {len(leads)} empresas encontradas!\n")

for lead in leads[:5]:
    print(f"Nome: {lead['nome']}")
    print(f"CNPJ: {lead['cnpj']}")
    print(f"Telefone: {lead['telefone']}")
    print(f"Email: {lead['email']}")
    print("-" * 40)