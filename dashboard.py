# dashboard.py
import streamlit as st
import pandas as pd
from database.database import SessionLocal
from database.models import Lead, Mensagem
from database.crud import LeadCRUD
from sqlalchemy import func, desc
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Prospector CRM",
    page_icon="🎯",
    layout="wide"
)

# Título
st.title("🎯 Prospector CRM")

# Sidebar
st.sidebar.title("Menu")
pagina = st.sidebar.radio("Navegação", ["Dashboard", "Pipeline", "Leads", "Conversas", "Coleta"])

# Conexão com banco
db = SessionLocal()

# ==========================================
# PÁGINA: DASHBOARD
# ==========================================
if pagina == "Dashboard":
    st.header("📊 Visão Geral")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    total_leads = db.query(func.count(Lead.id)).scalar()
    com_whatsapp = db.query(func.count(Lead.id)).filter(Lead.telefone.isnot(None)).scalar()
    score_medio = db.query(func.avg(Lead.score)).scalar() or 0
    contatados = db.query(func.count(Lead.id)).filter(Lead.status != 'novo').scalar()
    
    col1.metric("Total de Leads", total_leads)
    col2.metric("Com WhatsApp", f"{com_whatsapp} ({int(com_whatsapp/total_leads*100) if total_leads > 0 else 0}%)")
    col3.metric("Score Médio", f"{score_medio:.1f}/10")
    col4.metric("Já Contatados", contatados)
    
    st.divider()
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📍 Leads por Cidade")
        
        por_cidade = db.query(Lead.cidade, func.count(Lead.id).label('count'))\
            .group_by(Lead.cidade).all()
        
        df_cidades = pd.DataFrame(por_cidade, columns=['Cidade', 'Count'])
        fig_cidades = px.bar(df_cidades, x='Cidade', y='Count', 
                            color='Count',
                            color_continuous_scale='Blues')
        st.plotly_chart(fig_cidades, use_container_width=True)
    
    with col2:
        st.subheader("⭐ Distribuição de Score")
        
        por_score = db.query(Lead.score, func.count(Lead.id).label('count'))\
            .group_by(Lead.score)\
            .order_by(Lead.score.desc()).all()
        
        df_scores = pd.DataFrame(por_score, columns=['Score', 'Count'])
        fig_scores = px.bar(df_scores, x='Score', y='Count',
                           color='Score',
                           color_continuous_scale='Greens')
        st.plotly_chart(fig_scores, use_container_width=True)
    
    st.divider()
    
    # Top leads
    st.subheader("🏆 Top 10 Leads (Score Alto)")
    
    top_leads = db.query(Lead)\
        .filter(Lead.score >= 7)\
        .order_by(Lead.score.desc())\
        .limit(10).all()
    
    for lead in top_leads:
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        col1.write(f"**{lead.nome}**")
        col2.write(f"📍 {lead.cidade}")
        col3.write(f"📱 {lead.telefone or 'Sem WhatsApp'}")
        col4.write(f"⭐ {lead.score}")

