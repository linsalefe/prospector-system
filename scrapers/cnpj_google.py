# scrapers/cnpj_google.py
import requests
from bs4 import BeautifulSoup
import re
import logging
import time

logger = logging.getLogger(__name__)

class CNPJGoogleSearch:
    
    @staticmethod
    def validar_cnpj(cnpj: str) -> bool:
        """
        Valida dígitos verificadores do CNPJ
        """
        cnpj = re.sub(r'[^0-9]', '', cnpj)
        
        if len(cnpj) != 14:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cnpj == cnpj[0] * 14:
            return False
        
        # Calcula primeiro dígito verificador
        soma = 0
        peso = 5
        for i in range(12):
            soma += int(cnpj[i]) * peso
            peso -= 1
            if peso < 2:
                peso = 9
        
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        if int(cnpj[12]) != digito1:
            return False
        
        # Calcula segundo dígito verificador
        soma = 0
        peso = 6
        for i in range(13):
            soma += int(cnpj[i]) * peso
            peso -= 1
            if peso < 2:
                peso = 9
        
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        if int(cnpj[13]) != digito2:
            return False
        
        return True
    
    @staticmethod
    def buscar_cnpj_google(nome_empresa: str, cidade: str) -> str:
        """
        Busca CNPJ da empresa via Google Search
        """
        
        try:
            # Monta query de busca
            query = f"{nome_empresa} {cidade} CNPJ"
            
            url = "https://www.google.com/search"
            params = {
                'q': query,
                'hl': 'pt-BR'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Procura por padrão de CNPJ na página
                # CNPJ: XX.XXX.XXX/XXXX-XX ou XXXXXXXXXXXXXX
                cnpj_pattern = r'\d{2}\.?\d{3}\.?\d{3}/?0001-?\d{2}|\b\d{14}\b'
                
                cnpjs = re.findall(cnpj_pattern, response.text)
                
                # Valida cada CNPJ encontrado
                for cnpj_raw in cnpjs:
                    cnpj = cnpj_raw.replace('.', '').replace('/', '').replace('-', '')
                    
                    if CNPJGoogleSearch.validar_cnpj(cnpj):
                        logger.info(f"✅ CNPJ válido encontrado via Google: {cnpj}")
                        return cnpj
            
            logger.warning(f"⚠️ CNPJ válido não encontrado no Google para {nome_empresa}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro na busca Google: {e}")
            return None
    
    @staticmethod
    def buscar_cnpj_website(website: str) -> str:
        """
        Busca CNPJ no website da empresa (rodapé)
        """
        
        if not website:
            return None
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(website, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Procura CNPJ na página - padrão mais específico
                # Busca por "CNPJ" seguido de números
                texto = response.text
                
                # Padrão: palavra "CNPJ" próxima aos números
                if 'CNPJ' in texto or 'cnpj' in texto:
                    # Procura padrão após a palavra CNPJ
                    cnpj_pattern = r'(?:CNPJ|cnpj)[:\s]*(\d{2}\.?\d{3}\.?\d{3}/?0001-?\d{2})'
                    
                    match = re.search(cnpj_pattern, texto)
                    if match:
                        cnpj = match.group(1).replace('.', '').replace('/', '').replace('-', '')
                        
                        if CNPJGoogleSearch.validar_cnpj(cnpj):
                            logger.info(f"✅ CNPJ válido encontrado no site: {cnpj}")
                            return cnpj
                
                # Se não encontrou com contexto, busca qualquer CNPJ válido
                cnpj_pattern = r'\d{2}\.?\d{3}\.?\d{3}/?0001-?\d{2}'
                cnpjs = re.findall(cnpj_pattern, texto)
                
                for cnpj_raw in cnpjs:
                    cnpj = cnpj_raw.replace('.', '').replace('/', '').replace('-', '')
                    
                    if CNPJGoogleSearch.validar_cnpj(cnpj):
                        logger.info(f"✅ CNPJ válido encontrado no site: {cnpj}")
                        return cnpj
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao acessar website: {e}")
            return None