# agent/qualifier.py
import anthropic
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import json

class QualifierAgent:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        
    def processar_mensagem(
        self, 
        lead_data: Dict, 
        mensagem_usuario: str,
        historico: List[Dict]
    ) -> Tuple[str, str, bool]:
        """
        Processa mensagem e retorna:
        - resposta (str)
        - estagio (str)
        - deve_notificar_humano (bool)
        """
        
        # Monta histórico formatado
        messages = []
        for msg in historico:
            messages.append({
                "role": "user" if msg['direcao'] == 'recebida' else "assistant",
                "content": msg['conteudo']
            })
        
        # Adiciona mensagem atual
        messages.append({
            "role": "user",
            "content": mensagem_usuario
        })
        
        # System prompt
        system_prompt = self._build_system_prompt(lead_data)
        
        # Chama Claude
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            temperature=0.7,
            system=system_prompt,
            messages=messages
        )
        
        resposta = response.content[0].text
        
        # Analisa estágio e intenção
        estagio = self._analisar_estagio(mensagem_usuario, resposta)
        deve_notificar = self._deve_notificar_humano(estagio, mensagem_usuario)
        
        return resposta, estagio, deve_notificar
    
    def _build_system_prompt(self, lead_data: Dict) -> str:
        """Constrói system prompt personalizado"""
        
        return f"""Você é um agente de qualificação de leads da FinClip, especializada em soluções de IA para imobiliárias.

INFORMAÇÕES DO LEAD:
- Empresa: {lead_data['nome']}
- Cidade: {lead_data['cidade']}
- Contato: {lead_data.get('contato_nome', 'não identificado')}

SUA MISSÃO:
Qualificar este lead e agendar demonstração do produto.

PRODUTO:
Sistema de IA que automatiza atendimento no WhatsApp para imobiliárias:
- Responde leads em 30 segundos (24/7)
- Qualifica automaticamente (orçamento, prazo, perfil)
- Agenda visitas
- Integra com CRMs (Vista, Jetimob, Superlógica)
- ROI: clientes aumentam 40-60% conversão de leads

PREÇO:
- Setup: R$2.500 (one-time)
- Mensalidade: R$997 a R$1.497/mês (depende do porte)

PROCESSO DE QUALIFICAÇÃO:
1. CONFIRMAR INTERESSE (se ainda não confirmou)
   - Lead está interessado em melhorar conversão de leads?
   
2. PERGUNTAS QUALIFICADORAS (faça 1-2 por vez, não todas de uma vez):
   - Quantos leads vocês recebem por mês?
   - Qual o principal canal? (site próprio, portais, indicação)
   - Quantos corretores na equipe?
   - Usam CRM atualmente? Qual?
   - Qual % dos leads são perdidos por demora no atendimento?

3. APRESENTAR VALOR
   - Explique brevemente como resolve a dor específica deles
   - Use dados: "clientes aumentam 40-60% conversão"
   - Mencione case: "Imobiliária Silva em JP aumentou 45% em 60 dias"

4. OFERECER DEMONSTRAÇÃO
   - "Vale 15-20min para te mostrar funcionando?"
   - Ofereça 3 horários nos próximos 3 dias úteis
   - Seja específico: "Terça 10h, Quarta 15h ou Quinta 10h?"

REGRAS IMPORTANTES:
- Mensagens CURTAS (máx 200 caracteres)
- Tom profissional mas amigável
- Use emojis com moderação (1-2 por mensagem)
- Não seja insistente
- Se lead perguntar preço, seja transparente
- Se lead não tiver interesse, agradeça e encerre educadamente

OBJEÇÕES COMUNS:
- "Muito caro" → Mostre ROI: se aumentar 2 vendas/mês já paga
- "Já usamos outro sistema" → Podemos integrar
- "Preciso pensar" → Ok, posso enviar case study?
- "Não tenho tempo" → Demo de 15min só, no horário que preferir

QUANDO AGENDAR REUNIÃO:
- Lead confirmou interesse em ver demo
- Já fez pelo menos 2 perguntas qualificadoras
- Lead está respondendo rápido/engajado

Se lead aceitar reunião, confirme:
"Perfeito! Confirmando: [DIA] às [HORA], certo? Vou te enviar o link do Google Meet."

IMPORTANTE: Você NÃO marca a reunião, apenas confirma o interesse e horário. Um humano vai finalizar o agendamento."""

    def _analisar_estagio(self, msg_usuario: str, resposta_agent: str) -> str:
        """Analisa em que estágio está a conversa"""
        
        msg_lower = msg_usuario.lower()
        
        # Keywords de cada estágio
        interesse_positivo = ['sim', 'quero', 'tenho interesse', 'me interessou', 'gostaria']
        qualificacao = ['leads', 'corretores', 'crm', 'site', 'portal']
        aceite_demo = ['pode mostrar', 'vamos agendar', 'quero ver', 'demo', 'reunião']
        confirmacao = ['confirmo', 'pode ser', 'tudo certo', 'ok', 'combinado', 'perfeito']
        rejeicao = ['não tenho interesse', 'não quero', 'não preciso', 'já uso']
        
        if any(palavra in msg_lower for palavra in rejeicao):
            return 'desqualificado'
        elif any(palavra in msg_lower for palavra in confirmacao):
            return 'agendamento_confirmado'
        elif any(palavra in msg_lower for palavra in aceite_demo):
            return 'oferecendo_horarios'
        elif any(palavra in msg_lower for palavra in qualificacao):
            return 'qualificacao'
        elif any(palavra in msg_lower for palavra in interesse_positivo):
            return 'interesse_confirmado'
        else:
            return 'exploracao'
    
    def _deve_notificar_humano(self, estagio: str, msg_usuario: str) -> bool:
        """Decide se deve notificar humano"""
        
        # Notifica se reunião foi confirmada
        if estagio == 'agendamento_confirmado':
            return True
        
        # Notifica se lead fez pergunta complexa
        perguntas_complexas = ['quanto custa', 'qual garantia', 'contrato', 'cancelamento']
        if any(p in msg_usuario.lower() for p in perguntas_complexas):
            return True
        
        return False