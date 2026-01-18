# scripts/preparar_educacao_para_crm.py
import pandas as pd
from pathlib import Path

print("📚 Preparando instituições de ensino para CRM...\n")

# Lê CSV completo
df = pd.read_csv('data/educacao_brasil.csv')

# Filtra polos/centros EAD
termos = [
    'POLO', 'NUCLEO', 'CENTRO DE', 'CENTRO EDUCACIONAL',
    'EAD', 'ENSINO A DISTANCIA', 'EDUCACAO A DISTANCIA',
    'ENSINO SUPERIOR', 'EDUCACAO SUPERIOR',
    'UNOPAR', 'ANHANGUERA', 'PITAGORAS', 'ESTACIO', 'UNICESUMAR',
    'FACULDADE', 'UNIVERSIDADE', 'INSTITUTO'
]

pattern = '|'.join(termos)
instituicoes = df[df['Razão Social'].str.contains(pattern, case=False, na=False)]

# Filtra só com telefone
com_telefone = instituicoes[instituicoes['Telefone 1'] != ''].copy()

# Adiciona score (baseado em ter email)
com_telefone['score'] = com_telefone.apply(
    lambda row: 8 if row['Email'] != '' else 6,
    axis=1
)

print(f"✅ {len(com_telefone):,} instituições selecionadas\n")

# Salva
output = Path('data/educacao_para_crm.csv')
com_telefone.to_csv(output, index=False)

print(f"📊 Distribuição:")
print(com_telefone['UF'].value_counts().head(10))
print(f"\n💾 Salvo em: {output.absolute()}")