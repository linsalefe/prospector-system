# scrapers/educacao_search.py
import requests
import time
import logging
from typing import List
import re

logger = logging.getLogger(__name__)

class EducacaoSearcher:
    """
    Busca instituições de ensino via CNAE na Receita Federal
    """
    
    # CNAEs de Educação
    CNAES_EDUCACAO = [
        '8511-2',  # Educação infantil - creche
        '8512-1',  # Educação infantil - pré-escola
        '8513-9',  # Ensino fundamental
        '8520-1',  # Ensino médio
        '8531-7',  # Educação superior - graduação
        '8532-5',  # Educação superior - graduação e pós
        '8533-3',  # Educação superior - pós-graduação
        '8541-4',  # Educação profissional técnico
        '8542-2',  # Educação profissional tecnológico
        '8592-9',  # Ensino de idiomas
        '8593-7',  # Ensino de música
        '8599-6',  # Outras atividades de ensino
    ]
    
    @staticmethod
    def buscar_por_cnae(cidade: str, estado: str, limite: int = 100) -> List[dict]:
        """
        Busca instituições de ensino registradas por CNAE
        """
        
        logger.info(f"🎓 Buscando instituições de ensino em {cidade}-{estado}...")
        
        leads = []
        
        # Keywords de busca
        keywords = [
            'escola', 'colegio', 'faculdade', 'universidade', 
            'curso', 'instituto', 'educacao', 'ensino'
        ]
        
        for keyword in keywords:
            logger.info(f"  🔍 Buscando: {keyword}...")
            
            try:
                # API pública CNPJ.ws
                url = f"https://www.cnpj.ws/{keyword}/{cidade}/{estado}"
                
                response = requests.get(url, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for empresa in data[:limite]:
                        # Valida se é instituição de ensino
                        cnae = empresa.get('atividade_principal', {}).get('id', '')
                        
                        # Verifica se é algum CNAE de educação
                        if any(cnae_val in str(cnae) for cnae_val in EducacaoSearcher.CNAES_EDUCACAO):
                            
                            cnpj = empresa.get('cnpj', '').replace('.', '').replace('/', '').replace('-', '')
                            
                            lead = {
                                'id': f"edu_{cnpj}",
                                'nome': empresa.get('razao_social', ''),
                                'fantasia': empresa.get('estabelecimento', {}).get('nome_fantasia'),
                                'cnpj': cnpj,
                                'cnae': cnae,
                                'telefone': EducacaoSearcher._extrair_telefone(empresa),
                                'email': empresa.get('estabelecimento', {}).get('email'),
                                'endereco': EducacaoSearcher._montar_endereco(empresa),
                                'cidade': cidade,
                                'estado': estado,
                                'fonte': 'Receita Federal (CNAE Educação)',
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
            
            # Para se já atingiu o limite
            if len(leads) >= limite:
                break
        
        logger.info(f"✅ {len(leads)} instituições de ensino encontradas")
        
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