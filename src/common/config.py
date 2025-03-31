import os
from pathlib import Path
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

# 基本設定
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = os.path.join(BASE_DIR, "logs")
DATA_DIR = os.path.join(BASE_DIR, "data")

# APIサーバー設定
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
ENV = os.getenv("ENV", "development")

# データベース設定
DB_TYPE = os.getenv("DB_TYPE", "sqlite")
DB_PATH = os.getenv("DB_PATH", os.path.join(DATA_DIR, "knowledge.db"))

# ベクトルデータベース設定
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "faiss")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", os.path.join(DATA_DIR, "vector_store"))

# LLM設定
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

# 初期化関数
def init_directories():
    """必要なディレクトリを作成する"""
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(VECTOR_DB_PATH, exist_ok=True)