import os, re, csv, sqlite3, zipfile
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = Path("data/cnpj.db")
DATA_DIR = Path("data/receita")

def normalize(s: str) -> str:
    """Normaliza texto para busca"""
    s = (s or "").upper().strip()
    s = re.sub(r"\s+", " ", s)
    return s

def cnpj_dv(cnpj12: str) -> str:
    """Calcula dígitos verificadores do CNPJ"""
    pesos1 = [5,4,3,2,9,8,7,6,5,4,3,2]
    pesos2 = [6] + pesos1

    def calc(nums, pesos):
        s = sum(int(n) * p for n, p in zip(nums, pesos))
        r = s % 11
        return "0" if r < 2 else str(11 - r)

    dv1 = calc(cnpj12, pesos1)
    dv2 = calc(cnpj12 + dv1, pesos2)
    return dv1 + dv2

def cnpj_completo(cnpj_basico: str, ordem: str, dv: str) -> str:
    """Monta CNPJ completo"""
    return cnpj_basico.zfill(8) + ordem.zfill(4) + dv.zfill(2)

def init_db(conn: sqlite3.Connection):
    """Inicializa banco de dados"""
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    
    # Tabela Empresas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            cnpj_basico TEXT PRIMARY KEY,
            razao_social TEXT,
            natureza_juridica TEXT,
            capital_social TEXT,
            porte TEXT
        );
    """)
    
    # Tabela Estabelecimentos (matriz/filiais com telefone)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS estabelecimentos (
            cnpj_completo TEXT PRIMARY KEY,
            cnpj_basico TEXT,
            cnpj_ordem TEXT,
            cnpj_dv TEXT,
            matriz_filial TEXT,
            nome_fantasia TEXT,
            situacao_cadastral TEXT,
            data_situacao_cadastral TEXT,
            tipo_logradouro TEXT,
            logradouro TEXT,
            numero TEXT,
            complemento TEXT,
            bairro TEXT,
            cep TEXT,
            uf TEXT,
            municipio TEXT,
            ddd_1 TEXT,
            telefone_1 TEXT,
            ddd_2 TEXT,
            telefone_2 TEXT,
            email TEXT
        );
    """)
    
    # Índice de busca para empresas (FTS5)
    cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS empresas_fts USING fts5(
            cnpj_basico,
            razao_social,
            content='empresas'
        );
    """)
    
    # Índice para buscar estabelecimentos por CNPJ básico
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_estab_cnpj_basico 
        ON estabelecimentos(cnpj_basico);
    """)
    
    conn.commit()
    logger.info("✅ Banco inicializado")

