"""
データコネクタファクトリー

このモジュールは、各種データソースのコネクタを生成するファクトリーを提供します。
設定情報に基づいて適切なコネクタインスタンスを生成します。
"""

from typing import Dict, Optional, Type, Union

from src.common.config import get_config
from src.common.logger import get_logger
from src.data_collection.arxiv.connector import ArxivConnector
from src.data_collection.interfaces import DataSourceConnector

logger = get_logger(__name__)
config = get_config()


class ConnectorFactory:
    """
    データソースコネクタのファクトリークラス
    
    設定情報に基づいて適切なコネクタインスタンスを生成します。
    """
    
    # 利用可能なコネクタクラスの登録
    _connectors: Dict[str, Type[DataSourceConnector]] = {
        "arxiv": ArxivConnector,
        # 他のコネクタを追加予定
    }
    
    @classmethod
    def get_connector(cls, 
                      source_type: str, 
                      db_connection=None, 
                      vector_db_client=None, 
                      file_storage=None) -> DataSourceConnector:
        """
        指定されたソースタイプのコネクタインスタンスを返す
        
        Args:
            source_type: ソースタイプ（例: "arxiv"）
            db_connection: データベース接続
            vector_db_client: ベクトルデータベースクライアント
            file_storage: ファイルストレージハンドラ
            
        Returns:
            コネクタインスタンス
            
        Raises:
            ValueError: 不明なソースタイプが指定された場合
        """
        connector_class = cls._connectors.get(source_type.lower())
        
        if not connector_class:
            available_types = ", ".join(cls._connectors.keys())
            raise ValueError(
                f"Unknown source type: {source_type}. "
                f"Available types: {available_types}"
            )
        
        # コネクタインスタンスを生成
        connector = connector_class(
            db_connection=db_connection,
            vector_db_client=vector_db_client,
            file_storage=file_storage
        )
        
        logger.info(f"Created connector of type {source_type}")
        return connector
    
    @classmethod
    def register_connector(cls, source_type: str, connector_class: Type[DataSourceConnector]) -> None:
        """
        新しいコネクタタイプを登録する
        
        Args:
            source_type: ソースタイプ識別子
            connector_class: データソースコネクタクラス
            
        Raises:
            TypeError: connector_classがDataSourceConnectorのサブクラスでない場合
        """
        if not issubclass(connector_class, DataSourceConnector):
            raise TypeError(
                f"Connector class must be a subclass of DataSourceConnector, "
                f"got {connector_class.__name__}"
            )
        
        cls._connectors[source_type.lower()] = connector_class
        logger.info(f"Registered new connector type: {source_type}")
    
    @classmethod
    def get_available_connectors(cls) -> Dict[str, Type[DataSourceConnector]]:
        """
        利用可能なコネクタタイプの辞書を返す
        
        Returns:
            ソースタイプとコネクタクラスのマッピング
        """
        return cls._connectors.copy()