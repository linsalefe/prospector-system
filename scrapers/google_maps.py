# scrapers/google_maps.py
import googlemaps
import pandas as pd
from typing import List
import time
import re
import logging

logger = logging.getLogger(__name__)

class ImobiliariasScraper:
    def __init__(self, google_api_key: str, hunter_api_key: str = None):
        self.gmaps = googlemaps.Client(key=google_api_key)
        self.hunter_api_key = hunter_api_key
    
    def buscar_imobiliarias(self, cidades: List[str], limite_por_cidade: int = 100) -> pd.DataFrame:
        """
        Busca imobiliárias em várias cidades usando Google Maps API
        """
        
        todos_leads = []
        leads_unicos = {}  # Para evitar duplicatas
        
        for cidade in cidades:
            logger.info(f"🔍 Buscando em: {cidade}")
            
            # Faz múltiplas buscas com termos diferentes
            termos = [
                f"imobiliária em {cidade}",
                f"corretor de imóveis em {cidade}",
                f"imóveis em {cidade}",
                f"apartamentos venda {cidade}",
            ]
            
            for termo in termos:
                try:
                    logger.info(f"   Termo: '{termo}'")
                    
                    # Primeira página
                    places_result = self.gmaps.places(
                        query=termo,
                        language='pt-BR'
                    )
                    
                    self._processar_resultados(places_result, cidade, leads_unicos)
                    
                    # Páginas seguintes (se houver)
                    while 'next_page_token' in places_result:
                        time.sleep(2)  # Obrigatório aguardar antes de usar next_page_token
                        
                        places_result = self.gmaps.places(
                            page_token=places_result['next_page_token'],
                            language='pt-BR'
                        )
                        
                        self._processar_resultados(places_result, cidade, leads_unicos)
                    
                    time.sleep(1)  # Delay entre termos
                    
                except Exception as e:
                    logger.error(f"❌ Erro no termo '{termo}': {e}")
            
            logger.info(f"✅ {len([l for l in leads_unicos.values() if l['cidade'] == cidade.split()[0]])} leads únicos em {cidade}")
        
        # Converte para lista
        todos_leads = list(leads_unicos.values())
        
        # Converte para DataFrame
        df = pd.DataFrame(todos_leads)
        
        logger.info(f"🎯 Total: {len(df)} leads únicos coletados")
        
        return df
    
    def _processar_resultados(self, places_result: dict, cidade: str, leads_unicos: dict):
        """Processa resultados e adiciona ao dicionário de leads únicos"""
        
        for place in places_result.get('results', []):
            lead = self._processar_place(place, cidade)
            
            if lead and lead['id'] not in leads_unicos:
                # Filtra: só adiciona se for realmente imobiliária
                nome_lower = lead['nome'].lower()
                if any(palavra in nome_lower for palavra in ['imob', 'imóve', 'corretor', 'remax', 're/max']):
                    leads_unicos[lead['id']] = lead
                    logger.info(f"  ✅ {lead['nome']}")
    
    def _processar_place(self, place: dict, cidade: str) -> dict:
        """
        Processa um resultado do Google Places e extrai informações
        """
        
        try:
            place_id = place.get('place_id')
            
            # Busca detalhes completos
            details = self.gmaps.place(
                place_id=place_id,
                language='pt-BR',
                fields=['name', 'formatted_phone_number', 'website', 
                       'formatted_address', 'rating', 'user_ratings_total']
            )
            
            result = details.get('result', {})
            
            # Extrai dados
            nome = result.get('name', '')
            telefone = result.get('formatted_phone_number', '')
            website = result.get('website', '')
            endereco = result.get('formatted_address', '')
            rating = result.get('rating', 0)
            total_reviews = result.get('user_ratings_total', 0)
            
            # Limpa telefone para formato WhatsApp
            telefone_limpo = self._limpar_telefone(telefone)
            
            # Extrai domínio do site
            domain = self._extrair_domain(website)
            
            # Calcula score de qualificação (0-10)
            score = self._calcular_score(rating, total_reviews, telefone_limpo, website)
            
            # Extrai estado
            estado = self._extrair_estado(cidade)
            
            lead_data = {
                'id': place_id,
                'nome': nome,
                'telefone': telefone_limpo,
                'email': None,
                'website': website,
                'domain': domain,
                'endereco': endereco,
                'cidade': cidade.split()[0],
                'estado': estado,
                'rating': rating,
                'total_reviews': total_reviews,
                'score': score,
                'status': 'novo',
                'contato_nome': None,
                'contato_cargo': None
            }
            
            return lead_data
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar place: {e}")
            return None
    
    def _limpar_telefone(self, telefone: str) -> str:
        """
        Limpa telefone e formata para WhatsApp (5583...)
        """
        if not telefone:
            return None
        
        # Remove caracteres especiais
        numeros = re.sub(r'[^0-9]', '', telefone)
        
        # Se já tem código do país, retorna
        if numeros.startswith('55'):
            return numeros
        
        # Se tem 11 dígitos (celular), adiciona 55
        if len(numeros) == 11:
            return f"55{numeros}"
        
        # Se tem 10 dígitos (fixo), não usa (WhatsApp só celular)
        if len(numeros) == 10:
            return None
        
        return numeros if len(numeros) >= 10 else None
    
    def _extrair_domain(self, website: str) -> str:
        """Extrai domínio do website"""
        if not website:
            return None
        
        # Remove protocolo
        domain = re.sub(r'https?://', '', website)
        domain = re.sub(r'www\.', '', domain)
        domain = domain.split('/')[0]
        
        return domain
    
    def _calcular_score(self, rating: float, reviews: int, telefone: str, website: str) -> int:
        """
        Calcula score de qualificação (0-10)
        """
        score = 0
        
        # Rating
        if rating >= 4.5:
            score += 2
        elif rating >= 4.0:
            score += 1
        
        # Reviews
        if reviews >= 100:
            score += 2
        elif reviews >= 50:
            score += 1
        
        # Telefone
        if telefone:
            score += 3
        
        # Website
        if website:
            score += 3
        
        return min(score, 10)
    
    def _extrair_estado(self, cidade: str) -> str:
        """Extrai sigla do estado da cidade"""
        partes = cidade.split()
        if len(partes) >= 2:
            return partes[-1]
        return ''