def upsert_empresa(conn, row):
    """Insere ou atualiza empresa"""
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO empresas
        (cnpj_basico, razao_social, natureza_juridica, capital_social, porte)
        VALUES (?, ?, ?, ?, ?)
    """, row)

def upsert_estabelecimento(conn, row):
    """Insere ou atualiza estabelecimento"""
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO estabelecimentos
        (cnpj_completo, cnpj_basico, cnpj_ordem, cnpj_dv, matriz_filial, nome_fantasia,
         situacao_cadastral, data_situacao_cadastral, tipo_logradouro, logradouro, numero,
         complemento, bairro, cep, uf, municipio, ddd_1, telefone_1, ddd_2, telefone_2, email)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, row)

def rebuild_fts(conn):
    """Reconstrói índice de busca"""
    cur = conn.cursor()
    cur.execute("INSERT INTO empresas_fts(empresas_fts) VALUES('rebuild');")
    conn.commit()
    logger.info("✅ Índice de busca reconstruído")

def import_empresas_zip(conn, zip_path: Path):
    """Importa dados de Empresas"""
    logger.info(f"📦 Processando {zip_path.name}...")
    
    with zipfile.ZipFile(zip_path, "r") as z:
        csv_files = [n for n in z.namelist() if any(ext in n.lower() for ext in ['.csv', '.emprecsv', '.txt'])]
        
        if not csv_files:
            logger.error(f"❌ Nenhum arquivo de dados encontrado!")
            return
        
        name = csv_files[0]
        
        with z.open(name) as f:
            text = (line.decode("latin1", errors="ignore") for line in f)
            reader = csv.reader(text, delimiter=";")
            
            count = 0
            for cols in reader:
                cnpj_basico = cols[0]
                razao = normalize(cols[1])
                natureza = cols[2] if len(cols) > 2 else ""
                capital = cols[4] if len(cols) > 4 else ""
                porte = cols[5] if len(cols) > 5 else ""
                
                upsert_empresa(conn, (cnpj_basico, razao, natureza, capital, porte))
                
                count += 1
                if count % 50000 == 0:
                    conn.commit()
                    logger.info(f"  {count:,} empresas processadas...")
            
            conn.commit()
            logger.info(f"✅ {zip_path.name}: {count:,} empresas importadas")

def import_estabelecimentos_zip(conn, zip_path: Path):
    """Importa dados de Estabelecimentos"""
    logger.info(f"📦 Processando {zip_path.name}...")
    
    with zipfile.ZipFile(zip_path, "r") as z:
        # Pega qualquer arquivo (ignora diretórios)
        files = [n for n in z.namelist() if not n.endswith('/')]
        
        if not files:
            logger.error(f"❌ Nenhum arquivo encontrado!")
            return
        
        name = files[0]
        logger.info(f"📄 Processando arquivo: {name}")
        
        with z.open(name) as f:
            text = (line.decode("latin1", errors="ignore") for line in f)
            reader = csv.reader(text, delimiter=";")
            
            count = 0
            for cols in reader:
                if len(cols) < 20:
                    continue
                
                cnpj_basico = cols[0]
                cnpj_ordem = cols[1]
                cnpj_dv = cols[2]
                cnpj_completo_str = cnpj_completo(cnpj_basico, cnpj_ordem, cnpj_dv)
                
                matriz_filial = cols[3]  # 1=Matriz, 2=Filial
                nome_fantasia = normalize(cols[4])
                situacao = cols[5]
                data_situacao = cols[6]
                
                tipo_logradouro = cols[13] if len(cols) > 13 else ""
                logradouro = cols[14] if len(cols) > 14 else ""
                numero = cols[15] if len(cols) > 15 else ""
                complemento = cols[16] if len(cols) > 16 else ""
                bairro = cols[17] if len(cols) > 17 else ""
                cep = cols[18] if len(cols) > 18 else ""
                uf = cols[19] if len(cols) > 19 else ""
                municipio = cols[20] if len(cols) > 20 else ""
                
                ddd_1 = cols[21] if len(cols) > 21 else ""
                telefone_1 = cols[22] if len(cols) > 22 else ""
                ddd_2 = cols[23] if len(cols) > 23 else ""
                telefone_2 = cols[24] if len(cols) > 24 else ""
                email = cols[26] if len(cols) > 26 else ""
                
                upsert_estabelecimento(conn, (
                    cnpj_completo_str, cnpj_basico, cnpj_ordem, cnpj_dv, matriz_filial,
                    nome_fantasia, situacao, data_situacao, tipo_logradouro, logradouro,
                    numero, complemento, bairro, cep, uf, municipio, ddd_1, telefone_1,
                    ddd_2, telefone_2, email
                ))
                
                count += 1
                if count % 50000 == 0:
                    conn.commit()
                    logger.info(f"  {count:,} estabelecimentos processados...")
            
            conn.commit()
            logger.info(f"✅ {zip_path.name}: {count:,} estabelecimentos importados")

def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("🚀 Criando/Atualizando banco de CNPJs...")
    
    conn = sqlite3.connect(DB_PATH.as_posix())
    init_db(conn)

    # Importa Empresas
    empresas_zips = sorted(DATA_DIR.glob("Empresas*.zip"))
    if empresas_zips:
        logger.info(f"📦 {len(empresas_zips)} arquivos de Empresas encontrados")
        for zp in empresas_zips:
            import_empresas_zip(conn, zp)
        rebuild_fts(conn)
    
    # Importa Estabelecimentos
    estab_zips = sorted(DATA_DIR.glob("Estabelecimentos*.zip"))
    if estab_zips:
        logger.info(f"📦 {len(estab_zips)} arquivos de Estabelecimentos encontrados")
        for zp in estab_zips:
            import_estabelecimentos_zip(conn, zp)
    
    # Estatísticas
    cur = conn.cursor()
    total_emp = cur.execute("SELECT COUNT(*) FROM empresas").fetchone()[0]
    total_estab = cur.execute("SELECT COUNT(*) FROM estabelecimentos").fetchone()[0]
    
    logger.info(f"✅ Banco atualizado:")
    logger.info(f"   Empresas: {total_emp:,}")
    logger.info(f"   Estabelecimentos: {total_estab:,}")
    logger.info(f"📍 Localização: {DB_PATH.absolute()}")
    
    conn.close()
    print("=== SCRIPT FINALIZADO ===")

if __name__ == "__main__":
    main()