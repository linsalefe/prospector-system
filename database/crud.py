# database/crud.py
from sqlalchemy.orm import Session
from .models import Lead, Mensagem, Reuniao
from datetime import datetime, timedelta
from typing import List, Optional

class LeadCRUD:
    @staticmethod
    def criar_lead(db: Session, lead_data: dict) -> Lead:
        """Cria novo lead"""
        lead = Lead(**lead_data)
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead
    
    @staticmethod
    def buscar_lead(db: Session, lead_id: str) -> Optional[Lead]:
        """Busca lead por ID"""
        return db.query(Lead).filter(Lead.id == lead_id).first()
    
    @staticmethod
    def buscar_por_telefone(db: Session, telefone: str) -> Optional[Lead]:
        """Busca lead por telefone"""
        return db.query(Lead).filter(Lead.telefone == telefone).first()
    
    @staticmethod
    def listar_para_contato(db: Session, limite: int = 20) -> List[Lead]:
        """Lista leads prontos para contato"""
        return db.query(Lead).filter(
            Lead.status == 'novo',
            Lead.telefone.isnot(None),
            Lead.score >= 6
        ).order_by(Lead.score.desc()).limit(limite).all()
    
    @staticmethod
    def listar_para_followup(db: Session) -> List[Lead]:
        """Lista leads para follow-up"""
        hoje = datetime.utcnow()
        return db.query(Lead).filter(
            Lead.proximo_followup <= hoje,
            Lead.status.in_(['contatado', 'qualificado'])
        ).all()
    
    @staticmethod
    def atualizar_status(db: Session, lead_id: str, novo_status: str):
        """Atualiza status do lead"""
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            lead.status = novo_status
            lead.atualizado_em = datetime.utcnow()
            db.commit()
            return lead
        return None
    
    @staticmethod
    def adicionar_mensagem(db: Session, lead_id: str, direcao: str, conteudo: str) -> Mensagem:
        """Adiciona mensagem ao histórico"""
        mensagem = Mensagem(
            lead_id=lead_id,
            direcao=direcao,
            conteudo=conteudo
        )
        db.add(mensagem)
        
        # Atualiza data último contato
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            lead.data_ultimo_contato = datetime.utcnow()
        
        db.commit()
        return mensagem
    
    @staticmethod
    def criar_reuniao(db: Session, lead_id: str, data_hora: datetime, link_meet: str) -> Reuniao:
        """Cria reunião"""
        reuniao = Reuniao(
            lead_id=lead_id,
            titulo=f"Demo AI Agent - {db.query(Lead).filter(Lead.id == lead_id).first().nome}",
            data_hora=data_hora,
            link_meet=link_meet
        )
        db.add(reuniao)
        
        # Atualiza lead
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            lead.status = 'reuniao_agendada'
            lead.data_reuniao = data_hora
        
        db.commit()
        return reuniao