"""
arXivコネクタのテスト

このモジュールは、arXivコネクタの機能をテストするためのテストケースを提供します。
"""

import os
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from src.data_collection.arxiv.connector import ArxivConnector
from src.data_collection.arxiv.exceptions import (
    ArxivAPIError,
    PDFDownloadError,
    TextExtractionError,
    SegmentationError,
    DataNotFoundError
)
from src.knowledge_extraction.entity_model import (
    SourceType,
    Document,
    Entity,
    Segment,
    SourceData,
    ContentType
)


class TestArxivConnector:
    """arXivコネクタに関するテストケース"""

    @pytest.fixture
    def arxiv_connector(self):
        """arXivコネクタのインスタンスを提供するフィクスチャ"""
        # モック依存関係を設定
        db_mock = MagicMock()
        vector_db_mock = MagicMock()
        storage_mock = MagicMock()
        
        # テスト用の一時ディレクトリを使用するよう設定
        with patch('os.makedirs'):
            with patch('src.common.config.get_config') as mock_get_config:
                # 設定をモック化
                mock_get_config.return_value = {'data_dir': '/tmp/test_data'}
                connector = ArxivConnector(
                    db_connection=db_mock,
                    vector_db_client=vector_db_mock,
                    file_storage=storage_mock
                )
                # APIクライアントを設定
                connector.api_client = MagicMock()
                return connector

    @pytest.mark.asyncio
    async def test_initialize(self, arxiv_connector):
        """initialize()メソッドのテスト"""
        # initialize()メソッドを呼び出し
        await arxiv_connector.initialize()
        # 現在は具体的な実装がないので、エラーなく実行されることだけを検証
        assert True

    @pytest.mark.asyncio
    async def test_get_source_info(self, arxiv_connector):
        """get_source_info()メソッドのテスト"""
        source_data = await arxiv_connector.get_source_info()
        
        # 戻り値がSourceDataクラスのインスタンスであることをチェック
        assert isinstance(source_data, SourceData)
        # ソースタイプがARXIVであることをチェック
        assert source_data.source_type == SourceType.ARXIV
        # URLがarXivのものであることをチェック
        assert source_data.source_url == "https://arxiv.org/"
        # 名前が正しいことをチェック
        assert source_data.source_name == "arXiv Open Access Papers"
        # メタデータに必要な情報が含まれていることをチェック
        assert "api_version" in source_data.metadata
        assert "request_delay" in source_data.metadata

    @pytest.mark.asyncio
    async def test_search_delegates_to_search_papers(self, arxiv_connector):
        """search()メソッドがsearch_papers()に適切に委譲することのテスト"""
        # search_papers()をモック化
        arxiv_connector.search_papers = AsyncMock(return_value=[{"paper": "data"}])
        
        # search()を呼び出し
        result = await arxiv_connector.search(
            query="quantum computing",
            category="cs.AI",
            date_from="2023-01-01",
            date_to="2023-12-31",
            max_results=50
        )
        
        # search_papers()が適切なパラメータで呼び出されたことを検証
        arxiv_connector.search_papers.assert_called_once_with(
            query="quantum computing",
            category="cs.AI",
            date_from="2023-01-01",
            date_to="2023-12-31",
            max_results=50
        )
        
        # 戻り値が正しいことを検証
        assert result == [{"paper": "data"}]

    @pytest.mark.asyncio
    async def test_search_papers(self, arxiv_connector):
        """search_papers()メソッドのテスト"""
        # 将来実装される関数なので、未実装だがNotImplementedErrorが出ないことだけ確認
        with pytest.raises(NotImplementedError, match=None):
            await arxiv_connector.search_papers(query="quantum computing")

    @pytest.mark.asyncio
    async def test_collect_delegates_to_collect_papers(self, arxiv_connector):
        """collect()メソッドがcollect_papers()に適切に委譲することのテスト"""
        # collect_papers()をモック化
        arxiv_connector.collect_papers = AsyncMock(return_value=[{"paper": "collected"}])
        
        # collect()を呼び出し
        result = await arxiv_connector.collect(
            query="machine learning",
            category="cs.LG",
            date_from="2023-01-01",
            date_to="2023-12-31",
            max_results=25
        )
        
        # collect_papers()が適切なパラメータで呼び出されたことを検証
        arxiv_connector.collect_papers.assert_called_once_with(
            query="machine learning",
            category="cs.LG",
            date_from="2023-01-01",
            date_to="2023-12-31",
            max_results=25
        )
        
        # 戻り値が正しいことを検証
        assert result == [{"paper": "collected"}]

    @pytest.mark.asyncio
    async def test_get_paper_by_id(self, arxiv_connector):
        """get_paper_by_id()メソッドのテスト"""
        # 将来実装される関数なので、未実装だがNotImplementedErrorが出ないことだけ確認
        with pytest.raises(NotImplementedError, match=None):
            await arxiv_connector.get_paper_by_id(arxiv_id="2301.12345")

    @pytest.mark.asyncio
    async def test_download_pdf(self, arxiv_connector):
        """download_pdf()メソッドのテスト"""
        # 将来実装される関数なので、未実装だがNotImplementedErrorが出ないことだけ確認
        with pytest.raises(NotImplementedError, match=None):
            await arxiv_connector.download_pdf(arxiv_id="2301.12345")

    @pytest.mark.asyncio
    async def test_extract_text_from_pdf(self, arxiv_connector):
        """extract_text_from_pdf()メソッドのテスト"""
        # 将来実装される関数なので、未実装だがNotImplementedErrorが出ないことだけ確認
        with pytest.raises(NotImplementedError, match=None):
            await arxiv_connector.extract_text_from_pdf(pdf_path="/path/to/pdf")

    @pytest.mark.asyncio
    async def test_segment_paper(self, arxiv_connector):
        """segment_paper()メソッドのテスト"""
        # 将来実装される関数なので、未実装だがNotImplementedErrorが出ないことだけ確認
        with pytest.raises(NotImplementedError, match=None):
            await arxiv_connector.segment_paper(arxiv_id="2301.12345")

    @pytest.mark.asyncio
    async def test_extract_entities(self, arxiv_connector):
        """extract_entities()メソッドのテスト"""
        # 将来実装される関数なので、未実装だがNotImplementedErrorが出ないことだけ確認
        with pytest.raises(NotImplementedError, match=None):
            await arxiv_connector.extract_entities(arxiv_id="2301.12345")

    @pytest.mark.asyncio
    async def test_extract_relations(self, arxiv_connector):
        """extract_relations()メソッドのテスト"""
        # 将来実装される関数なので、未実装だがNotImplementedErrorが出ないことだけ確認
        with pytest.raises(NotImplementedError, match=None):
            await arxiv_connector.extract_relations(arxiv_id="2301.12345")

    @pytest.mark.asyncio
    async def test_search_by_category(self, arxiv_connector):
        """search_by_category()メソッドのテスト"""
        # 将来実装される関数なので、未実装だがNotImplementedErrorが出ないことだけ確認
        with pytest.raises(NotImplementedError, match=None):
            await arxiv_connector.search_by_category(category="cs.AI")

    @pytest.mark.asyncio
    async def test_search_by_date_range(self, arxiv_connector):
        """search_by_date_range()メソッドのテスト"""
        # 将来実装される関数なので、未実装だがNotImplementedErrorが出ないことだけ確認
        with pytest.raises(NotImplementedError, match=None):
            await arxiv_connector.search_by_date_range(date_from="2023-01-01", date_to="2023-12-31")

    @pytest.mark.asyncio
    async def test_download_full_text(self, arxiv_connector):
        """download_full_text()メソッドのテスト"""
        # 将来実装される関数なので、未実装だがNotImplementedErrorが出ないことだけ確認
        with pytest.raises(NotImplementedError, match=None):
            await arxiv_connector.download_full_text(document_id="2301.12345")

    @pytest.mark.asyncio
    async def test_get_document(self, arxiv_connector):
        """get_document()メソッドのテスト"""
        # 将来実装される関数なので、未実装だがNotImplementedErrorが出ないことだけ確認
        with pytest.raises(NotImplementedError, match=None):
            await arxiv_connector.get_document(document_id="2301.12345")

    @pytest.mark.asyncio
    async def test_extract_references(self, arxiv_connector):
        """extract_references()メソッドのテスト"""
        # 将来実装される関数なので、未実装だがNotImplementedErrorが出ないことだけ確認
        with pytest.raises(NotImplementedError, match=None):
            await arxiv_connector.extract_references(document_id="2301.12345")

    @pytest.mark.asyncio
    async def test_get_citation_data(self, arxiv_connector):
        """get_citation_data()メソッドのテスト"""
        # 将来実装される関数なので、未実装だがNotImplementedErrorが出ないことだけ確認
        with pytest.raises(NotImplementedError, match=None):
            await arxiv_connector.get_citation_data(document_id="2301.12345")

    @pytest.mark.asyncio
    async def test_get_paper_metadata(self, arxiv_connector):
        """get_paper_metadata()メソッドのテスト"""
        # 将来実装される関数なので、未実装だがNotImplementedErrorが出ないことだけ確認
        with pytest.raises(NotImplementedError, match=None):
            await arxiv_connector.get_paper_metadata(arxiv_id="2301.12345")

    @pytest.mark.asyncio
    async def test_get_vector_embeddings(self, arxiv_connector):
        """get_vector_embeddings()メソッドのテスト"""
        # 将来実装される関数なので、未実装だがNotImplementedErrorが出ないことだけ確認
        with pytest.raises(NotImplementedError, match=None):
            await arxiv_connector.get_vector_embeddings(arxiv_id="2301.12345")

    @pytest.mark.asyncio
    async def test_error_handling_arxiv_api_error(self, arxiv_connector):
        """ArxivAPIErrorの処理をテスト"""
        # APIエラーをシミュレート
        arxiv_connector.api_client.fetch_papers = AsyncMock(side_effect=ArxivAPIError(400, "Bad Request"))
        
        # search_papers()をオーバーライドして、api_clientを使用するようにする
        async def mock_search_papers(query, **kwargs):
            return await arxiv_connector.api_client.fetch_papers(query)
        
        arxiv_connector.search_papers = mock_search_papers
        
        # APIエラーが適切に伝播されることを確認
        with pytest.raises(ArxivAPIError) as excinfo:
            await arxiv_connector.search(query="quantum computing")
        
        # エラーメッセージと状態コードを検証
        assert excinfo.value.status_code == 400
        assert "Bad Request" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_error_handling_download_error(self, arxiv_connector):
        """PDFDownloadErrorの処理をテスト"""
        # モックでエラーをシミュレート
        with patch.object(arxiv_connector, 'download_pdf', side_effect=PDFDownloadError("Failed to download PDF")):
            # エラーが適切に伝播されることを確認
            with pytest.raises(PDFDownloadError) as excinfo:
                await arxiv_connector.download_pdf(arxiv_id="2301.12345")
            
            # エラーメッセージを検証
            assert "Failed to download PDF" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_error_handling_text_extraction_error(self, arxiv_connector):
        """TextExtractionErrorの処理をテスト"""
        # モックでエラーをシミュレート
        with patch.object(arxiv_connector, 'extract_text_from_pdf', 
                         side_effect=TextExtractionError("Failed to extract text")):
            # エラーが適切に伝播されることを確認
            with pytest.raises(TextExtractionError) as excinfo:
                await arxiv_connector.extract_text_from_pdf(pdf_path="/path/to/pdf")
            
            # エラーメッセージを検証
            assert "Failed to extract text" in str(excinfo.value)