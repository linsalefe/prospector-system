# test_api_debug.py
import requests
import json

print("🔍 Testando APIs de CNPJ disponíveis...")
print("=" * 50)

# API 1: BrasilAPI
print("\n1. Testando BrasilAPI...")
try:
    # Busca por CNPJ específico de teste
    url = "https://brasilapi.com.br/api/cnpj/v1/27865757000102"  # CNPJ exemplo
    response = requests.get(url, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("✅ BrasilAPI funcionando!")
        print(f"Razão Social: {data.get('razao_social')}")
        print(f"CNAE: {data.get('cnae_fiscal')}")
except Exception as e:
    print(f"❌ Erro: {e}")

# API 2: ReceitaWS
print("\n2. Testando ReceitaWS...")
try:
    url = "https://www.receitaws.com.br/v1/cnpj/27865757000102"
    response = requests.get(url, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("✅ ReceitaWS funcionando!")
        print(f"Nome: {data.get('nome')}")
        print(f"CNAE: {data.get('atividade_principal')}")
except Exception as e:
    print(f"❌ Erro: {e}")

# API 3: Minha Receita (alternativa)
print("\n3. Testando Minha Receita...")
try:
    url = "https://minhareceita.org/27865757000102"
    response = requests.get(url, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Minha Receita funcionando!")
except Exception as e:
    print(f"❌ Erro: {e}")

print("\n" + "=" * 50)