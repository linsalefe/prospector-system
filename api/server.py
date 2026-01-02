# api/server.py
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database.database import get_db
from database.crud import LeadCRUD
from agent.qualifier import QualifierAgent
from outreach.whatsapp import ZAPIClient
from crm.notifications import TelegramNotifier
import os
import logging

app = FastAPI(title="Prospector System API")

logger = logging.getLogger(__name__)

# Inicializa clients
agent = QualifierAgent(api_key=os.getenv('ANTHROPIC_API_KEY'))
zapi = ZAPIClient(
    instance_id=os.getenv('ZAPI_INSTANCE_ID'),
    token=os.getenv('ZAPI_TOKEN')
)
telegram = TelegramNotifier(token=os.getenv('TELEGRAM_BOT_TOKEN'))

@app.get("/")
def root():
    return {"status": "ok", "message": "Prospector System API"}

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook para receber mensagens do WhatsApp (Z-API)
    """
    
    try:
        data = await request.json()
        
        # Extrai dados da mensagem
        telefone = data.get('phone')
        mensagem = data.get('text', {}).get('message', '')
        
        if not telefone or not mensagem:
            return JSONResponse({"status": "ignored"})
        
        logger.info(f"📱 Mensagem recebida de {telefone}: {mensagem[:50]}...")
        
        # Busca lead por telefone
        lead = LeadCRUD.buscar_por_telefone(db, telefone)
        
        if not lead:
            logger.warning(f"⚠️ Lead não encontrado: {telefone}")
            return JSONResponse({"status": "lead_not_found"})
        
        # Adiciona mensagem ao histórico
        LeadCRUD.adicionar_mensagem(db, lead.id, 'recebida', mensagem)
        
        # Busca histórico completo
        historico = [
            {
                'direcao': msg.direcao,
                'conteudo': msg.conteudo
            }
            for msg in lead.mensagens[:-1]  # Exclui a mensagem atual que acabamos de adicionar
        ]
        
        # Processa com agent
        lead_data = {
            'nome': lead.nome,
            'cidade': lead.cidade,
            'contato_nome': lead.contato_nome
        }
        
        resposta, estagio, deve_notificar = agent.processar_mensagem(
            lead_data,
            mensagem,
            historico
        )
        
        # Envia resposta
        sucesso = zapi.enviar_mensagem(telefone, resposta)
        
        if sucesso:
            # Salva resposta do agent
            LeadCRUD.adicionar_mensagem(db, lead.id, 'enviada', resposta)
            
            # Atualiza estágio
            lead.estagio_conversa = estagio
            db.commit()
            
            logger.info(f"✅ Resposta enviada. Estágio: {estagio}")
            
            # Notifica humano se necessário
            if deve_notificar:
                telegram.notificar_reuniao_agendada(lead, resposta)
                logger.info("📬 Notificação enviada ao Telegram")
        
        return JSONResponse({
            "status": "success",
            "estagio": estagio
        })
        
    except Exception as e:
        logger.error(f"❌ Erro no webhook: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/stats")
def obter_stats(db: Session = Depends(get_db)):
    """Retorna estatísticas do sistema"""
    
    from sqlalchemy import func
    from database.models import Lead
    
    stats = {
        'total_leads': db.query(func.count(Lead.id)).scalar(),
        'por_status': dict(
            db.query(Lead.status, func.count(Lead.id))
            .group_by(Lead.status)
            .all()
        ),
        'score_medio': db.query(func.avg(Lead.score)).scalar(),
        'reunioes_agendadas': db.query(func.count(Lead.id))
            .filter(Lead.status == 'reuniao_agendada')
            .scalar()
    }
    
    return stats