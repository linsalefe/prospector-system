# test_educacao.py
from dotenv import load_dotenv
from scrapers.educacao_search import EducacaoSearcher
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)

print("🎓 Testando busca de Instituições de Ensino...")
print("=" * 50)

# Testa Campina Grande
leads = EducacaoSearcher.buscar_por_cnae('Campina Grande', 'PB', limite=10)

print(f"\n✅ {len(leads)} instituições encontradas!\n")

for lead in leads[:5]:
    print(f"Nome: {lead['nome']}")
    print(f"Fantasia: {lead['fantasia']}")
    print(f"CNPJ: {lead['cnpj']}")
    print(f"CNAE: {lead['cnae']}")
    print(f"Telefone: {lead['telefone']}")
    print(f"Email: {lead['email']}")
    print(f"Cidade: {lead['cidade']}")
    print("-" * 40)