# scrapers/creci_cnpj.py
import requests
import time
import logging

logger = logging.getLogger(__name__)

class CRECIBuscador:
    """
    Busca empresas imobiliárias via CNPJ filtrando por CNAE
    CNAE 6821-8/01 = Corretagem na compra e venda de imóveis
    """
    
    @staticmethod
    def buscar_imobiliarias_por_cidade(cidade: str, estado: str, limite: int = 100):
        """
        Busca todas as imobiliárias registradas em uma cidade
        """
        
        logger.info(f"🔍 Buscando imobiliárias registradas em {cidade}-{estado}...")
        
        leads = []
        
        try:
            # API Brasil.io - base de CNPJs públicos
            url = "https://api.brasil.io/v1/dataset/empresas/companies/data/"
            
            params = {
                'municipio': cidade.upper(),
                'uf': estado,
                'cnae_fiscal_principal': '6821801',  # CNAE de imobiliária
                'page_size': limite
            }
            
            # Precisa de token (gratuito)
            # Registre em: https://brasil.io/auth/entrar/
            headers = {
                'Authorization': 'Token SEU_TOKEN_AQUI'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                for empresa in data.get('results', []):
                    lead = {
                        'id': empresa['cnpj'],
                        'nome': empresa['razao_social'],
                        'fantasia': empresa.get('nome_fantasia'),
                        'cnpj': empresa['cnpj'],
                        'telefone': empresa.get('ddd_telefone_1'),
                        'email': empresa.get('email'),
                        'cidade': cidade,
                        'estado': estado,
                        'fonte': 'Receita Federal',
                        'score': 8  # Alto porque é empresa ativa
                    }
                    
                    leads.append(lead)
                    logger.info(f"  ✅ {lead['nome']}")
            
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
        
        logger.info(f"✅ {len(leads)} empresas encontradas")
        
        return leads