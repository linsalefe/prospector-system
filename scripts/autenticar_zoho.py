# scripts/autenticar_zoho.py
import sys
sys.path.append('.')

from crm.zoho_crm import ZohoCRM
from dotenv import load_dotenv

load_dotenv()

zoho = ZohoCRM()

print("🔐 Autenticação Zoho CRM\n")
print("1. Acesse esta URL no navegador:")
print(f"\n{zoho.get_auth_url()}\n")
print("2. Autorize o aplicativo")
print("3. Copie o 'code' da URL de retorno")
print("4. Cole aqui:\n")

code = input("Code: ").strip()

if zoho.generate_tokens(code):
    print("\n✅ Autenticado com sucesso!")
    print("Tokens salvos em: data/zoho_tokens.json")
else:
    print("\n❌ Erro na autenticação")