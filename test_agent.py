# test_agent.py
from dotenv import load_dotenv
from config import Config
from agent.qualifier import QualifierAgent

load_dotenv()

print("🤖 Testando AI Agent...\n")

# Inicializa agent
agent = QualifierAgent(api_key=Config.OPENAI_API_KEY)

# Dados de um lead
lead_data = {
    'nome': 'Shalom Imóveis',
    'cidade': 'Campina Grande',
    'contato_nome': 'João'
}

# Simula conversa
print("=" * 50)
print("TESTE 1: Primeira mensagem do lead")
print("=" * 50)

msg1 = "Oi, vi sua mensagem. Conte mais sobre o sistema"
historico = []

resposta, estagio, notificar = agent.processar_mensagem(lead_data, msg1, historico)

print(f"\n📱 Lead: {msg1}")
print(f"🤖 Agent: {resposta}")
print(f"📊 Estágio: {estagio}")
print(f"🔔 Notificar humano: {notificar}")

print("\n" + "=" * 50)
print("TESTE 2: Lead interessado")
print("=" * 50)

historico = [
    {'direcao': 'recebida', 'conteudo': msg1},
    {'direcao': 'enviada', 'conteudo': resposta}
]

msg2 = "Interessante! Quantos leads vocês atendem por mês?"

resposta2, estagio2, notificar2 = agent.processar_mensagem(lead_data, msg2, historico)

print(f"\n📱 Lead: {msg2}")
print(f"🤖 Agent: {resposta2}")
print(f"📊 Estágio: {estagio2}")
print(f"🔔 Notificar humano: {notificar2}")