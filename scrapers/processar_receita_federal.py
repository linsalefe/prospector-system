# scrapers/processar_receita_federal.py
import zipfile
import pandas as pd
import os
import logging
from typing import List

logger = logging.getLogger(__name__)

class ProcessadorReceitaFederal:
    """
    Processa arquivos da Receita Federal e filtra por CNAE
    """
    
    # CNAEs de Educação
    CNAES_EDUCACAO = [
        '8511200',  # Educação infantil - creche
        '8512100',  # Educação infantil - pré-escola
        '8513900',  # Ensino fundamental
        '8520100',  # Ensino médio
        '8531700',  # Educação superior - graduação
        '8532500',  # Educação superior - graduação e pós
        '8533300',  # Educação superior - pós-graduação
        '8541400',  # Educação profissional técnico
        '8542200',  # Educação profissional tecnológico
        '8592900',  # Ensino de idiomas
        '8593700',  # Ensino de música
        '8599600',  # Outras atividades de ensino
    ]
    
    # Colunas dos arquivos Estabelecimentos
    COLUNAS = [
        'cnpj_basico',
        'cnpj_ordem',
        'cnpj_dv',
        'identificador_matriz_filial',
        'nome_fantasia',
        'situacao_cadastral',
        'data_situacao_cadastral',
        'motivo_situacao_cadastral',
        'nome_cidade_exterior',
        'pais',
        'data_inicio_atividade',
        'cnae_fiscal_principal',
        'cnae_fiscal_secundaria',
        'tipo_logradouro',
        'logradouro',
        'numero',
        'complemento',
        'bairro',
        'cep',
        'uf',
        'municipio',
        'ddd_1',
        'telefone_1',
        'ddd_2',
        'telefone_2',
        'ddd_fax',
        'fax',
        'correio_eletronico',
        'situacao_especial',
        'data_situacao_especial'
    ]
    
    @staticmethod
    def processar_estabelecimentos(
        pasta_receita: str,
        output_file: str = 'empresas_educacao.csv'
    ) -> pd.DataFrame:
        """
        Processa todos os arquivos Estabelecimentos e filtra por CNAE educação
        """
        
        logger.info("🏢 Processando base da Receita Federal...")
        logger.info(f"📁 Pasta: {pasta_receita}")
        
        all_empresas = []
        
        # Lista arquivos ZIP de Estabelecimentos
        arquivos = [f for f in os.listdir(pasta_receita) 
                   if f.startswith('Estabelecimentos') and f.endswith('.zip')]
        
        arquivos.sort()
        
        logger.info(f"📦 {len(arquivos)} arquivos encontrados")
        
        for idx, arquivo in enumerate(arquivos, 1):
            logger.info(f"\n[{idx}/{len(arquivos)}] Processando {arquivo}...")
            
            caminho_zip = os.path.join(pasta_receita, arquivo)
            
            try:
                with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
                    # Lista arquivos dentro do ZIP
                    csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv') or f.endswith('.CSV')]
                    
                    for csv_file in csv_files:
                        logger.info(f"  📄 Lendo {csv_file}...")
                        
                        # Lê CSV
                        with zip_ref.open(csv_file) as f:
                            df = pd.read_csv(
                                f,
                                sep=';',
                                encoding='latin1',
                                names=ProcessadorReceitaFederal.COLUNAS,
                                dtype=str,
                                low_memory=False
                            )
                            
                            # Filtra por CNAE educação
                            df_educacao = df[
                                df['cnae_fiscal_principal'].isin(ProcessadorReceitaFederal.CNAES_EDUCACAO)
                            ]
                            
                            logger.info(f"    ✅ {len(df_educacao)} empresas de educação encontradas")
                            
                            if len(df_educacao) > 0:
                                all_empresas.append(df_educacao)
            
            except Exception as e:
                logger.error(f"  ❌ Erro ao processar {arquivo}: {e}")
        
        # Concatena todos os DataFrames
        if all_empresas:
            df_final = pd.concat(all_empresas, ignore_index=True)
            
            # Remove duplicatas
            df_final = df_final.drop_duplicates(subset=['cnpj_basico', 'cnpj_ordem', 'cnpj_dv'])
            
            # Formata CNPJ
            df_final['cnpj'] = (
                df_final['cnpj_basico'] + 
                df_final['cnpj_ordem'] + 
                df_final['cnpj_dv']
            )
            
            # Formata telefone
            df_final['telefone'] = df_final.apply(
                lambda x: f"55{x['ddd_1']}{x['telefone_1']}" 
                if pd.notna(x['ddd_1']) and pd.notna(x['telefone_1']) 
                else None,
                axis=1
            )
            
            # Filtra apenas ativos
            df_final = df_final[df_final['situacao_cadastral'] == '02']
            
            logger.info(f"\n✅ TOTAL: {len(df_final)} empresas de educação ativas no Brasil")
            
            # Salva CSV
            df_final.to_csv(output_file, index=False, encoding='utf-8-sig')
            logger.info(f"💾 Salvo em: {output_file}")
            
            return df_final
        
        else:
            logger.warning("❌ Nenhuma empresa de educação encontrada")
            return pd.DataFrame()