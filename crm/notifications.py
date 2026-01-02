# crm/notifications.py
import requests
from typing import Dict

class TelegramNotifier:
    def __init__(self, token: str, chat_id: str = None):
        self.token = token
        self.chat_id = chat_id  # Seu chat_id pessoal
        self.base_url = f"https://api.telegram.org/bot{token}"
    
    def enviar_mensagem(self, mensagem: str, chat_id: str = None):
        """Envia mensagem Telegram"""
        
        chat = chat_id or self.chat_id
        
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat,
            "text": mensagem,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, json=payload)
            return response.status_code == 200
        except:
            return False
    
    def notificar_reuniao_agendada(self, lead, mensagem_agent: str):
        """Notifica que reunião foi agendada"""
        
        texto = f"""🎯 <b>NOVA REUNIÃO AGENDADA!</b>

📋 <b>Lead:</b> {lead.nome}
👤 <b>Contato:</b> {lead.contato_nome or 'N/A'}
📍 <b>Cidade:</b> {lead.cidade}
📱 <b>Tel:</b> {lead.telefone}
⭐ <b>Score:</b> {lead.score}/10

💬 <b>Última mensagem do agent:</b>
{mensagem_agent}

<i>Finalize o agendamento e envie o link do Meet!</i>"""
        
        self.enviar_mensagem(texto)
    
    def notificar_novo_lead_quente(self, lead):
        """Notifica sobre lead muito qualificado"""
        
        texto = f"""🔥 <b>LEAD QUENTE!</b>

📋 {lead.nome}
⭐ Score: {lead.score}/10
📍 {lead.cidade}

Enviar primeira mensagem agora?"""
        
        self.enviar_mensagem(texto)