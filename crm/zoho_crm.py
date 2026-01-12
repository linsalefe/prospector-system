# crm/zoho_crm.py
import requests
import os
from datetime import datetime, timedelta
import json
from pathlib import Path

class ZohoCRM:
    def __init__(self):
        self.client_id = os.getenv('ZOHO_CLIENT_ID')
        self.client_secret = os.getenv('ZOHO_CLIENT_SECRET')
        self.redirect_uri = os.getenv('ZOHO_REDIRECT_URI')
        self.token_file = Path('data/zoho_tokens.json')
        
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        
        self._load_tokens()
    
    def _load_tokens(self):
        """Carrega tokens salvos"""
        if self.token_file.exists():
            with open(self.token_file, 'r') as f:
                data = json.load(f)
                self.access_token = data.get('access_token')
                self.refresh_token = data.get('refresh_token')
                self.token_expiry = datetime.fromisoformat(data.get('token_expiry'))
    
    def _save_tokens(self):
        """Salva tokens"""
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.token_file, 'w') as f:
            json.dump({
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'token_expiry': self.token_expiry.isoformat()
            }, f)
    
    def get_auth_url(self):
        """Retorna URL para autorização"""
        scope = "ZohoCRM.modules.ALL,ZohoCRM.settings.ALL"
        return (
            f"https://accounts.zoho.com/oauth/v2/auth?"
            f"scope={scope}&"
            f"client_id={self.client_id}&"
            f"response_type=code&"
            f"access_type=offline&"
            f"redirect_uri={self.redirect_uri}"
        )
    
    def generate_tokens(self, code):
        """Gera tokens a partir do código de autorização"""
        url = "https://accounts.zoho.com/oauth/v2/token"
        
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'code': code
        }
        
        response = requests.post(url, data=data)
        
        print(f"\n🔍 Status: {response.status_code}")
        print(f"📦 Resposta: {response.text}\n")
        
        if response.status_code == 200:
            result = response.json()
            
            if 'access_token' in result:
                self.access_token = result['access_token']
                self.refresh_token = result['refresh_token']
                self.token_expiry = datetime.now() + timedelta(seconds=result['expires_in'])
                self._save_tokens()
                return True
            else:
                print(f"❌ Erro: {result}")
                return False
        else:
            print(f"❌ Erro HTTP: {response.text}")
            return False
    
    def _refresh_access_token(self):
        """Renova access token"""
        url = "https://accounts.zoho.com/oauth/v2/token"
        
        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token
        }
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            result = response.json()
            self.access_token = result['access_token']
            self.token_expiry = datetime.now() + timedelta(seconds=result['expires_in'])
            self._save_tokens()
            return True
        return False
    
    def _ensure_valid_token(self):
        """Garante que o token está válido"""
        if not self.access_token:
            raise Exception("Não autenticado. Execute o fluxo de autenticação primeiro.")
        
        if datetime.now() >= self.token_expiry:
            self._refresh_access_token()
    
    def criar_lead(self, lead_data):
        """Cria lead no Zoho CRM"""
        self._ensure_valid_token()
    
        url = "https://www.zohoapis.com/crm/v2/Leads"
    
        headers = {
        'Authorization': f'Zoho-oauthtoken {self.access_token}',
        'Content-Type': 'application/json'
        }
    
    # Formata dados para Zoho
        zoho_lead = {
        "Company": lead_data['nome'],
        "Last_Name": lead_data.get('contato_nome', 'Proprietário'),
        "Phone": lead_data.get('telefone'),
        "City": lead_data.get('cidade'),
        "State": lead_data.get('estado'),
        "Lead_Source": "Database",
        "Lead_Status": "Not Contacted",
        "Rating": self._score_to_rating(lead_data.get('score', 5))
        }
    
        # Só adiciona email se for válido
        email = lead_data.get('email')
        if email and '@' in str(email) and len(str(email)) > 5:
            zoho_lead["Email"] = email
    
        payload = {"data": [zoho_lead]}
    
        response = requests.post(url, headers=headers, json=payload)
    
        if response.status_code in [200, 201]:
            result = response.json()
            if result['data'][0]['status'] == 'success':
                return result['data'][0]['details']['id']
    
        print(f"Erro ao criar lead: {response.text}")
        return None
    
    def _score_to_rating(self, score):
        """Converte score para rating do Zoho"""
        if score >= 8:
            return "Hot"
        elif score >= 6:
            return "Warm"
        else:
            return "Cold"
    
    def buscar_lead(self, telefone):
        """Busca lead por telefone"""
        self._ensure_valid_token()
        
        url = f"https://www.zohoapis.com/crm/v2/Leads/search?phone={telefone}"
        
        headers = {
            'Authorization': f'Zoho-oauthtoken {self.access_token}'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if 'data' in result:
                return result['data'][0]
        
        return None