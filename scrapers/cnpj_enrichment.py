# scrapers/cnpj_enrichment.py
import requests
import time
import logging
import re
from .local_cnpj_search import LocalCNPJSearch
from .cnpj_google import CNPJGoogleSearch

logger = logging.getLogger(__name__)

class CNPJEnricher:
    
    @staticmethod
    def buscar_cnpj_empresa(nome_empresa: str, cidade: str, estado: str, website: str = None) -> str:
        """
        Busca CNPJ da empresa (várias estratégias em ordem de prioridade)
        """
        
        # Estratégia 1: Banco local (MELHOR - offline e rápido)
        logger.info(f"  💾 Buscando no banco local...")
        try:
            resultado = LocalCNPJSearch.melhor_match(nome_empresa)
            if resultado:
                return resultado['cnpj']
        except Exception as e:
            logger.warning(f"  ⚠️ Erro no banco local: {e}")
        
        time.sleep(1)
        
        # Estratégia 2: Buscar no website da empresa
        if website:
            logger.info(f"  🌐 Tentando extrair do website...")
            cnpj = CNPJGoogleSearch.buscar_cnpj_website(website)
            if cnpj:
                return cnpj
            time.sleep(1)
        
        # Estratégia 3: Buscar no Google (fallback)
        logger.info(f"  🔍 Buscando no Google (fallback)...")
        cnpj = CNPJGoogleSearch.buscar_cnpj_google(nome_empresa, cidade)
        if cnpj:
            return cnpj
        
        return None
    
    @staticmethod
    def buscar_dados_cnpj(cnpj: str) -> dict:
        """
        Busca dados completos da empresa + sócios na Receita Federal
        """
        if not cnpj:
            return None
        
        # Limpa CNPJ
        cnpj_limpo = re.sub(r'[^0-9]', '', cnpj)
        
        logger.info(f"  📋 Consultando CNPJ na Receita: {cnpj_limpo}")
        
        try:
            # ReceitaWS - API gratuita (LIMITE: 3 req/min)
            url = f"https://receitaws.com.br/v1/cnpj/{cnpj_limpo}"
            
            response = requests.get(url, timeout=15)
            
            logger.info(f"  📡 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'OK':
                    resultado = {
                        'cnpj': data.get('cnpj'),
                        'nome': data.get('nome'),
                        'fantasia': data.get('fantasia'),
                        'telefone': data.get('telefone'),
                        'email': data.get('email'),
                        'capital_social': data.get('capital_social'),
                        'socios': []
                    }
                    
                    # Extrai sócios
                    for socio in data.get('qsa', []):
                        resultado['socios'].append({
                            'nome': socio.get('nome'),
                            'qualificacao': socio.get('qual', '')
                        })
                    
                    logger.info(f"  ✅ {len(resultado['socios'])} sócios encontrados")
                    return resultado
                else:
                    logger.warning(f"  ⚠️ {data.get('message', 'Erro desconhecido')}")
                    return None
            
            elif response.status_code == 429:
                logger.warning("⚠️ Rate limit! Aguardando 20s...")
                time.sleep(20)
                return CNPJEnricher.buscar_dados_cnpj(cnpj)
            else:
                logger.error(f"  ❌ HTTP {response.status_code}")
                return None
            
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            return None
    
    @staticmethod
    def enriquecer_lead(nome_empresa: str, cidade: str, estado: str, website: str = None) -> dict:
        """
        Pipeline completo de enriquecimento
        """
        
        logger.info(f"🔍 Enriquecendo: {nome_empresa}")
        
        # 1. Busca CNPJ (banco local primeiro)
        cnpj = CNPJEnricher.buscar_cnpj_empresa(nome_empresa, cidade, estado, website)
        
        if not cnpj:
            logger.warning("  ⚠️ CNPJ não encontrado")
            return None
        
        logger.info(f"  📋 CNPJ: {cnpj}")
        
        # 2. Rate limit antes de consultar Receita (20s entre requests)
        time.sleep(20)
        
        # 3. Busca dados completos (sócios)
        dados = CNPJEnricher.buscar_dados_cnpj(cnpj)
        
        if dados and dados['socios']:
            # 4. Extrai nome do principal sócio
            principal_socio = dados['socios'][0]['nome']
            primeiro_nome = principal_socio.split()[0].title()
            
            dados['contato_nome'] = primeiro_nome
            dados['contato_cargo'] = dados['socios'][0]['qualificacao']
            
            logger.info(f"  👤 Contato: {primeiro_nome} ({dados['contato_cargo']})")
        
        return dados