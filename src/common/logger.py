import logging
import os
import sys
from logging.handlers import RotatingFileHandler

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

# デフォルトロガー
default_logger = setup_logger('knowledge_acquisition')