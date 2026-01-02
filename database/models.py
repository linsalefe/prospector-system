# database/models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Lead(Base):
    __tablename__ = 'leads'
    
    id = Column(String, primary_key=True)  # Google Maps place_id
    nome = Column(String, nullable=False)
    telefone = Column(String)
    email = Column(String)
    website = Column(String)
    domain = Column(String)
    
    # Contato
    contato_nome = Column(String)
    contato_cargo = Column(String)
    
    # Localização
    endereco = Column(String)
    cidade = Column(String)
    estado = Column(String)
    
    # Métricas
    rating = Column(Float)
    total_reviews = Column(Integer)
    score = Column(Integer)
    
    # Status
    status = Column(String, default='novo')  # novo, contatado, qualificado, reuniao_agendada, cliente, perdido
    estagio_conversa = Column(String)  # interesse, qualificacao, apresentacao, agendamento
    
    # Datas
    data_coleta = Column(DateTime, default=datetime.utcnow)
    data_primeiro_contato = Column(DateTime)
    data_ultimo_contato = Column(DateTime)
    data_reuniao = Column(DateTime)
    proximo_followup = Column(DateTime)
    
    # Qualificação
    leads_mes = Column(Integer)
    num_corretores = Column(Integer)
    usa_crm = Column(String)
    principal_canal = Column(String)
    
    # Metadata
    notas = Column(Text)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    mensagens = relationship("Mensagem", back_populates="lead", cascade="all, delete-orphan")
    reunioes = relationship("Reuniao", back_populates="lead", cascade="all, delete-orphan")

class Mensagem(Base):
    __tablename__ = 'mensagens'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(String, ForeignKey('leads.id'))
    
    direcao = Column(String)  # 'enviada' ou 'recebida'
    conteudo = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    enviada_com_sucesso = Column(Boolean, default=True)
    erro = Column(String)
    
    lead = relationship("Lead", back_populates="mensagens")

class Reuniao(Base):
    __tablename__ = 'reunioes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(String, ForeignKey('leads.id'))
    
    titulo = Column(String)
    data_hora = Column(DateTime)
    duracao_minutos = Column(Integer, default=30)
    link_meet = Column(String)
    google_event_id = Column(String)
    
    status = Column(String, default='agendada')  # agendada, realizada, cancelada, no_show
    
    # Notas
    notas_pre = Column(Text)
    notas_pos = Column(Text)
    resultado = Column(String)  # fechou, perdeu, followup
    
    criada_em = Column(DateTime, default=datetime.utcnow)
    
    lead = relationship("Lead", back_populates="reunioes")