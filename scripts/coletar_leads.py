# scripts/coletar_leads.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from config import Config
from database.database import SessionLocal
from database.crud import LeadCRUD
from scrapers.google_maps import ImobiliariasScraper
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def coletar():
    """Coleta leads e salva no banco"""
    
    logger.info("🔍 Iniciando coleta de leads...")
    
    # Scraper
    scraper = ImobiliariasScraper(
        google_api_key=Config.GOOGLE_MAPS_API_KEY,
        hunter_api_key=Config.HUNTER_API_KEY
    )
    
    # Cidades target
    cidades = [
        'Campina Grande PB',
        'João Pessoa PB',
    ]
    
    # Busca (10 por cidade para teste)
    df = scraper.buscar_imobiliarias(cidades, limite_por_cidade=10)
    
    # Salva no banco
    db = SessionLocal()
    try:
        novos = 0
        duplicados = 0
        
        for _, row in df.iterrows():
            # Verifica se já existe
            existing = LeadCRUD.buscar_lead(db, row['id'])
            if not existing:
                LeadCRUD.criar_lead(db, row.to_dict())
                novos += 1
                logger.info(f"  ➕ {row['nome']}")
            else:
                duplicados += 1
        
        logger.info(f"✅ Coleta concluída!")
        logger.info(f"   Novos: {novos}")
        logger.info(f"   Duplicados: {duplicados}")
        
    finally:
        db.close()

if __name__ == "__main__":
    coletar()