# scrapers/creci.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import logging

logger = logging.getLogger(__name__)

class CRECIScraper:
    """
    Scraper para buscar imobiliárias e corretores no CRECI
    """
    
    CRECI_URLS = {
        'PB': 'https://www.crecipb.gov.br',
        'PE': 'https://www.crecipe.gov.br',
        'CE': 'https://www.crecice.gov.br'
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def buscar_imobiliarias(self, estado: str, cidade: str = None, limite: int = 100) -> pd.DataFrame:
        """
        Busca imobiliárias registradas no CRECI
        
        Args:
            estado: Sigla do estado (PB, PE, CE)
            cidade: Cidade específica (opcional)
            limite: Limite de resultados
        """
        
        logger.info(f"🔍 Buscando no CRECI-{estado}...")
        
        if estado == 'PB':
            return self._buscar_creci_pb(cidade, limite)
        elif estado == 'PE':
            return self._buscar_creci_pe(cidade, limite)
        elif estado == 'CE':
            return self._buscar_creci_ce(cidade, limite)
        else:
            logger.error(f"Estado {estado} não suportado")
            return pd.DataFrame()
    
    def _buscar_creci_pb(self, cidade: str, limite: int) -> pd.DataFrame:
        """
        Busca específica para CRECI-PB
        """
        
        leads = []
        
        try:
            # URL de consulta do CRECI-PB
            url = "https://www.crecipb.gov.br/consulta-publica/"
            
            # Faz requisição
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                logger.error(f"Erro ao acessar CRECI-PB: {response.status_code}")
                return pd.DataFrame()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Procura por empresas
            # NOTA: A estrutura HTML varia, pode precisar ajustar
            empresas = soup.find_all('div', class_='empresa')
            
            for empresa in empresas[:limite]:
                try:
                    nome = empresa.find('h3').text.strip()
                    
                    # Extrai CRECI
                    creci = empresa.find('span', class_='creci')
                    creci_numero = creci.text.strip() if creci else None
                    
                    # Extrai telefone
                    tel = empresa.find('span', class_='telefone')
                    telefone = tel.text.strip() if tel else None
                    
                    # Extrai email
                    email_tag = empresa.find('a', href=re.compile('mailto:'))
                    email = email_tag['href'].replace('mailto:', '') if email_tag else None
                    
                    # Extrai cidade
                    cidade_tag = empresa.find('span', class_='cidade')
                    cidade_nome = cidade_tag.text.strip() if cidade_tag else None
                    
                    # Filtro por cidade se especificado
                    if cidade and cidade_nome:
                        if cidade.lower() not in cidade_nome.lower():
                            continue
                    
                    lead = {
                        'id': f"creci_pb_{creci_numero}",
                        'nome': nome,
                        'telefone': self._limpar_telefone(telefone),
                        'email': email,
                        'creci': creci_numero,
                        'cidade': cidade_nome or cidade,
                        'estado': 'PB',
                        'fonte': 'CRECI-PB',
                        'score': 7  # Score padrão alto (é empresa registrada)
                    }
                    
                    leads.append(lead)
                    logger.info(f"  ✅ {nome}")
                    
                except Exception as e:
                    logger.error(f"Erro ao processar empresa: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ Erro no scraping CRECI-PB: {e}")
        
        logger.info(f"✅ {len(leads)} imobiliárias encontradas no CRECI-PB")
        
        return pd.DataFrame(leads)
    
    def _buscar_creci_pe(self, cidade: str, limite: int) -> pd.DataFrame:
        """
        Busca específica para CRECI-PE
        """
        # Implementação similar ao PB
        # Ajustar conforme estrutura do site
        logger.warning("CRECI-PE ainda não implementado")
        return pd.DataFrame()
    
    def _buscar_creci_ce(self, cidade: str, limite: int) -> pd.DataFrame:
        """
        Busca específica para CRECI-CE
        """
        # Implementação similar ao PB
        logger.warning("CRECI-CE ainda não implementado")
        return pd.DataFrame()
    
    def _limpar_telefone(self, telefone: str) -> str:
        """
        Limpa e formata telefone para WhatsApp
        """
        if not telefone:
            return None
        
        # Remove caracteres especiais
        numeros = re.sub(r'[^0-9]', '', telefone)
        
        # Se já tem 55, retorna
        if numeros.startswith('55'):
            return numeros
        
        # Se tem 11 dígitos (celular), adiciona 55
        if len(numeros) == 11:
            return f"55{numeros}"
        
        # Se tem 10 (fixo), não usa
        if len(numeros) == 10:
            return None
        
        return numeros if len(numeros) >= 10 else None