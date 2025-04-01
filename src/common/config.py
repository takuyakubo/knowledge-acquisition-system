import os
from pathlib import Path
from typing import Dict, Any
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

# 設定取得関数
def get_config() -> Dict[str, Any]:
    """設定情報を取得する

    Returns:
        Dict[str, Any]: 設定情報の辞書
    """
    return {
        "base_dir": str(BASE_DIR),
        "log_dir": LOG_DIR,
        "data_dir": DATA_DIR,
        "api_host": API_HOST,
        "api_port": API_PORT,
        "env": ENV,
        "db_type": DB_TYPE,
        "db_path": DB_PATH,
        "vector_db_type": VECTOR_DB_TYPE,
        "vector_db_path": VECTOR_DB_PATH,
        "llm_api_key": LLM_API_KEY,
        "llm_model": LLM_MODEL
    }

# 初期化関数
def init_directories():
    """必要なディレクトリを作成する"""
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(VECTOR_DB_PATH, exist_ok=True)