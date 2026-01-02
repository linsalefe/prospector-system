# scrapers/cnae_search.py
import requests
import time
import logging
from typing import List
import re

logger = logging.getLogger(__name__)

class CNAESearcher:
    """
    Busca empresas imobiliárias via CNAE na Receita Federal
    CNAE 6821-8/01 = Corretagem na compra e venda de imóveis
    """
    
    # Mapeamento de cidades para códigos IBGE
    CODIGOS_IBGE = {
        'Campina Grande': '2504009',
        'João Pessoa': '2507507',
        'Recife': '2611606',
        'Fortaleza': '2304400',
        'Natal': '2408102'
    }
    
    @staticmethod
    def buscar_por_cnae(cidade: str, estado: str, limite: int = 100) -> List[dict]:
        """
        Busca imobiliárias registradas por CNAE
        """
        
        logger.info(f"🏢 Buscando empresas registradas em {cidade}-{estado}...")
        
        leads = []
        
        # Método 1: Busca por palavras-chave + validação CNPJ
        keywords = ['imobiliaria', 'imoveis', 'imóveis', 'remax', 'corretor']
        
        for keyword in keywords:
            logger.info(f"  🔍 Buscando: {keyword}...")
            
            try:
                # API pública CNPJ.ws
                url = f"https://www.cnpj.ws/{keyword}/{cidade}/{estado}"
                
                response = requests.get(url, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for empresa in data[:limite]:
                        # Valida se é realmente imobiliária
                        cnae = empresa.get('atividade_principal', {}).get('id', '')
                        
                        # CNAEs de imobiliárias
                        cnaes_validos = ['6821-8', '6821801', '68.21-8-01']
                        
                        if any(cnae_val in str(cnae) for cnae_val in cnaes_validos):
                            
                            cnpj = empresa.get('cnpj', '').replace('.', '').replace('/', '').replace('-', '')
                            
                            lead = {
                                'id': f"cnae_{cnpj}",
                                'nome': empresa.get('razao_social', ''),
                                'fantasia': empresa.get('estabelecimento', {}).get('nome_fantasia'),
                                'cnpj': cnpj,
                                'telefone': CNAESearcher._extrair_telefone(empresa),
                                'email': empresa.get('estabelecimento', {}).get('email'),
                                'endereco': CNAESearcher._montar_endereco(empresa),
                                'cidade': cidade,
                                'estado': estado,
                                'fonte': 'Receita Federal (CNAE)',
                                'score': 8,
                                'website': None
                            }
                            
                            # Evita duplicatas
                            if not any(l['cnpj'] == cnpj for l in leads):
                                leads.append(lead)
                                logger.info(f"    ✅ {lead['nome']}")
                
                time.sleep(2)  # Rate limit
                
            except Exception as e:
                logger.error(f"  ❌ Erro na busca '{keyword}': {e}")
        
        logger.info(f"✅ {len(leads)} empresas registradas encontradas")
        
        return leads
    
    @staticmethod
    def _extrair_telefone(empresa: dict) -> str:
        """Extrai e formata telefone"""
        
        estab = empresa.get('estabelecimento', {})
        
        ddd = estab.get('ddd1', '')
        tel = estab.get('telefone1', '')
        
        if not ddd or not tel:
            return None
        
        # Monta número
        telefone = f"{ddd}{tel}".replace('-', '').replace(' ', '')
        
        # Remove caracteres especiais
        numeros = re.sub(r'[^0-9]', '', telefone)
        
        # Adiciona código do país se for celular (11 dígitos)
        if len(numeros) == 11:
            return f"55{numeros}"
        
        return numeros if len(numeros) >= 10 else None
    
    @staticmethod
    def _montar_endereco(empresa: dict) -> str:
        """Monta endereço completo"""
        
        estab = empresa.get('estabelecimento', {})
        
        partes = [
            estab.get('tipo_logradouro', ''),
            estab.get('logradouro', ''),
            estab.get('numero', ''),
            estab.get('bairro', ''),
            estab.get('cidade', {}).get('nome', ''),
            estab.get('estado', {}).get('sigla', '')
        ]
        
        return ', '.join([p for p in partes if p])