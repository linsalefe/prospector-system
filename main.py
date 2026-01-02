# main.py
import os
import logging
from dotenv import load_dotenv
from database.database import init_db, SessionLocal
from database.crud import LeadCRUD
from scrapers.google_maps import ImobiliariasScraper
from outreach.scheduler import OutreachScheduler
from outreach.whatsapp import ZAPIClient
from api.server import app
import uvicorn
from threading import Thread

# Carrega variáveis de ambiente
load_dotenv()

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('prospector.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def scraping_job():
    """Job de scraping (roda 1x por semana)"""
    logger.info("🔍 Iniciando job de scraping...")
    
    scraper = ImobiliariasScraper(
        google_api_key=os.getenv('GOOGLE_MAPS_API_KEY'),
        hunter_api_key=os.getenv('HUNTER_API_KEY')
    )
    
    cidades = [
        'Campina Grande PB',
        'João Pessoa PB',
        'Recife PE',
        'Fortaleza CE'
    ]
    
    # Scraping
    df = scraper.buscar_imobiliarias(cidades, limite_por_cidade=100)
    
    # Salva no database
    db = SessionLocal()
    try:
        novos = 0
        for _, row in df.iterrows():
            # Verifica se já existe
            existing = LeadCRUD.buscar_lead(db, row['id'])
            if not existing:
                LeadCRUD.criar_lead(db, row.to_dict())
                novos += 1
        
        logger.info(f"✅ Scraping concluído: {novos} novos leads")
    finally:
        db.close()

def iniciar_sistema():
    """Inicializa todo o sistema"""
    
    logger.info("🚀 Iniciando Prospector System...")
    
    # Inicializa database
    init_db()
    logger.info("✅ Database inicializado")
    
    # Inicializa scheduler de outreach
    zapi = ZAPIClient(
        instance_id=os.getenv('ZAPI_INSTANCE_ID'),
        token=os.getenv('ZAPI_TOKEN')
    )
    
    scheduler = OutreachScheduler(zapi)
    scheduler.iniciar()
    logger.info("✅ Scheduler iniciado")
    
    # Inicia API server em thread separada
    def run_api():
        uvicorn.run(app, host="0.0.0.0", port=8000)
    
    api_thread = Thread(target=run_api, daemon=True)
    api_thread.start()
    logger.info("✅ API server iniciado na porta 8000")
    
    logger.info("🎉 Sistema operacional!")
    
    # Mantém programa rodando
    try:
        while True:
            import time
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("⏹️ Encerrando sistema...")
        scheduler.parar()

if __name__ == "__main__":
    iniciar_sistema()