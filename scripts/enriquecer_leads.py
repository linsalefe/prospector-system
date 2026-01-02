# scripts/enriquecer_leads.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.database import SessionLocal
from database.models import Lead
from scrapers.cnpj_enrichment import CNPJEnricher
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def enriquecer_todos():
    """
    Enriquece todos os leads do banco com dados do CNPJ
    """
    
    db = SessionLocal()
    
    try:
        # Busca leads sem CNPJ ou sem contato_nome
        leads = db.query(Lead).filter(
            (Lead.contato_nome == None) | (Lead.email == None)
        ).limit(50).all()  # Começa com 50 para testar
        
        logger.info(f"🔍 Enriquecendo {len(leads)} leads...")
        
        enriquecidos = 0
        
        for idx, lead in enumerate(leads, 1):
            logger.info(f"\n[{idx}/{len(leads)}] {lead.nome}")
            
            try:
                # Enriquece
                dados = CNPJEnricher.enriquecer_lead(lead.nome, lead.cidade, lead.website)
                
                if dados:
                    # Atualiza lead
                    lead.email = dados.get('email') or lead.email
                    lead.contato_nome = dados.get('contato_nome') or lead.contato_nome
                    lead.contato_cargo = dados.get('contato_cargo') or lead.contato_cargo
                    
                    # Telefone do CNPJ pode ser melhor que do Google Maps
                    if dados.get('telefone'):
                        lead.telefone = dados['telefone']
                    
                    db.commit()
                    
                    enriquecidos += 1
                    
                    logger.info(f"  ✅ Enriquecido!")
                    logger.info(f"     Contato: {lead.contato_nome}")
                    logger.info(f"     Cargo: {lead.contato_cargo}")
                    logger.info(f"     Email: {lead.email}")
                    logger.info(f"     Sócios: {len(dados.get('socios', []))}")
                else:
                    logger.warning(f"  ⚠️ CNPJ não encontrado")
                
                # Rate limit: 3 req/min na ReceitaWS
                time.sleep(20)
                
            except Exception as e:
                logger.error(f"  ❌ Erro: {e}")
                continue
        
        logger.info(f"\n✅ Enriquecimento concluído!")
        logger.info(f"   {enriquecidos}/{len(leads)} leads enriquecidos")
        
    finally:
        db.close()

if __name__ == "__main__":
    enriquecer_todos()