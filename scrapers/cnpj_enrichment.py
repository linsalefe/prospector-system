# scrapers/cnpj_enrichment.py
import requests
import time
import logging
import re
from .cnpj_google import CNPJGoogleSearch

logger = logging.getLogger(__name__)

class CNPJEnricher:
    
    @staticmethod
    def buscar_cnpj_empresa(nome_empresa: str, cidade: str, website: str = None) -> str:
        """
        Busca CNPJ da empresa (várias estratégias)
        """
        
        # Estratégia 1: Buscar no website da empresa
        if website:
            logger.info(f"  🌐 Tentando extrair do website...")
            cnpj = CNPJGoogleSearch.buscar_cnpj_website(website)
            if cnpj:
                return cnpj
            time.sleep(2)
        
        # Estratégia 2: Buscar no Google
        logger.info(f"  🔍 Buscando no Google...")
        cnpj = CNPJGoogleSearch.buscar_cnpj_google(nome_empresa, cidade)
        if cnpj:
            return cnpj
        
        return None
    
    @staticmethod
    def buscar_dados_cnpj(cnpj: str) -> dict:
        """
        Busca dados completos da empresa + sócios
        """
        if not cnpj:
            return None
        
        # Limpa CNPJ
        cnpj_limpo = re.sub(r'[^0-9]', '', cnpj)
        
        logger.info(f"  📋 Consultando CNPJ: {cnpj_limpo}")
        
        try:
            # ReceitaWS - API gratuita (cuidado com rate limit: 3 req/min)
            url = f"https://receitaws.com.br/v1/cnpj/{cnpj_limpo}"
            
            response = requests.get(url, timeout=15)
            
            logger.info(f"  📡 Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                logger.info(f"  📦 Resposta status: {data.get('status')}")
                
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
                    
                    logger.info(f"  ✅ Dados obtidos: {len(resultado['socios'])} sócios encontrados")
                    return resultado
                else:
                    logger.warning(f"  ⚠️ Status não OK: {data.get('message', 'Sem mensagem')}")
                    return None
            
            elif response.status_code == 429:
                logger.warning("⚠️ Rate limit atingido, aguardando 20s...")
                time.sleep(20)
                return CNPJEnricher.buscar_dados_cnpj(cnpj)
            else:
                logger.error(f"  ❌ Erro HTTP: {response.status_code}")
                try:
                    logger.error(f"  ❌ Resposta: {response.text[:200]}")
                except:
                    pass
                return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao consultar CNPJ: {e}")
            return None
    
    @staticmethod
    def enriquecer_lead(nome_empresa: str, cidade: str, website: str = None) -> dict:
        """
        Pipeline completo de enriquecimento
        """
        
        logger.info(f"🔍 Enriquecendo: {nome_empresa}")
        
        # 1. Busca CNPJ (várias estratégias)
        cnpj = CNPJEnricher.buscar_cnpj_empresa(nome_empresa, cidade, website)
        
        if not cnpj:
            logger.warning("  ⚠️ CNPJ não encontrado")
            return None
        
        logger.info(f"  📋 CNPJ encontrado: {cnpj}")
        
        # Aguarda para não bater rate limit
        time.sleep(2)
        
        # 2. Busca dados completos
        dados = CNPJEnricher.buscar_dados_cnpj(cnpj)
        
        if dados:
            # 3. Tenta extrair nome do principal sócio
            if dados['socios']:
                principal_socio = dados['socios'][0]['nome']
                primeiro_nome = principal_socio.split()[0].title()
                
                dados['contato_nome'] = primeiro_nome
                dados['contato_cargo'] = dados['socios'][0]['qualificacao']
            
            return dados
        
        return None