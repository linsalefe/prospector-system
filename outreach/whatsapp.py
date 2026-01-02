# outreach/whatsapp.py
import requests
from typing import Optional
import time

class ZAPIClient:
    def __init__(self, instance_id: str, token: str):
        self.instance_id = instance_id
        self.token = token
        self.base_url = f"https://api.z-api.io/instances/{instance_id}/token/{token}"
    
    def enviar_mensagem(self, telefone: str, mensagem: str) -> bool:
        """Envia mensagem de texto"""
        
        url = f"{self.base_url}/send-text"
        
        payload = {
            "phone": telefone,
            "message": mensagem
        }
        
        try:
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                return True
            else:
                print(f"❌ Erro ao enviar para {telefone}: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Exceção ao enviar: {e}")
            return False
    
    def verificar_numero(self, telefone: str) -> bool:
        """Verifica se número está no WhatsApp"""
        
        url = f"{self.base_url}/phone-exists/{telefone}"
        
        try:
            response = requests.get(url)
            data = response.json()
            return data.get('exists', False)
        except:
            return False