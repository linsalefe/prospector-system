# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI (ChatGPT)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Google Maps
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    
    # Hunter.io (opcional - para buscar emails)
    HUNTER_API_KEY = os.getenv('HUNTER_API_KEY', '')
    
    # Z-API (WhatsApp)
    ZAPI_INSTANCE_ID = os.getenv('ZAPI_INSTANCE_ID')
    ZAPI_TOKEN = os.getenv('ZAPI_TOKEN')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./database/prospector.db')
    
    @classmethod
    def validar(cls):
        """Valida se as configs essenciais existem"""
        erros = []
        
        if not cls.OPENAI_API_KEY:
            erros.append("OPENAI_API_KEY não configurada")
        
        if not cls.GOOGLE_MAPS_API_KEY:
            erros.append("GOOGLE_MAPS_API_KEY não configurada")
            
        if not cls.ZAPI_INSTANCE_ID or not cls.ZAPI_TOKEN:
            erros.append("Z-API não configurada")
        
        if erros:
            raise ValueError(f"Configurações faltando:\n" + "\n".join(f"- {e}" for e in erros))
        
        return True