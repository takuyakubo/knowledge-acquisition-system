"""
コネクタファクトリーのテスト

このモジュールは、データ収集用のコネクタファクトリーの機能をテストします。
"""

import pytest
from unittest.mock import patch, MagicMock

from src.data_collection.factory import ConnectorFactory
from src.data_collection.arxiv.connector import ArxivConnector
from src.knowledge_extraction.entity_model import SourceType


class TestConnectorFactory:
    """コネクタファクトリーのテストケース"""
    
    @pytest.fixture
    def factory(self):
        """テスト用のファクトリーインスタンスを提供"""
        # DB接続やその他の依存関係をモック化
        db_mock = MagicMock()
        vector_db_mock = MagicMock()
        storage_mock = MagicMock()
        
        # ファクトリーを作成
        factory = ConnectorFactory(
            db_connection=db_mock,
            vector_db_client=vector_db_mock,
            file_storage=storage_mock
        )
        return factory
    
    def test_get_connector_arxiv(self, factory):
        """arXivコネクタの取得をテスト"""
        # ArxivConnectorクラスのインスタンス化をパッチ
        with patch('src.data_collection.factory.ArxivConnector') as mock_arxiv:
            # モックコネクタを作成
            mock_connector = MagicMock()
            mock_arxiv.return_value = mock_connector
            
            # ファクトリーからコネクタを取得
            connector = factory.get_connector(SourceType.ARXIV)
            
            # 結果を検証
            assert connector == mock_connector
            mock_arxiv.assert_called_once()
    
    def test_get_connector_unknown_source(self, factory):
        """未知のソースタイプでの例外発生をテスト"""
        # 存在しないソースタイプに対してValueErrorが発生することを検証
        with pytest.raises(ValueError) as excinfo:
            factory.get_connector("unknown_source_type")
        
        # エラーメッセージを検証
        assert "Unsupported source type" in str(excinfo.value)
    
    def test_create_connector_with_config(self, factory):
        """設定付きでコネクタを作成するテスト"""
        # 設定付きでArxivConnectorをパッチ
        with patch('src.data_collection.factory.ArxivConnector') as mock_arxiv:
            # モックコネクタを作成
            mock_connector = MagicMock()
            mock_arxiv.return_value = mock_connector
            
            # カスタム設定
            custom_config = {
                "api_key": "test_key",
                "max_results": 50,
                "request_delay": 2
            }
            
            # ファクトリーからコネクタを取得（設定付き）
            connector = factory.get_connector(SourceType.ARXIV, config=custom_config)
            
            # 結果を検証
            assert connector == mock_connector
            # コネクタインスタンス作成時に設定が渡されることを確認
            mock_arxiv.assert_called_once()
            
            # モックコネクタの設定が正しく適用されることを確認
            mock_connector.configure.assert_called_once_with(custom_config)
    
    def test_register_and_get_custom_connector(self, factory):
        """カスタムコネクタの登録と取得をテスト"""
        # カスタムソースタイプとコネクタクラス
        custom_source_type = "CUSTOM_SOURCE"
        mock_connector_class = MagicMock()
        mock_connector_instance = MagicMock()
        mock_connector_class.return_value = mock_connector_instance
        
        # カスタムコネクタを登録
        factory.register_connector(custom_source_type, mock_connector_class)
        
        # 登録したコネクタを取得
        connector = factory.get_connector(custom_source_type)
        
        # 結果を検証
        assert connector == mock_connector_instance
        mock_connector_class.assert_called_once()
        
        # 登録されているコネクタタイプを確認
        assert custom_source_type in factory.get_available_connectors()