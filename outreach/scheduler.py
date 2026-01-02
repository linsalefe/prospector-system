# outreach/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database.database import SessionLocal
from database.crud import LeadCRUD
from .whatsapp import ZAPIClient
from .message_generator import MessageGenerator
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class OutreachScheduler:
    def __init__(self, zapi_client: ZAPIClient):
        self.scheduler = BackgroundScheduler()
        self.zapi = zapi_client
        
    def iniciar(self):
        """Inicia scheduler com jobs"""
        
        # Job 1: Enviar mensagens para novos leads (3x por dia)
        self.scheduler.add_job(
            self.enviar_primeiras_mensagens,
            CronTrigger(hour='9,14,17', minute=0),  # 9h, 14h, 17h
            id='enviar_primeiras_mensagens',
            name='Enviar primeiras mensagens',
            replace_existing=True
        )
        
        # Job 2: Follow-ups (1x por dia)
        self.scheduler.add_job(
            self.enviar_followups,
            CronTrigger(hour=10, minute=30),  # 10:30
            id='enviar_followups',
            name='Enviar follow-ups',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("✅ Scheduler iniciado")
    
    def enviar_primeiras_mensagens(self):
        """Envia primeiras mensagens para leads novos"""
        
        logger.info("📤 Iniciando envio de primeiras mensagens...")
        
        db = SessionLocal()
        try:
            # Busca leads prontos para contato (max 20 por vez)
            leads = LeadCRUD.listar_para_contato(db, limite=20)
            
            enviados = 0
            
            for lead in leads:
                # Verifica se número existe no WhatsApp
                if not self.zapi.verificar_numero(lead.telefone):
                    logger.warning(f"⚠️ {lead.nome}: número não tem WhatsApp")
                    continue
                
                # Gera mensagem personalizada
                mensagem = MessageGenerator.gerar_primeira_mensagem({
                    'nome': lead.nome,
                    'cidade': lead.cidade,
                    'contato_nome': lead.contato_nome
                })
                
                # Envia
                sucesso = self.zapi.enviar_mensagem(lead.telefone, mensagem)
                
                if sucesso:
                    # Atualiza database
                    LeadCRUD.atualizar_status(db, lead.id, 'contatado')
                    lead.data_primeiro_contato = datetime.utcnow()
                    lead.proximo_followup = datetime.utcnow() + timedelta(days=3)
                    
                    LeadCRUD.adicionar_mensagem(
                        db, 
                        lead.id, 
                        'enviada', 
                        mensagem
                    )
                    
                    enviados += 1
                    logger.info(f"  ✅ {lead.nome}")
                    
                    # Delay entre mensagens (evita ban)
                    import time
                    time.sleep(5)
                else:
                    logger.error(f"  ❌ {lead.nome}: falha no envio")
            
            logger.info(f"📤 {enviados} mensagens enviadas")
            
        finally:
            db.close()
    
    def enviar_followups(self):
        """Envia follow-ups para leads que não responderam"""
        
        logger.info("📤 Iniciando follow-ups...")
        
        db = SessionLocal()
        try:
            # Busca leads para follow-up
            leads = LeadCRUD.listar_para_followup(db)
            
            enviados = 0
            
            for lead in leads:
                # Conta quantas mensagens já enviamos
                num_tentativas = len([m for m in lead.mensagens if m.direcao == 'enviada'])
                
                # Máximo 3 tentativas
                if num_tentativas >= 3:
                    LeadCRUD.atualizar_status(db, lead.id, 'desqualificado')
                    continue
                
                # Gera follow-up
                mensagem = MessageGenerator.gerar_followup({
                    'nome': lead.nome,
                    'cidade': lead.cidade,
                    'contato_nome': lead.contato_nome
                }, numero_tentativa=num_tentativas)
                
                # Envia
                sucesso = self.zapi.enviar_mensagem(lead.telefone, mensagem)
                
                if sucesso:
                    lead.proximo_followup = datetime.utcnow() + timedelta(days=5)
                    LeadCRUD.adicionar_mensagem(db, lead.id, 'enviada', mensagem)
                    enviados += 1
                    logger.info(f"  ✅ {lead.nome} (tentativa {num_tentativas + 1})")
                    
                    import time
                    time.sleep(5)
            
            logger.info(f"📤 {enviados} follow-ups enviados")
            
        finally:
            db.close()
    
    def parar(self):
        """Para scheduler"""
        self.scheduler.shutdown()
        logger.info("⏹️ Scheduler parado")