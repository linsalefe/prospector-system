# scripts/setup_db.py
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.database import init_db
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup():
    """Cria todas as tabelas do banco de dados"""
    
    logger.info("🔧 Inicializando banco de dados...")
    
    try:
        init_db()
        logger.info("✅ Banco de dados criado com sucesso!")
        logger.info(f"📍 Localização: {Config.DATABASE_URL}")
    except Exception as e:
        logger.error(f"❌ Erro ao criar banco: {e}")
        return False
    
    return True

if __name__ == "__main__":
    setup()