# scripts/importar_educacao_zoho_v3.py
import sys
sys.path.append('.')

from crm.zoho_crm import ZohoCRM
from dotenv import load_dotenv
import time
import json
from pathlib import Path
import sqlite3

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

print("📚 Importando APENAS INSTITUIÇÕES DE ENSINO para Zoho CRM\n")

zoho = ZohoCRM()
conn = sqlite3.connect('data/cnpj.db')
cur = conn.cursor()

# FILTRO RESTRITO: APENAS palavras relacionadas a ENSINO
query = """
SELECT 
    e.razao_social,
    e.cnpj_basico,
    es.ddd_1,
    es.telefone_1,
    es.email,
    m.nome as cidade,
    es.uf
FROM empresas e
JOIN estabelecimentos es ON e.cnpj_basico = es.cnpj_basico
LEFT JOIN municipios m ON es.municipio = m.codigo_ibge
WHERE (
    e.razao_social LIKE '%FACULDADE%' OR
    e.razao_social LIKE '%UNIVERSIDADE%' OR
    e.razao_social LIKE '%CENTRO UNIVERSITARIO%' OR
    (e.razao_social LIKE '%ESCOLA%' AND e.razao_social NOT LIKE '%INSTITUTO%') OR
    (e.razao_social LIKE '%COLEGIO%' AND e.razao_social NOT LIKE '%INSTITUTO%') OR
    e.razao_social LIKE '%POLO EAD%' OR
    e.razao_social LIKE '%POLO EDUCACIONAL%' OR
    e.razao_social LIKE '%POLO UNIVERSITARIO%' OR
    e.razao_social LIKE '%ENSINO SUPERIOR%' OR
    e.razao_social LIKE '%EDUCACAO SUPERIOR%' OR
    e.razao_social LIKE '%UNOPAR%' OR
    e.razao_social LIKE '%ANHANGUERA%' OR
    e.razao_social LIKE '%ESTACIO%' OR
    e.razao_social LIKE '%UNICESUMAR%' OR
    e.razao_social LIKE '%PITAGORAS%'
)
AND es.cnpj_ordem = '0001'
AND es.ddd_1 IS NOT NULL 
AND es.telefone_1 IS NOT NULL
AND LENGTH(es.ddd_1) >= 2
AND LENGTH(es.telefone_1) >= 8
ORDER BY es.uf, m.nome
LIMIT 10000
"""

print("🔍 Buscando APENAS instituições de ENSINO...\n")
cur.execute(query)
leads = cur.fetchall()

print(f"✅ {len(leads):,} instituições de ENSINO encontradas\n")

ja_importados = carregar_progresso()
print(f"✅ {len(ja_importados):,} já importadas\n")

importados_hoje = 0
erros = 0
contador = 0

for row in leads:
    contador += 1
    
    razao, cnpj, ddd, tel, email, cidade, uf = row
    id_temp = f"{cnpj}_{uf}"
    
    if id_temp in ja_importados:
        continue
    
    if importados_hoje >= LIMITE_DIARIO:
        print(f"\n⚠️ Limite diário atingido ({LIMITE_DIARIO})")
        break
    
    telefone = f"55{ddd}{tel}"
    nome_display = razao[:40] + "..." if len(razao) > 40 else razao
    
    print(f"[{contador}/{len(leads)}] {uf} | {nome_display}", end=" | ")
    
    lead_data = {
        'nome': razao,
        'contato_nome': 'Coordenador',
        'telefone': telefone,
        'email': email if email else None,
        'cidade': cidade or uf,
        'estado': uf,
        'score': 8 if email else 6
    }
    
    try:
        lead_id = zoho.criar_lead(lead_data)
        
        if lead_id:
            print("✅")
            importados_hoje += 1
            ja_importados.add(id_temp)
            
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
conn.close()

print(f"\n✅ Importação concluída!")
print(f"   Hoje: {importados_hoje}")
print(f"   Erros: {erros}")
print(f"   Total: {len(ja_importados):,}")