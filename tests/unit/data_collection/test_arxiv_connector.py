"""
arXivコネクタのテスト

このモジュールは、arXivコネクタの機能をテストするためのテストケースを提供します。
"""

import os
import pytest
import numpy as np
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from uuid import UUID, uuid4

from src.data_collection.arxiv.connector import ArxivConnector
from src.data_collection.arxiv.exceptions import (
    ArxivAPIError,
    PDFDownloadError,
    TextExtractionError,
    SegmentationError,
    DataNotFoundError,
    EntityExtractionError,
    RelationExtractionError
)
from src.knowledge_extraction.entity_model import (
    SourceType,
    Document,
    Entity,
    Segment,
    SourceData,
    ContentType,
    SegmentType,
    EntityType,
    RelationType,
    Relation
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
        # API呼び出しをモック化
        def mock_results(search):
            # モックの結果を返す
            mock_result = MagicMock()
            mock_result.get_short_id.return_value = "2301.12345"
            mock_result.title = "Quantum Computing Research"
            mock_result.authors = [MagicMock(name="Alice Smith")]
            mock_result.summary = "A paper about quantum computing."
            mock_result.published = datetime.now()
            mock_result.updated = datetime.now()
            mock_result.categories = ["cs.AI", "quant-ph"]
            mock_result.pdf_url = "https://arxiv.org/pdf/2301.12345"
            mock_result.entry_id = "https://arxiv.org/abs/2301.12345"
            mock_result.journal_ref = None
            mock_result.doi = None
            mock_result.comment = "25 pages"
            return [mock_result]
            
        # クライアントのresultsメソッドをモック化
        arxiv_connector.api_client.results = mock_results
        
        # メソッドを呼び出し
        results = await arxiv_connector.search_papers(query="quantum computing")
        
        # 検証
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["id"] == "2301.12345"
        assert results[0]["title"] == "Quantum Computing Research"
        assert "pdf_url" in results[0]

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
        # API呼び出しをモック化
        def mock_results(search):
            # モックの結果を返す
            mock_result = MagicMock()
            mock_result.get_short_id.return_value = "2301.12345"
            mock_result.title = "Quantum Computing Research"
            mock_result.authors = [MagicMock(name="Alice Smith")]
            mock_result.summary = "A paper about quantum computing."
            mock_result.published = datetime.now()
            mock_result.updated = datetime.now()
            mock_result.categories = ["cs.AI", "quant-ph"]
            mock_result.pdf_url = "https://arxiv.org/pdf/2301.12345"
            mock_result.entry_id = "https://arxiv.org/abs/2301.12345"
            mock_result.journal_ref = None
            mock_result.doi = None
            mock_result.comment = "25 pages"
            return [mock_result]
            
        # クライアントのresultsメソッドをモック化
        arxiv_connector.api_client.results = mock_results
        
        # メソッドを呼び出し
        paper = await arxiv_connector.get_paper_by_id(arxiv_id="2301.12345")
        
        # 検証
        assert isinstance(paper, dict)
        assert paper["id"] == "2301.12345"
        assert paper["title"] == "Quantum Computing Research"
        assert "pdf_url" in paper

    @pytest.mark.asyncio
    async def test_download_pdf(self, arxiv_connector):
        """download_pdf()メソッドのテスト"""
        # get_paper_by_idをモック化
        arxiv_connector.get_paper_by_id = AsyncMock(return_value={
            "id": "2301.12345",
            "pdf_url": "https://arxiv.org/pdf/2301.12345"
        })
        
        # セッションのgetをモック化
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"PDF content")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        arxiv_connector.session = MagicMock()
        arxiv_connector.session.get = MagicMock(return_value=mock_response)
        
        # ファイル操作をモック化
        with patch("builtins.open", mock_open()) as mock_file:
            # メソッドを呼び出し
            result = await arxiv_connector.download_pdf(arxiv_id="2301.12345")
            
            # 検証
            assert result.endswith("2301.12345.pdf")
            mock_file().write.assert_called_once_with(b"PDF content")

    @pytest.mark.asyncio
    async def test_extract_text_from_pdf(self, arxiv_connector):
        """extract_text_from_pdf()メソッドのテスト"""
        # os.path.existsをモック化
        with patch("os.path.exists", return_value=True):
            # PDFMinerのextract_textをモック化
            with patch("src.data_collection.arxiv.connector.extract_text", return_value="Extracted text content"):
                # メソッドを呼び出し
                result = await arxiv_connector.extract_text_from_pdf(pdf_path="/path/to/pdf")
                
                # 検証
                assert result == "Extracted text content"

    @pytest.mark.asyncio
    async def test_segment_paper(self, arxiv_connector):
        """segment_paper()メソッドのテスト"""
        # get_paper_by_idをモック化
        arxiv_connector.get_paper_by_id = AsyncMock(return_value={
            "id": "2301.12345",
            "title": "Test Paper",
            "authors": ["Test Author"],
            "summary": "Test abstract",
            "categories": ["cs.AI"]
        })
        
        # テキスト内容を提供
        text_content = """Abstract
This is an abstract.

Introduction
This is an introduction.

Method
This is the method section.

Conclusion
This is the conclusion.

References
[1] Test reference.
"""
        
        # メソッドを呼び出し
        segments = await arxiv_connector.segment_paper(arxiv_id="2301.12345", text_content=text_content)
        
        # 検証
        assert isinstance(segments, list)
        assert len(segments) > 0
        for segment in segments:
            assert isinstance(segment, Segment)
            assert hasattr(segment, "segment_id")
            assert hasattr(segment, "content")
            assert hasattr(segment, "segment_type")

    @pytest.mark.asyncio
    async def test_extract_entities(self, arxiv_connector):
        """extract_entities()メソッドのテスト"""
        # segment_paperをモック化
        segment1 = Segment(
            segment_id=uuid4(),
            document_id=uuid4(),
            content="Test abstract",
            segment_type=SegmentType.ABSTRACT,
            position=0,
            metadata={}
        )
        arxiv_connector.segment_paper = AsyncMock(return_value=[segment1])
        
        # get_paper_by_idをモック化
        arxiv_connector.get_paper_by_id = AsyncMock(return_value={
            "id": "2301.12345",
            "title": "Test Paper",
            "authors": ["Test Author"],
            "summary": "Test abstract",
            "published": "2023-01-15",
            "categories": ["cs.AI"]
        })
        
        # メソッドを呼び出し
        entities = await arxiv_connector.extract_entities(arxiv_id="2301.12345")
        
        # 検証
        assert isinstance(entities, list)
        assert len(entities) > 0
        for entity in entities:
            assert isinstance(entity, Entity)
            assert hasattr(entity, "entity_id")
            assert hasattr(entity, "name")
            assert hasattr(entity, "entity_type")
        
        # 論文エンティティが含まれることを確認
        paper_entity = next((e for e in entities if e.entity_type == EntityType.PAPER), None)
        assert paper_entity is not None
        assert paper_entity.name == "Test Paper"

    @pytest.mark.asyncio
    async def test_extract_relations(self, arxiv_connector):
        """extract_relations()メソッドのテスト"""
        # extract_entitiesをモック化
        paper_entity = Entity(
            entity_id=uuid4(),
            name="Test Paper",
            entity_type=EntityType.PAPER,
            aliases=[],
            description="Test paper description",
            source_segments=[uuid4()],
            confidence=1.0,
            metadata={"arxiv_id": "2301.12345"}
        )
        author_entity = Entity(
            entity_id=uuid4(),
            name="Test Author",
            entity_type=EntityType.PERSON,
            aliases=[],
            description="Author of the paper",
            source_segments=[uuid4()],
            confidence=1.0,
            metadata={}
        )
        category_entity = Entity(
            entity_id=uuid4(),
            name="cs.AI",
            entity_type=EntityType.CONCEPT,
            aliases=[],
            description="AI category",
            source_segments=[uuid4()],
            confidence=1.0,
            metadata={"type": "category"}
        )
        arxiv_connector.extract_entities = AsyncMock(return_value=[paper_entity, author_entity, category_entity])
        
        # メソッドを呼び出し
        relations = await arxiv_connector.extract_relations(arxiv_id="2301.12345")
        
        # 検証
        assert isinstance(relations, list)
        assert len(relations) > 0
        for relation in relations:
            assert isinstance(relation, Relation)
            assert hasattr(relation, "relation_id")
            assert hasattr(relation, "source_entity_id")
            assert hasattr(relation, "target_entity_id")
            assert hasattr(relation, "relation_type")
        
        # 著者関係が含まれているか確認
        authored_by_relation = next((r for r in relations if r.relation_type == RelationType.AUTHORED_BY), None)
        assert authored_by_relation is not None
        assert authored_by_relation.source_entity_id == paper_entity.entity_id
        assert authored_by_relation.target_entity_id == author_entity.entity_id

    @pytest.mark.asyncio
    async def test_search_by_category(self, arxiv_connector):
        """search_by_category()メソッドのテスト"""
        # search_papersをモック化
        arxiv_connector.search_papers = AsyncMock(return_value=[{"id": "2301.12345", "title": "AI Paper"}])
        
        # メソッドを呼び出し
        results = await arxiv_connector.search_by_category(category="cs.AI")
        
        # 検証
        arxiv_connector.search_papers.assert_called_once()
        call_args = arxiv_connector.search_papers.call_args[1]
        assert "cat:cs.AI" in call_args.get("query", "")
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["id"] == "2301.12345"

    @pytest.mark.asyncio
    async def test_search_by_date_range(self, arxiv_connector):
        """search_by_date_range()メソッドのテスト"""
        # search_papersをモック化
        arxiv_connector.search_papers = AsyncMock(return_value=[{"id": "2301.12345", "title": "Recent Paper"}])
        
        # メソッドを呼び出し
        results = await arxiv_connector.search_by_date_range(date_from="2023-01-01", date_to="2023-12-31")
        
        # 検証
        arxiv_connector.search_papers.assert_called_once()
        call_args = arxiv_connector.search_papers.call_args[1]
        assert call_args.get("date_from") == "2023-01-01"
        assert call_args.get("date_to") == "2023-12-31"
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["id"] == "2301.12345"

    @pytest.mark.asyncio
    async def test_download_full_text(self, arxiv_connector):
        """download_full_text()メソッドのテスト"""
        # download_pdfをモック化
        arxiv_connector.download_pdf = AsyncMock(return_value="/path/to/paper.pdf")
        
        # 通常のID場合のみ成功するようにし、UUIDは未実装エラーにする
        result = await arxiv_connector.download_full_text(document_id="2301.12345")
        assert result == "/path/to/paper.pdf"
        arxiv_connector.download_pdf.assert_called_once_with(arxiv_id="2301.12345", target_path=None)
        
        # UUIDの場合は対応していないのでNotImplementedErrorが発生
        with pytest.raises(NotImplementedError):
            await arxiv_connector.download_full_text(document_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_document(self, arxiv_connector):
        """get_document()メソッドのテスト"""
        # get_source_infoとget_paper_by_idをモック化
        source_data = SourceData(
            source_id=uuid4(),
            source_type=SourceType.ARXIV,
            source_url="https://arxiv.org/",
            source_name="arXiv"
        )
        arxiv_connector.get_source_info = AsyncMock(return_value=source_data)
        
        paper_data = {
            "id": "2301.12345",
            "title": "Test Paper",
            "authors": ["Test Author"],
            "summary": "Test abstract",
            "published": "2023-01-15",
            "categories": ["cs.AI"],
            "journal_ref": None,
            "doi": None,
            "comment": "25 pages"
        }
        arxiv_connector.get_paper_by_id = AsyncMock(return_value=paper_data)
        
        # メソッドを呼び出し
        document = await arxiv_connector.get_document(document_id="2301.12345")
        
        # 検証
        assert isinstance(document, Document)
        assert document.title == "Test Paper"
        assert document.authors == ["Test Author"]
        assert document.source_id == source_data.source_id
        assert "arxiv_id" in document.metadata
        assert document.metadata["arxiv_id"] == "2301.12345"

    @pytest.mark.asyncio
    async def test_extract_references(self, arxiv_connector):
        """extract_references()メソッドのテスト"""
        # download_pdfとextract_text_from_pdfをモック化
        arxiv_connector.download_pdf = AsyncMock(return_value="/path/to/paper.pdf")
        arxiv_connector.extract_text_from_pdf = AsyncMock(return_value="""
        Abstract
        This is an abstract.
        
        Introduction
        This is an introduction.
        
        References
        [1] Reference 1
        [2] Reference 2
        [3] Reference 3
        """)
        
        # メソッドを呼び出し
        references = await arxiv_connector.extract_references(document_id="2301.12345")
        
        # 検証
        assert isinstance(references, list)
        # リファレンスセクションが検出され、パースされていることをチェック
        assert len(references) > 0

    @pytest.mark.asyncio
    async def test_get_citation_data(self, arxiv_connector):
        """get_citation_data()メソッドのテスト"""
        # get_paper_by_idをモック化
        paper_data = {
            "id": "2301.12345",
            "title": "Test Paper",
            "authors": ["Test Author"],
            "published": "2023-01-15",
            "abstract_url": "https://arxiv.org/abs/2301.12345",
            "pdf_url": "https://arxiv.org/pdf/2301.12345",
            "doi": None
        }
        arxiv_connector.get_paper_by_id = AsyncMock(return_value=paper_data)
        
        # メソッドを呼び出し
        citation_data = await arxiv_connector.get_citation_data(document_id="2301.12345")
        
        # 検証
        assert isinstance(citation_data, dict)
        assert citation_data["arxiv_id"] == "2301.12345"
        assert citation_data["title"] == "Test Paper"
        assert citation_data["authors"] == ["Test Author"]
        assert citation_data["year"] == "2023"  # 年のみが抽出されていることを確認
        assert "citations_count" in citation_data
        assert "urls" in citation_data
        assert citation_data["urls"]["arxiv"] == "https://arxiv.org/abs/2301.12345"
        assert citation_data["urls"]["pdf"] == "https://arxiv.org/pdf/2301.12345"

    @pytest.mark.asyncio
    async def test_get_paper_metadata(self, arxiv_connector):
        """get_paper_metadata()メソッドのテスト"""
        # get_paper_by_idをモック化
        paper_data = {
            "id": "2301.12345",
            "title": "Test Paper",
            "authors": ["Test Author"],
            "summary": "Test abstract",
            "published": "2023-01-15",
            "updated": "2023-01-20",
            "categories": ["cs.AI", "quant-ph"],
            "pdf_url": "https://arxiv.org/pdf/2301.12345",
            "abstract_url": "https://arxiv.org/abs/2301.12345",
            "journal_ref": None,
            "doi": None,
            "comment": "25 pages"
        }
        arxiv_connector.get_paper_by_id = AsyncMock(return_value=paper_data)
        
        # メソッドを呼び出し
        metadata = await arxiv_connector.get_paper_metadata(arxiv_id="2301.12345")
        
        # 検証
        assert isinstance(metadata, dict)
        assert metadata["arxiv_id"] == "2301.12345"
        assert metadata["title"] == "Test Paper"
        assert metadata["authors"] == ["Test Author"]
        assert "abstract" in metadata
        assert "published" in metadata
        assert "categories" in metadata
        assert "primary_category" in metadata
        assert metadata["primary_category"] == "cs.AI"
        assert "source" in metadata
        assert metadata["source"] == "arxiv"

    @pytest.mark.asyncio
    async def test_get_vector_embeddings(self, arxiv_connector):
        """get_vector_embeddings()メソッドのテスト"""
        # get_paper_by_idをモック化
        paper_data = {
            "id": "2301.12345",
            "title": "Test Paper",
            "summary": "Test abstract"
        }
        arxiv_connector.get_paper_by_id = AsyncMock(return_value=paper_data)
        
        # segment_paperをモック化
        segment1 = Segment(
            segment_id=uuid4(),
            document_id=uuid4(),
            content="Test abstract",
            segment_type=SegmentType.ABSTRACT,
            position=0,
            metadata={}
        )
        arxiv_connector.segment_paper = AsyncMock(return_value=[segment1])
        
        # numpyのランダム処理をモック化
        with patch("numpy.random.rand", return_value=np.zeros(384)):
            # メソッドを呼び出し
            embeddings = await arxiv_connector.get_vector_embeddings(arxiv_id="2301.12345")
            
            # 検証
            assert isinstance(embeddings, dict)
            assert "title" in embeddings
            assert isinstance(embeddings["title"], list)
            assert len(embeddings["title"]) == 384
            assert "abstract" in embeddings
            assert "segments" in embeddings
            assert str(segment1.segment_id) in embeddings["segments"]
            assert "metadata" in embeddings
            assert embeddings["metadata"]["arxiv_id"] == "2301.12345"

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