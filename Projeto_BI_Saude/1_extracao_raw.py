"""
1_extracao_raw.py
=================
FASE 1: Extração e Carga Raw (substitui o Pentaho — ETL em código)

Pipeline:
    API Kaggle (Parquet) → PostgreSQL (schema: public, tabelas: raw_*)

Autenticação:
    As credenciais são lidas do arquivo .env (ignorado pelo .gitignore).
    A Kaggle API aceita KAGGLE_USERNAME e KAGGLE_KEY como variáveis de ambiente.

Como rodar:
    1. Preencha o arquivo .env com suas credenciais
    2. pip install -r requirements.txt
    3. python 1_extracao_raw.py
"""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from kaggle.api.kaggle_api_extended import KaggleApi

# ============================================================
# 0. CARREGAMENTO DE CREDENCIAIS
# ============================================================
ENV_FILE = Path(__file__).resolve().with_name(".env")
if not ENV_FILE.is_file():
    raise FileNotFoundError(f"Arquivo de credenciais não encontrado: {ENV_FILE}")

load_dotenv(dotenv_path=ENV_FILE, override=True)

variaveis_obrigatorias = ["KAGGLE_USERNAME", "KAGGLE_API_TOKEN", "DB_USER", "DB_PASS", "DB_NAME"]
for var in variaveis_obrigatorias:
    if not os.getenv(var):
        raise EnvironmentError(f"A variável '{var}' não foi encontrada no arquivo .env.")

print("✅ Credenciais carregadas com sucesso do arquivo .env")

# Autentica um cliente criado após carregar o .env, garantindo que ele use
# KAGGLE_USERNAME e KAGGLE_API_TOKEN definidos nesse arquivo.
kaggle_api = KaggleApi()
kaggle_api.authenticate()
print("✅ Autenticação com a API do Kaggle estabelecida com sucesso!")

# ============================================================
# 1. CONEXÃO COM O POSTGRESQL
# ============================================================
DB_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}"
    f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}"
    f"/{os.getenv('DB_NAME')}"
)
engine = create_engine(DB_URL)

try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ Conexão com PostgreSQL estabelecida com sucesso!")
except Exception as e:
    raise ConnectionError(f"Não foi possível conectar ao PostgreSQL: {e}")

# ============================================================
# 2. CONFIGURAÇÃO DO DOWNLOAD
# ============================================================
DATASET = "rafatrindade/brazilian-kaggle-datahub"
DOWNLOAD_PATH = "./dados_brutos"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# Mapeamento: nome_da_tabela_no_postgres → nome_do_arquivo_no_kaggle
ARQUIVOS = {
    "raw_municipios":    "municipios.parquet",
    "raw_populacao":     "populacao.parquet",
    "raw_pib":           "pib.parquet",
    "raw_leitos":        "cnes_leitos.parquet",
    "raw_profissionais": "cnes_profissionais.parquet",
}

# ============================================================
# 3. LOOP DE EXTRAÇÃO E CARGA (RAW)
# ============================================================
print("\n=== FASE 1: EXTRAÇÃO E CARGA RAW ===\n")

for tabela, arquivo in ARQUIVOS.items():
    print(f"{'='*60}")
    print(f"[{list(ARQUIVOS.keys()).index(tabela)+1}/{len(ARQUIVOS)}] Processando: {arquivo}")
    print(f"{'='*60}")

    caminho_arquivo = os.path.join(DOWNLOAD_PATH, arquivo)
    if os.path.exists(caminho_arquivo):
        print(f"  ⚡ Arquivo já existe localmente. Pulando download.")
    else:
        print(f"  📥 Baixando {arquivo} da API do Kaggle...")
        kaggle_api.dataset_download_file(
            dataset=DATASET,
            file_name=arquivo,
            path=DOWNLOAD_PATH,
            quiet=False
        )
        if not os.path.isfile(caminho_arquivo):
            raise FileNotFoundError(
                f"A API do Kaggle não criou o arquivo esperado: {caminho_arquivo}"
            )
        print(f"  ✅ Download concluído!")

    print(f"  📖 Lendo o arquivo Parquet...")
    df = pd.read_parquet(caminho_arquivo)

    print(f"\n  📊 AUDITORIA DOS DADOS RAW:")
    print(f"     Shape:   {df.shape[0]:,} linhas × {df.shape[1]} colunas")
    
    nulos = df.isnull().sum()
    nulos_relevantes = nulos[nulos > 0]
    if len(nulos_relevantes) > 0:
        print(f"     ⚠️  Colunas com nulos encontradas.")
    else:
        print(f"     ✅ Nenhum valor nulo encontrado!")

    print(f"\n  💾 Carregando no PostgreSQL (tabela: public.{tabela})...")
    df.to_sql(
        name=tabela,
        con=engine,
        if_exists="replace",
        index=False,
        schema="public",
        chunksize=10_000
    )
    print(f"  ✅ {tabela} carregada! ({df.shape[0]:,} registros)\n")

print("\n🎉 FASE 1 CONCLUÍDA — Dados brutos disponíveis no PostgreSQL!")
