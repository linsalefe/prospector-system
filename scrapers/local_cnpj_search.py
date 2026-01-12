# scrapers/local_cnpj_search.py
import sqlite3, re
from pathlib import Path
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)

DB = Path("data/cnpj.db")

class LocalCNPJSearch:
    
    @staticmethod
    def cnpj_dv(cnpj12: str) -> str:
        """Calcula dígitos verificadores"""
        pesos1 = [5,4,3,2,9,8,7,6,5,4,3,2]
        pesos2 = [6] + pesos1
        
        def calc(nums, pesos):
            s = sum(int(n) * p for n, p in zip(nums, pesos))
            r = s % 11
            return "0" if r < 2 else str(11 - r)
        
        dv1 = calc(cnpj12, pesos1)
        dv2 = calc(cnpj12 + dv1, pesos2)
        return dv1 + dv2
    
    @staticmethod
    def cnpj_matriz_from_basico(cnpj_basico: str) -> str:
        """Gera CNPJ completo (14 dígitos) da matriz"""
        base = re.sub(r"\D", "", cnpj_basico or "").zfill(8)
        ordem = "0001"
        return base + ordem + LocalCNPJSearch.cnpj_dv(base + ordem)
    
    @staticmethod
    def buscar_estabelecimento(cnpj_basico: str):
        """Busca dados do estabelecimento matriz por CNPJ básico"""
        
        if not DB.exists():
            return None
        
        conn = sqlite3.connect(DB.as_posix())
        cur = conn.cursor()
        
        logger.info(f"  🔍 Buscando estabelecimento: CNPJ básico {cnpj_basico}")
        
        # Busca estabelecimento matriz (cnpj_ordem = '0001')
        cur.execute("""
            SELECT ddd_1, telefone_1, ddd_2, telefone_2, email, uf, municipio
            FROM estabelecimentos
            WHERE cnpj_basico = ? AND cnpj_ordem = '0001'
            LIMIT 1
        """, (cnpj_basico,))
        
        row = cur.fetchone()
        
        if not row:
            logger.warning(f"  ⚠️ Estabelecimento não encontrado para CNPJ básico {cnpj_basico}")
            # Tenta buscar qualquer estabelecimento desse CNPJ
            cur.execute("""
                SELECT ddd_1, telefone_1, ddd_2, telefone_2, email, uf, municipio
                FROM estabelecimentos
                WHERE cnpj_basico = ?
                LIMIT 1
            """, (cnpj_basico,))
            row = cur.fetchone()
        
        conn.close()
        
        if row:
            ddd1, tel1, ddd2, tel2, email, uf, municipio = row
            
            logger.info(f"  📊 Dados encontrados - DDD1: {ddd1}, Tel1: {tel1}, Email: {email}")
            
            # Monta telefone completo
            telefone = None
            if ddd1 and tel1:
                telefone = f"55{ddd1}{tel1}".replace(' ', '').replace('-', '')
            elif ddd2 and tel2:
                telefone = f"55{ddd2}{tel2}".replace(' ', '').replace('-', '')
            
            return {
                'telefone': telefone,
                'email': email,
                'uf': uf,
                'municipio': municipio
            }
        
        logger.warning(f"  ⚠️ Nenhum estabelecimento encontrado")
        return None
    
    @staticmethod
    def search(nome: str, limit=10):
        """Busca empresas por nome"""
        
        if not DB.exists():
            logger.warning(f"⚠️ Banco de CNPJs não encontrado: {DB}")
            return []
        
        conn = sqlite3.connect(DB.as_posix())
        cur = conn.cursor()
        
        # FTS5 match
        q = " ".join(nome.upper().split())
        cur.execute("""
            SELECT cnpj_basico, razao_social
            FROM empresas_fts
            WHERE empresas_fts MATCH ?
            LIMIT ?
        """, (q, limit))
        
        rows = cur.fetchall()
        conn.close()
        
        return [{"cnpj_basico": b, "cnpj": LocalCNPJSearch.cnpj_matriz_from_basico(b), "razao_social": r} for b, r in rows]
    
    @staticmethod
    def melhor_match(nome_empresa: str):
        """Encontra o melhor match por similaridade + dados completos"""
        
        candidatos = LocalCNPJSearch.search(nome_empresa, limit=20)
        
        if not candidatos:
            return None
        
        melhor = None
        melhor_score = 0.0
        
        for item in candidatos:
            razao = item['razao_social']
            score = SequenceMatcher(None, nome_empresa.upper(), razao.upper()).ratio()
            
            if score > melhor_score:
                melhor_score = score
                melhor = item
        
        if melhor_score < 0.6:  # Mínimo 60% similaridade
            return None
        
        melhor['score'] = round(melhor_score, 4)
        
        # Busca dados do estabelecimento (telefone, email)
        estab = LocalCNPJSearch.buscar_estabelecimento(melhor['cnpj_basico'])
        if estab:
            melhor['telefone'] = estab['telefone']
            melhor['email'] = estab['email']
            melhor['uf'] = estab['uf']
            melhor['municipio'] = estab['municipio']
        
        logger.info(f"  ✅ Match: {melhor['razao_social']} ({melhor_score*100:.1f}%)")
        if melhor.get('telefone'):
            logger.info(f"  📱 Telefone: {melhor['telefone']}")
        
        return melhor