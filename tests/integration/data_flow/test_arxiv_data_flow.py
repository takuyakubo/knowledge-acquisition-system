"""
arXivコネクタのデータフロー統合テスト

このモジュールは、arXivコネクタを使ったデータ収集から知識抽出までのフローをテストします。
"""

import os
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from src.data_collection.arxiv.connector import ArxivConnector
from src.data_collection.arxiv.exceptions import ArxivAPIError
from src.knowledge_extraction.entity_model import (
    SourceType,
    Document,
    Entity,
    Segment,
    SourceData,
    ContentType,
    EntityType
)


@pytest.mark.asyncio
class TestArxivDataFlow:
    """arXivコネクタを使ったデータフロー統合テスト"""

    @pytest_asyncio.fixture
    async def mock_arxiv_connector(self):
        """
        モック化されたarXivコネクタを提供するフィクスチャ
        
        実際のAPIを呼び出さずにテストできるようにするためのモック
        """
        # 基本的なモックを設定
        with patch('os.makedirs'):
            with patch('src.common.config.get_config') as mock_get_config:
                # 設定をモック化
                mock_get_config.return_value = {'data_dir': '/tmp/test_data'}
                connector = ArxivConnector()
                
                # APIレスポンスをモック化
                sample_papers = [
                    {
                        "id": "2301.12345",
                        "title": "Quantum Machine Learning Applications",
                        "authors": ["Alice Smith", "Bob Johnson"],
                        "summary": "This paper explores quantum computing applications in machine learning...",
                        "published": "2023-01-15",
                        "updated": "2023-01-20",
                        "categories": ["cs.AI", "quant-ph"],
                        "pdf_url": "https://arxiv.org/pdf/2301.12345"
                    },
                    {
                        "id": "2302.54321",
                        "title": "Deep Learning for Quantum Systems",
                        "authors": ["Carol Williams", "David Brown"],
                        "summary": "We present a novel deep learning approach for quantum systems...",
                        "published": "2023-02-10",
                        "updated": "2023-02-15",
                        "categories": ["cs.LG", "quant-ph"],
                        "pdf_url": "https://arxiv.org/pdf/2302.54321"
                    }
                ]
                
                # search_papers のモック実装
                async def mock_search_papers(*args, **kwargs):
                    return sample_papers
                
                # download_pdf のモック実装
                async def mock_download_pdf(arxiv_id, target_path=None):
                    if target_path is None:
                        target_path = f"/tmp/test_data/raw/arxiv/{arxiv_id}.pdf"
                    return target_path
                
                # extract_text_from_pdf のモック実装
                async def mock_extract_text_from_pdf(pdf_path):
                    # PDF パスから arxiv_id を抽出
                    arxiv_id = os.path.basename(pdf_path).replace(".pdf", "")
                    if arxiv_id == "2301.12345":
                        return "This paper explores quantum computing applications in machine learning..."
                    elif arxiv_id == "2302.54321":
                        return "We present a novel deep learning approach for quantum systems..."
                    else:
                        return "Sample text content for testing purposes."
                
                # segment_paper のモック実装
                async def mock_segment_paper(arxiv_id, text_content=None):
                    if text_content is None:
                        if arxiv_id == "2301.12345":
                            text_content = "This paper explores quantum computing applications in machine learning..."
                        elif arxiv_id == "2302.54321":
                            text_content = "We present a novel deep learning approach for quantum systems..."
                        else:
                            text_content = "Sample text content for testing purposes."
                    
                    # テスト用のセグメントを作成
                    segments = [
                        Segment(
                            segment_id=uuid4(),
                            document_id=UUID('11111111-1111-1111-1111-111111111111'),
                            content=text_content[:50],
                            segment_type="abstract",
                            position=0,
                            metadata={"source": "arxiv", "paper_id": arxiv_id}
                        ),
                        Segment(
                            segment_id=uuid4(),
                            document_id=UUID('11111111-1111-1111-1111-111111111111'),
                            content=text_content[50:] if len(text_content) > 50 else "Additional content",
                            segment_type="introduction",
                            position=1,
                            metadata={"source": "arxiv", "paper_id": arxiv_id}
                        )
                    ]
                    return segments
                
                # extract_entities のモック実装
                async def mock_extract_entities(arxiv_id, segments=None):
                    if segments is None:
                        segments = await mock_segment_paper(arxiv_id)
                    
                    # テスト用のエンティティを作成
                    entities = []
                    if arxiv_id == "2301.12345":
                        entities = [
                            Entity(
                                entity_id=uuid4(),
                                name="Quantum Computing",
                                entity_type=EntityType.TECHNOLOGY,
                                aliases=["Quantum Computation", "Quantum Information Processing"],
                                description="Computing paradigm that uses quantum-mechanical phenomena",
                                confidence=0.95,
                                source_segments=[segments[0].segment_id]
                            ),
                            Entity(
                                entity_id=uuid4(),
                                name="Machine Learning",
                                entity_type=EntityType.CONCEPT,
                                aliases=["ML", "Automated Learning"],
                                description="Field of AI focused on algorithms that learn from data",
                                confidence=0.92,
                                source_segments=[segments[0].segment_id, segments[1].segment_id]
                            )
                        ]
                    elif arxiv_id == "2302.54321":
                        entities = [
                            Entity(
                                entity_id=uuid4(),
                                name="Deep Learning",
                                entity_type=EntityType.TECHNOLOGY,
                                aliases=["DL", "Deep Neural Networks"],
                                description="Subset of machine learning using neural networks with many layers",
                                confidence=0.97,
                                source_segments=[segments[0].segment_id]
                            ),
                            Entity(
                                entity_id=uuid4(),
                                name="Quantum Systems",
                                entity_type=EntityType.CONCEPT,
                                aliases=["Quantum Physics Systems"],
                                description="Physical systems governed by quantum mechanics",
                                confidence=0.94,
                                source_segments=[segments[1].segment_id]
                            )
                        ]
                    return entities
                
                # モックメソッドを設定
                connector.initialize = AsyncMock()
                connector.search_papers = AsyncMock(side_effect=mock_search_papers)
                connector.download_pdf = AsyncMock(side_effect=mock_download_pdf)
                connector.extract_text_from_pdf = AsyncMock(side_effect=mock_extract_text_from_pdf)
                connector.segment_paper = AsyncMock(side_effect=mock_segment_paper)
                connector.extract_entities = AsyncMock(side_effect=mock_extract_entities)
                
                return connector

    async def test_complete_paper_processing_flow(self, mock_arxiv_connector):
        """
        論文処理の完全なフローをテスト
        
        検索から知識抽出までの一連の流れをテスト
        """
        # 1. 論文を検索
        papers = await mock_arxiv_connector.search_papers(
            query="quantum machine learning",
            category="cs.AI",
            max_results=2
        )
        
        # 結果を検証
        assert len(papers) == 2
        assert papers[0]["id"] == "2301.12345"
        assert "Quantum Machine Learning" in papers[0]["title"]
        
        # 最初の論文を処理
        paper_id = papers[0]["id"]
        
        # 2. PDFをダウンロード
        pdf_path = await mock_arxiv_connector.download_pdf(paper_id)
        assert pdf_path.endswith(f"{paper_id}.pdf")
        
        # 3. テキストを抽出
        text_content = await mock_arxiv_connector.extract_text_from_pdf(pdf_path)
        assert "quantum computing" in text_content.lower()
        
        # 4. テキストをセグメント化
        segments = await mock_arxiv_connector.segment_paper(paper_id, text_content)
        assert len(segments) == 2
        assert segments[0].segment_type == "abstract"
        assert segments[1].segment_type == "introduction"
        
        # 5. エンティティを抽出
        entities = await mock_arxiv_connector.extract_entities(paper_id, segments)
        assert len(entities) == 2
        
        # エンティティの検証
        entity_names = [entity.name for entity in entities]
        assert "Quantum Computing" in entity_names
        assert "Machine Learning" in entity_names
        
        # 抽出されたエンティティのメタデータを検証
        quantum_entity = next((e for e in entities if e.name == "Quantum Computing"), None)
        ml_entity = next((e for e in entities if e.name == "Machine Learning"), None)
        
        assert quantum_entity is not None
        assert ml_entity is not None
        assert quantum_entity.entity_type == EntityType.TECHNOLOGY
        assert ml_entity.entity_type == EntityType.CONCEPT
        assert len(quantum_entity.aliases) > 0
        assert len(ml_entity.aliases) > 0
        
        # 6. 開始から終了までの一連の流れが成功していることを確認
        assert mock_arxiv_connector.search_papers.called
        assert mock_arxiv_connector.download_pdf.called
        assert mock_arxiv_connector.extract_text_from_pdf.called
        assert mock_arxiv_connector.segment_paper.called
        assert mock_arxiv_connector.extract_entities.called

    async def test_error_handling_in_flow(self, mock_arxiv_connector):
        """
        処理フロー中のエラーハンドリングをテスト
        """
        # API検索エラーをシミュレート
        mock_arxiv_connector.search_papers = AsyncMock(side_effect=ArxivAPIError(503, "Service Unavailable"))
        
        # エラーが適切に伝播されることを確認
        with pytest.raises(ArxivAPIError) as excinfo:
            await mock_arxiv_connector.search_papers(query="quantum computing")
        
        # エラーメッセージと状態コードを検証
        assert excinfo.value.status_code == 503
        assert "Service Unavailable" in str(excinfo.value)