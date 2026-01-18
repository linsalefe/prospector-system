# scripts/importar_educacao_para_zoho.py
import sys
sys.path.append('.')

from crm.zoho_crm import ZohoCRM
import pandas as pd
from dotenv import load_dotenv
import time
import json
from pathlib import Path

load_dotenv()

PROGRESSO_FILE = Path('data/progresso_educacao.json')
LIMITE_DIARIO = 1000

def carregar_progresso():
    if PROGRESSO_FILE.exists():
        with open(PROGRESSO_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def salvar_progresso(importados):
    PROGRESSO_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESSO_FILE, 'w') as f:
        json.dump(list(importados), f)

print("📚 Importando INSTITUIÇÕES DE ENSINO para Zoho CRM\n")

zoho = ZohoCRM()

# Lê CSV preparado
df = pd.read_csv('data/educacao_para_crm.csv')

print(f"📊 {len(df):,} instituições no arquivo")

# Limpa e valida telefones
df['tel_limpo'] = df['Telefone 1'].astype(str).str.strip()
df = df[df['tel_limpo'].str.len() >= 12]
df = df[df['tel_limpo'].str.isdigit()]

print(f"✅ {len(df):,} com telefones válidos")
print(f"📍 Estados: {', '.join(df['UF'].value_counts().head(5).index.tolist())}\n")

# Carrega progresso
ja_importados = carregar_progresso()
print(f"✅ {len(ja_importados):,} já importadas anteriormente\n")

# Filtra não importadas
df['id_temp'] = df['CNPJ'].astype(str) + '_' + df['UF']
df_pendentes = df[~df['id_temp'].isin(ja_importados)].head(LIMITE_DIARIO)

print(f"🎯 {len(df_pendentes)} para importar hoje\n")

if len(df_pendentes) == 0:
    print("✅ Todas as instituições já foram importadas!")
    exit()

importados_hoje = 0
erros = 0

for i, row in df_pendentes.iterrows():
    nome_display = row['Razão Social'][:40] + "..." if len(row['Razão Social']) > 40 else row['Razão Social']
    
    print(f"[{importados_hoje + erros + 1}/{len(df_pendentes)}] {row['UF']} | {nome_display}", end=" | ")
    
    lead_data = {
        'nome': row['Razão Social'],
        'contato_nome': 'Coordenador',
        'telefone': row['tel_limpo'],
        'email': row['Email'] if row['Email'] != '' else None,
        'cidade': row['Cidade'],
        'estado': row['UF'],
        'score': int(row['score'])
    }
    
    try:
        lead_id = zoho.criar_lead(lead_data)
        
        if lead_id:
            print("✅")
            importados_hoje += 1
            ja_importados.add(row['id_temp'])
            
            if importados_hoje % 10 == 0:
                salvar_progresso(ja_importados)
        else:
            print("❌")
            erros += 1
    
    except Exception as e:
        print(f"⚠️ Erro: {str(e)[:50]}")
        erros += 1
        time.sleep(5)
    
    time.sleep(1)

salvar_progresso(ja_importados)

print(f"\n✅ Importação concluída!")
print(f"   Hoje: {importados_hoje}")
print(f"   Erros: {erros}")
print(f"   Total: {len(ja_importados):,}")
print(f"\n💡 Execute novamente amanhã para continuar!")
print(f"   Acesse: https://crm.zoho.com/crm/tab/Leads")