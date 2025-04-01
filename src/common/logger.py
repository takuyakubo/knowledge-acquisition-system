import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 基本設定
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = os.path.join(BASE_DIR, "logs")

def setup_logger(name, log_file=None, level=logging.INFO):
    """ロガーのセットアップ関数

    Args:
        name (str): ロガー名
        log_file (str, optional): ログファイルパス. デフォルトはNone.
        level (int, optional): ログレベル. デフォルトはINFO.

    Returns:
        logging.Logger: 設定済みロガーオブジェクト
    """
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # ハンドラがすでに存在する場合は追加しない
    if not logger.handlers:
        # コンソールハンドラ
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # ファイルハンドラ（指定時のみ）
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger

def get_logger(name):
    """モジュール用のロガーを取得する

    Args:
        name (str): モジュール名

    Returns:
        logging.Logger: 設定済みロガーオブジェクト
    """
    # ログディレクトリを作成
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # モジュールごとのログファイルパスを構築
    module_name = name.split('.')[-1]
    log_file = os.path.join(LOG_DIR, f"{module_name}.log")
    
    # ロガーを設定して返す
    return setup_logger(name, log_file)

# デフォルトロガー
default_logger = setup_logger('knowledge_acquisition')