# ==========================================
# PÁGINA: PIPELINE (KANBAN)
# ==========================================
elif pagina == "Pipeline":
    st.header("📊 Pipeline de Vendas (Kanban)")
    
    # Define estágios
    estagios = {
        "novo": {"emoji": "🆕", "nome": "Novo", "cor": "#2196F3"},
        "contatado": {"emoji": "📞", "nome": "Contatado", "cor": "#FF9800"},
        "qualificado": {"emoji": "✅", "nome": "Qualificado", "cor": "#9C27B0"},
        "reuniao_agendada": {"emoji": "🗓️", "nome": "Reunião Agendada", "cor": "#4CAF50"},
        "cliente": {"emoji": "🎉", "nome": "Cliente", "cor": "#00BCD4"},
        "perdido": {"emoji": "❌", "nome": "Perdido", "cor": "#F44336"}
    }
    
    # Métricas por estágio
    cols_metricas = st.columns(len(estagios))
    for idx, (status, info) in enumerate(estagios.items()):
        count = db.query(func.count(Lead.id)).filter(Lead.status == status).scalar()
        cols_metricas[idx].metric(f"{info['emoji']} {info['nome']}", count)
    
    st.divider()
    
    # Kanban Board
    cols = st.columns(len(estagios))
    
    for idx, (status, info) in enumerate(estagios.items()):
        with cols[idx]:
            # Header da coluna
            st.markdown(f"### {info['emoji']} {info['nome']}")
            
            # Busca leads deste estágio
            leads = db.query(Lead)\
                .filter(Lead.status == status)\
                .order_by(Lead.score.desc())\
                .limit(10)\
                .all()
            
            if not leads:
                st.info("Vazio")
            else:
                for lead in leads:
                    # Container do card
                    with st.container():
                        # Nome truncado
                        nome_display = lead.nome[:22] + "..." if len(lead.nome) > 22 else lead.nome
                        tel_display = lead.telefone[-9:] if lead.telefone else "Sem tel"
                        
                        st.markdown(f"""
                        <div style='
                            background-color: #ffffff;
                            padding: 12px;
                            border-radius: 8px;
                            border-left: 4px solid {info['cor']};
                            margin-bottom: 10px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            color: #000000;
                        '>
                            <strong style='color: #000000; font-size: 14px;'>{nome_display}</strong><br>
                            <small style='color: #666666;'>📍 {lead.cidade}</small><br>
                            <small style='color: #666666;'>📱 {tel_display}</small><br>
                            <small style='color: #666666;'>⭐ {lead.score}/10</small>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Botões
                        col1, col2, col3 = st.columns(3)
                        
                        # Ver detalhes
                        if col1.button("👁️", key=f"ver_{lead.id}"):
                            st.session_state.modal_lead = lead.id
                        
                        # Mover para próximo estágio
                        prox = None
                        if status == "novo":
                            prox = "contatado"
                        elif status == "contatado":
                            prox = "qualificado"
                        elif status == "qualificado":
                            prox = "reuniao_agendada"
                        elif status == "reuniao_agendada":
                            prox = "cliente"
                        
                        if prox and col2.button("➡️", key=f"move_{lead.id}"):
                            LeadCRUD.atualizar_status(db, lead.id, prox)
                            st.success(f"Movido para {estagios[prox]['nome']}")
                            st.rerun()
                        
                        # Marcar como perdido
                        if status not in ["cliente", "perdido"] and col3.button("❌", key=f"lost_{lead.id}"):
                            LeadCRUD.atualizar_status(db, lead.id, "perdido")
                            st.warning("Marcado como perdido")
                            st.rerun()
    
    # Modal de detalhes
    if 'modal_lead' in st.session_state:
        lead = LeadCRUD.buscar_lead(db, st.session_state.modal_lead)
        if lead:
            st.divider()
            st.subheader(f"📋 Detalhes: {lead.nome}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**📍 Cidade:** {lead.cidade}")
                st.write(f"**📱 Telefone:** {lead.telefone or 'N/A'}")
                st.write(f"**⭐ Score:** {lead.score}/10")
                st.write(f"**⭐ Rating:** {lead.rating or 'N/A'}")
            
            with col2:
                st.write(f"**🏷️ Status:** {lead.status}")
                st.write(f"**📊 Reviews:** {lead.total_reviews or 0}")
                if lead.website:
                    st.markdown(f"**🌐 Website:** [{lead.website}]({lead.website})")
                st.write(f"**📧 Email:** {lead.email or 'N/A'}")
            
            if st.button("✖️ Fechar"):
                del st.session_state.modal_lead
                st.rerun()

# ==========================================
# PÁGINA: LEADS
# ==========================================
elif pagina == "Leads":
    st.header("📋 Lista de Leads")
    
    # Filtros
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        filtro_cidade = st.selectbox(
            "Cidade",
            ["Todas"] + [c[0] for c in db.query(Lead.cidade).distinct().all()]
        )
    
    with col2:
        filtro_score = st.slider("Score mínimo", 0, 10, 0)
    
    with col3:
        filtro_whatsapp = st.checkbox("Apenas com WhatsApp")
    
    with col4:
        filtro_status = st.selectbox(
            "Status",
            ["Todos", "novo", "contatado", "qualificado", "reuniao_agendada", "cliente", "perdido"]
        )
    
    # Query com filtros
    query = db.query(Lead).filter(Lead.score >= filtro_score)
    
    if filtro_cidade != "Todas":
        query = query.filter(Lead.cidade == filtro_cidade)
    
    if filtro_whatsapp:
        query = query.filter(Lead.telefone.isnot(None))
    
    if filtro_status != "Todos":
        query = query.filter(Lead.status == filtro_status)
    
    leads = query.order_by(Lead.score.desc()).all()
    
    st.write(f"**{len(leads)} leads encontrados**")
    
    # Tabela de leads
    if leads:
        df_leads = pd.DataFrame([{
            'Nome': lead.nome,
            'Cidade': lead.cidade,
            'Telefone': lead.telefone or '-',
            'Score': lead.score,
            'Rating': f"{lead.rating or 0:.1f}",
            'Reviews': lead.total_reviews or 0,
            'Status': lead.status
        } for lead in leads])
        
        st.dataframe(
            df_leads,
            use_container_width=True,
            hide_index=True
        )
        
        # Exportar CSV
        csv = df_leads.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar CSV",
            data=csv,
            file_name="leads.csv",
            mime="text/csv"
        )

# ==========================================
# PÁGINA: CONVERSAS
# ==========================================
elif pagina == "Conversas":
    st.header("💬 Conversas")
    
    # Busca leads com mensagens
    leads_com_msg = db.query(Lead)\
        .join(Mensagem)\
        .group_by(Lead.id)\
        .order_by(desc(func.max(Mensagem.timestamp)))\
        .all()
    
    if not leads_com_msg:
        st.info("Nenhuma conversa ainda")
    else:
        # Seletor de lead
        lead_selecionado = st.selectbox(
            "Selecione um lead",
            leads_com_msg,
            format_func=lambda x: f"{x.nome} ({x.cidade}) - {len(x.mensagens)} msgs"
        )
        
        if lead_selecionado:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader(f"💬 {lead_selecionado.nome}")
                st.write(f"📍 {lead_selecionado.cidade} | ⭐ Score: {lead_selecionado.score}")
                st.write(f"📱 {lead_selecionado.telefone or 'Sem telefone'}")
                st.write(f"🏷️ Status: **{lead_selecionado.status}**")
                if lead_selecionado.estagio_conversa:
                    st.write(f"📊 Estágio: **{lead_selecionado.estagio_conversa}**")
            
            with col2:
                if lead_selecionado.website:
                    st.write(f"🌐 [Website]({lead_selecionado.website})")
                st.write(f"💬 Total mensagens: {len(lead_selecionado.mensagens)}")
            
            st.divider()
            
            # Histórico de mensagens
            st.subheader("📜 Histórico")
            
            for msg in lead_selecionado.mensagens:
                if msg.direcao == 'recebida':
                    st.markdown(f"""
                    <div style='background-color: #e3f2fd; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;'>
                        <strong>👤 Lead:</strong><br>
                        {msg.conteudo}<br>
                        <small style='color: #666;'>{msg.timestamp.strftime('%d/%m/%Y %H:%M')}</small>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='background-color: #f1f8e9; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;'>
                        <strong>🤖 Agent:</strong><br>
                        {msg.conteudo}<br>
                        <small style='color: #666;'>{msg.timestamp.strftime('%d/%m/%Y %H:%M')}</small>
                    </div>
                    """, unsafe_allow_html=True)

# ==========================================
# PÁGINA: COLETA
# ==========================================
elif pagina == "Coleta":
    st.header("🔍 Coletar Novos Leads")
    
    st.write("Execute a coleta de leads diretamente pelo dashboard.")
    
    cidades_input = st.text_area(
        "Cidades (uma por linha)",
        "Campina Grande PB\nJoão Pessoa PB"
    )
    
    limite = st.slider("Limite por cidade", 5, 50, 10)
    
    if st.button("🚀 Iniciar Coleta", type="primary"):
        with st.spinner("Coletando leads..."):
            from config import Config
            from scrapers.google_maps import ImobiliariasScraper
            
            cidades = [c.strip() for c in cidades_input.split('\n') if c.strip()]
            
            scraper = ImobiliariasScraper(
                google_api_key=Config.GOOGLE_MAPS_API_KEY,
                hunter_api_key=Config.HUNTER_API_KEY
            )
            
            df = scraper.buscar_imobiliarias(cidades, limite_por_cidade=limite)
            
            novos = 0
            duplicados = 0
            
            for _, row in df.iterrows():
                existing = LeadCRUD.buscar_lead(db, row['id'])
                if not existing:
                    LeadCRUD.criar_lead(db, row.to_dict())
                    novos += 1
                else:
                    duplicados += 1
            
            st.success(f"✅ Coleta concluída! {novos} novos leads, {duplicados} duplicados")
            st.balloons()

db.close()