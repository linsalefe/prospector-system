# outreach/message_generator.py
from typing import Dict
import random

class MessageGenerator:
    
    TEMPLATES_PRIMEIRA_MENSAGEM = [
        """Olá {contato_nome}, tudo bem?

Sou Álefe da FinClip. Vi que a {empresa} está em {cidade}.

Trabalho com imobiliárias que perdem leads por demora no atendimento.

Criamos um agente de IA que responde WhatsApp em 30s e qualifica automaticamente.

A Imobiliária Silva aumentou 40% de conversão em 2 meses.

Posso te mostrar em 15min como funciona?""",

        """Oi {contato_nome}! 

Álefe aqui, da FinClip 👋

Ajudo imobiliárias como a {empresa} a não perderem mais leads por demora no atendimento.

Nosso agente de IA responde 24/7 e qualifica leads automaticamente.

Vale 15min pra eu te mostrar? Clientes estão aumentando conversão em 40-60%.""",

        """E aí {contato_nome},

Sou o Álefe. Desenvolvo IA pra imobiliárias.

Vocês da {empresa} usam algum sistema pra atender leads do WhatsApp automaticamente?

Criamos um agente que responde em segundos, qualifica e agenda visita sozinho.

Resultado: +40% conversão pros nossos clientes.

Te mostro em 15min?"""
    ]
    
    TEMPLATES_FOLLOWUP = [
        """Oi {contato_nome}!

Enviei uma mensagem sobre automação de leads há alguns dias.

Vi que {empresa} anuncia em [Portal]. Vocês devem receber bastante lead, né?

Nosso sistema ajuda a não perder nenhum. Vale uma conversa rápida?""",

        """Oi {contato_nome}, tudo bem?

Seguindo o contato anterior: fiz um case study rápido de como a Imobiliária Silva aumentou conversão em 45%.

Posso te enviar? São só 2 páginas.

Se fizer sentido, a gente agenda 15min depois."""
    ]
    
    @classmethod
    def gerar_primeira_mensagem(cls, lead_data: Dict) -> str:
        """Gera primeira mensagem personalizada"""
        
        template = random.choice(cls.TEMPLATES_PRIMEIRA_MENSAGEM)
        
        contato = lead_data.get('contato_nome', lead_data['nome'].split()[0])
        
        return template.format(
            contato_nome=contato,
            empresa=lead_data['nome'],
            cidade=lead_data['cidade']
        )
    
    @classmethod
    def gerar_followup(cls, lead_data: Dict, numero_tentativa: int = 1) -> str:
        """Gera mensagem de follow-up"""
        
        template = random.choice(cls.TEMPLATES_FOLLOWUP)
        
        contato = lead_data.get('contato_nome', lead_data['nome'].split()[0])
        
        return template.format(
            contato_nome=contato,
            empresa=lead_data['nome']
        )