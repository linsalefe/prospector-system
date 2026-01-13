# test_processar_receita.py
from dotenv import load_dotenv
from scrapers.processar_receita_federal import ProcessadorReceitaFederal
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)

print("🏢 Processando Base da Receita Federal...")
print("=" * 50)

# Caminho correto
PASTA_RECEITA = './data/receita'

df = ProcessadorReceitaFederal.processar_estabelecimentos(
    pasta_receita=PASTA_RECEITA,
    output_file='empresas_educacao_brasil.csv'
)

print("\n" + "=" * 50)
print("📊 RESUMO")
print("=" * 50)
print(f"Total: {len(df)} empresas")
print(f"\nPor UF:")
print(df['uf'].value_counts().head(10))
print(f"\nPor CNAE:")
print(df['cnae_fiscal_principal'].value_counts())