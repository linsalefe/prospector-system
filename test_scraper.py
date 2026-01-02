# test_scraper.py
from dotenv import load_dotenv
from config import Config
from scrapers.google_maps import ImobiliariasScraper
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)

# Testa scraper
scraper = ImobiliariasScraper(
    google_api_key=Config.GOOGLE_MAPS_API_KEY,
    hunter_api_key=None
)

print("🔍 Testando busca em Campina Grande...")

# Busca apenas 5 leads para teste
df = scraper.buscar_imobiliarias(['Campina Grande PB'], limite_por_cidade=5)

print(f"\n✅ {len(df)} leads encontrados!\n")
print(df[['nome', 'telefone', 'cidade', 'rating', 'score']].to_string())

