"""
arXiv APIコネクタ

arXiv APIを使用して学術論文データを収集するコネクタのインターフェース実装です。
"""

import asyncio
import aiohttp
import arxiv
import io
import os
import re
import requests
from datetime import datetime, date
from pdfminer.high_level import extract_text
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from src.common.config import get_config
from src.common.logger import get_logger
from src.data_collection.arxiv.exceptions import (ArxivAPIError,
                                                 DataNotFoundError,
                                                 PDFDownloadError,
                                                 SegmentationError,
                                                 TextExtractionError,
                                                 EntityExtractionError,
                                                 RelationExtractionError)
from src.data_collection.interfaces import ArxivConnectorInterface
from src.knowledge_extraction.entity_model import (Document, Entity, Relation,
                                                  Segment, SourceData,
                                                  SourceType, SegmentType,
                                                  EntityType, RelationType)

logger = get_logger(__name__)
config = get_config()


class ArxivConnector(ArxivConnectorInterface):
    """
    arXiv APIコネクタの実装クラス
    
    arXiv APIを使用して論文データを収集・処理するための機能を提供します。
    """
    
    def __init__(self, db_connection=None, vector_db_client=None, file_storage=None):
        """
        ArxivConnectorの初期化
        
        Args:
            db_connection: データベース接続オブジェクト
            vector_db_client: ベクトルデータベースクライアント
            file_storage: ファイルストレージハンドラ
        """
        self.db = db_connection
        self.vector_db = vector_db_client
        self.storage = file_storage
        
        # データ保存先の設定
        self.raw_data_dir = os.path.join(config.get('data_dir', 'data'), 'raw', 'arxiv')
        self.processed_data_dir = os.path.join(config.get('data_dir', 'data'), 'processed', 'arxiv')
        
        # ディレクトリ作成
        os.makedirs(self.raw_data_dir, exist_ok=True)
        os.makedirs(self.processed_data_dir, exist_ok=True)
        
        # APIクライアント
        self.api_client = arxiv.Client(
            page_size=100,
            delay_seconds=3.0,
            num_retries=3
        )
        
        # セッション
        self.session = None
        
        # エンティティ抽出・セグメント処理（実装時に初期化）
        self.entity_extractor = None
        self.text_processor = None
        
        # 正規表現パターン
        self.section_patterns = {
            'abstract': r'(?:abstract|概要|要約)(?:\s|:|：|\n)+',
            'introduction': r'(?:introduction|はじめに|序論|1\.(?:\s|．|\n)+(?:introduction|はじめに|序論))(?:\s|:|：|\n)+',
            'background': r'(?:background|背景|関連研究|previous\s+work|related\s+work)(?:\s|:|：|\n)+',
            'method': r'(?:method|methodology|approach|提案手法|手法|アプローチ|方法)(?:\s|:|：|\n)+',
            'experiment': r'(?:experiment|evaluation|実験|評価)(?:\s|:|：|\n)+',
            'result': r'(?:result|実験結果|結果)(?:\s|:|：|\n)+',
            'discussion': r'(?:discussion|考察)(?:\s|:|：|\n)+',
            'conclusion': r'(?:conclusion|おわりに|結論)(?:\s|:|：|\n)+',
            'reference': r'(?:reference|bibliography|参考文献|引用文献)(?:\s|:|：|\n)+',
        }
    
    async def initialize(self) -> None:
        """
        コネクタを初期化する
        
        必要なリソースへの接続、認証、初期設定などを行います。
        
        Raises:
            ConnectionError: 接続エラー
            AuthenticationError: 認証エラー
        """
        if self.session is None:
            self.session = aiohttp.ClientSession()
        logger.info("ArxivConnector initialized successfully")
    
    async def get_source_info(self) -> SourceData:
        """
        データソース情報を取得する
        
        Returns:
            データソース情報
        """
        return SourceData(
            source_type=SourceType.ARXIV,
            source_url="https://arxiv.org/",
            source_name="arXiv Open Access Papers",
            metadata={
                "api_version": "1.0", 
                "request_delay": 3,
                "max_results_per_query": 1000,
                "categories": [
                    "cs.AI", "cs.CL", "cs.CV", "cs.LG", "cs.NE", "cs.RO",
                    "stat.ML", "math.OC", "physics.comp-ph", "quant-ph"
                ]
            }
        )
    
    async def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        データソース内を検索する
        
        Args:
            query: 検索クエリ
            **kwargs: 追加の検索パラメータ
            
        Returns:
            検索結果のリスト
            
        Raises:
            SearchError: 検索エラー
        """
        # search_papersの呼び出しにマッピング
        return await self.search_papers(
            query=query,
            category=kwargs.get('category'),
            date_from=kwargs.get('date_from'),
            date_to=kwargs.get('date_to'),
            max_results=kwargs.get('max_results', 100)
        )
    
    async def search_papers(self, 
                           query: str, 
                           category: Optional[str] = None,
                           date_from: Optional[str] = None, 
                           date_to: Optional[str] = None,
                           max_results: int = 100) -> List[Dict[str, Any]]:
        """
        arXiv APIを使用して論文を検索する
        
        Args:
            query: 検索クエリ（例: "machine learning"）
            category: arXivカテゴリ（例: "cs.AI"）
            date_from: 検索開始日（YYYY-MM-DD形式）
            date_to: 検索終了日（YYYY-MM-DD形式）
            max_results: 最大結果数
            
        Returns:
            論文メタデータのリスト
        
        Raises:
            ArxivAPIError: API通信エラー発生時
        """
        logger.info(f"Searching papers with query: {query}, category: {category}, date range: {date_from} to {date_to}")
        
        try:
            # APIクエリ構築
            search_query = query
            
            # カテゴリがある場合、クエリに追加
            if category:
                search_query = f"{search_query} AND cat:{category}"
            
            # 日付範囲処理
            date_query = ""
            if date_from or date_to:
                if date_from:
                    try:
                        date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
                        date_query += f" AND submittedDate:[{date_from} TO "
                    except ValueError:
                        logger.warning(f"Invalid date_from format: {date_from}, expected YYYY-MM-DD")
                        raise ValueError(f"Invalid date_from format: {date_from}, expected YYYY-MM-DD")
                else:
                    date_query += " AND submittedDate:[ TO "
                
                if date_to:
                    try:
                        date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
                        date_query += f"{date_to}]"
                    except ValueError:
                        logger.warning(f"Invalid date_to format: {date_to}, expected YYYY-MM-DD")
                        raise ValueError(f"Invalid date_to format: {date_to}, expected YYYY-MM-DD")
                else:
                    date_query += f"{date.today().strftime('%Y-%m-%d')}]"
                
                search_query += date_query
            
            logger.debug(f"Final search query: {search_query}")
            
            # 検索を実行
            search = arxiv.Search(
                query=search_query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            results = []
            
            # 非同期環境でarxivモジュールを使用するためのループ処理
            def process_results():
                papers = []
                for result in self.api_client.results(search):
                    paper = {
                        "id": result.get_short_id(),
                        "title": result.title.replace("\n", " "),
                        "authors": [author.name for author in result.authors],
                        "summary": result.summary.replace("\n", " "),
                        "published": result.published.strftime("%Y-%m-%d"),
                        "updated": result.updated.strftime("%Y-%m-%d") if result.updated else None,
                        "categories": result.categories,
                        "pdf_url": result.pdf_url,
                        "abstract_url": result.entry_id,
                        "journal_ref": result.journal_ref,
                        "doi": result.doi,
                        "comment": result.comment
                    }
                    papers.append(paper)
                    if len(papers) >= max_results:
                        break
                return papers
            
            # 非同期ループでAPIリクエストを実行
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, process_results)
            
            logger.info(f"Found {len(results)} papers matching query")
            return results
            
        except Exception as e:
            error_msg = f"Error searching arXiv API: {str(e)}"
            logger.error(error_msg)
            raise ArxivAPIError(500, error_msg)
    
    async def get_paper_by_id(self, arxiv_id: str) -> Dict[str, Any]:
        """
        arXiv IDを使用して特定の論文を取得する
        
        Args:
            arxiv_id: arXiv論文ID（例: "2103.13630"）
            
        Returns:
            論文メタデータ
            
        Raises:
            ArxivAPIError: API通信エラーまたは論文が見つからない場合
            DataNotFoundError: 論文が見つからない場合
        """
        logger.info(f"Fetching paper with ID: {arxiv_id}")
        
        try:
            # IDフォーマットの正規化（バージョン番号を取り除く）
            clean_id = re.sub(r'v\d+$', '', arxiv_id)
            
            # 論文検索
            search = arxiv.Search(
                id_list=[clean_id],
                max_results=1
            )
            
            # 非同期環境でarxivモジュールを使用するためのループ処理
            def process_result():
                results = list(self.api_client.results(search))
                if not results:
                    return None
                
                result = results[0]
                return {
                    "id": result.get_short_id(),
                    "title": result.title.replace("\n", " "),
                    "authors": [author.name for author in result.authors],
                    "summary": result.summary.replace("\n", " "),
                    "published": result.published.strftime("%Y-%m-%d"),
                    "updated": result.updated.strftime("%Y-%m-%d") if result.updated else None,
                    "categories": result.categories,
                    "pdf_url": result.pdf_url,
                    "abstract_url": result.entry_id,
                    "journal_ref": result.journal_ref,
                    "doi": result.doi,
                    "comment": result.comment
                }
            
            # 非同期ループでAPIリクエストを実行
            loop = asyncio.get_event_loop()
            paper = await loop.run_in_executor(None, process_result)
            
            if not paper:
                error_msg = f"Paper with ID {arxiv_id} not found"
                logger.warning(error_msg)
                raise DataNotFoundError(error_msg)
            
            logger.info(f"Successfully fetched paper: {paper['title']}")
            return paper
            
        except DataNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Error fetching paper with ID {arxiv_id}: {str(e)}"
            logger.error(error_msg)
            raise ArxivAPIError(500, error_msg)
    
    async def collect(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        データを収集して保存する
        
        Args:
            query: 収集クエリ
            **kwargs: 追加の収集パラメータ
            
        Returns:
            収集結果情報のリスト
            
        Raises:
            CollectionError: 収集エラー
        """
        # collect_papersの呼び出しにマッピング
        return await self.collect_papers(
            query=query,
            category=kwargs.get('category'),
            date_from=kwargs.get('date_from'),
            date_to=kwargs.get('date_to'),
            max_results=kwargs.get('max_results', 100)
        )
    
    async def collect_papers(self, 
                            query: str, 
                            category: Optional[str] = None, 
                            date_from: Optional[str] = None, 
                            date_to: Optional[str] = None, 
                            max_results: int = 100) -> List[Dict[str, Any]]:
        """
        論文を検索し、メタデータと内容を収集・保存する
        
        Args:
            query: 検索クエリ
            category: arXivカテゴリ
            date_from: 検索開始日
            date_to: 検索終了日
            max_results: 最大結果数
            
        Returns:
            処理結果のリスト（成功/失敗情報を含む）
            
        Raises:
            各種エラー: 処理中に発生したエラー
        """
        logger.info(f"Collecting papers with query: {query}, category: {category}, date range: {date_from} to {date_to}")
        
        results = []
        
        try:
            # 論文の検索
            papers = await self.search_papers(
                query=query,
                category=category,
                date_from=date_from,
                date_to=date_to,
                max_results=max_results
            )
            
            # 各論文についてPDFのダウンロードとテキスト抽出を行う
            for paper in papers:
                paper_result = {
                    "id": paper["id"],
                    "title": paper["title"],
                    "status": "processing",
                    "errors": []
                }
                
                try:
                    # PDFダウンロード
                    pdf_path = await self.download_pdf(paper["id"])
                    paper_result["pdf_path"] = pdf_path
                    
                    # テキスト抽出
                    try:
                        text = await self.extract_text_from_pdf(pdf_path)
                        paper_result["text_extracted"] = True
                        paper_result["text_length"] = len(text)
                        
                        # セグメント化
                        try:
                            segments = await self.segment_paper(paper["id"], text)
                            paper_result["segments_count"] = len(segments)
                            
                            # メタデータをローカルに保存
                            metadata = {
                                "paper_id": paper["id"],
                                "title": paper["title"],
                                "authors": paper["authors"],
                                "categories": paper["categories"],
                                "published": paper["published"],
                                "updated": paper["updated"],
                                "abstract": paper["summary"],
                                "pdf_path": pdf_path,
                                "segments": [
                                    {
                                        "segment_id": str(segment.segment_id),
                                        "segment_type": segment.segment_type,
                                        "position": segment.position,
                                        "content_length": len(segment.content)
                                    }
                                    for segment in segments
                                ],
                                "collected_at": datetime.now().isoformat()
                            }
                            
                            # メタデータファイルのパス
                            metadata_path = os.path.join(
                                self.processed_data_dir, 
                                f"{paper['id']}_metadata.json"
                            )
                            
                            # ファイルに保存
                            import json
                            with open(metadata_path, 'w', encoding='utf-8') as f:
                                json.dump(metadata, f, ensure_ascii=False, indent=2)
                            
                            paper_result["metadata_path"] = metadata_path
                            paper_result["saved_to_db"] = True
                            paper_result["status"] = "success"
                            
                        except SegmentationError as e:
                            paper_result["errors"].append(f"Segmentation error: {str(e)}")
                            paper_result["status"] = "partial"
                            
                    except TextExtractionError as e:
                        paper_result["text_extracted"] = False
                        paper_result["errors"].append(f"Text extraction error: {str(e)}")
                        paper_result["status"] = "partial"
                        
                except PDFDownloadError as e:
                    paper_result["errors"].append(f"PDF download error: {str(e)}")
                    paper_result["status"] = "failed"
                
                results.append(paper_result)
                
            logger.info(f"Collection completed: {len(results)} papers processed")
            return results
            
        except ArxivAPIError as e:
            logger.error(f"arXiv API error during collection: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in collect_papers: {e}")
            raise
    
    async def get_document(self, document_id: Union[str, UUID]) -> Document:
        """
        特定のドキュメントを取得する
        
        Args:
            document_id: ドキュメントID（arXiv IDまたはUUID）
            
        Returns:
            ドキュメント情報
            
        Raises:
            DocumentNotFoundError: ドキュメントが見つからない場合
        """
        try:
            # UUIDの場合はデータベースから取得（今回は実装しない）
            if isinstance(document_id, UUID) or (isinstance(document_id, str) and len(document_id) == 36):
                # 本来はデータベースから検索する
                raise DataNotFoundError(f"Document with UUID {document_id} not found in database")
            
            # arXiv IDの場合はAPIから取得
            paper = await self.get_paper_by_id(document_id)
            
            # ドキュメントオブジェクトを作成
            source_data = await self.get_source_info()
            
            document = Document(
                document_id=uuid4(),  # 新しいUUIDを生成
                source_id=source_data.source_id,
                title=paper["title"],
                authors=paper["authors"],
                publication_date=datetime.strptime(paper["published"], "%Y-%m-%d"),
                content_type="pdf",  # PDFとして扱う
                raw_content_path=os.path.join(self.raw_data_dir, f"{paper['id']}.pdf"),
                language="en",  # 英語と仮定
                version=paper["id"].split("v")[-1] if "v" in paper["id"] else "1",
                metadata={
                    "arxiv_id": paper["id"],
                    "categories": paper["categories"],
                    "abstract": paper["summary"],
                    "doi": paper["doi"],
                    "journal_ref": paper["journal_ref"],
                    "comment": paper["comment"]
                }
            )
            
            return document
            
        except DataNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {str(e)}")
            raise DataNotFoundError(f"Error retrieving document: {str(e)}")
    
    async def search_by_category(self, category: str, **kwargs) -> List[Dict[str, Any]]:
        """
        カテゴリによる検索を行う
        
        Args:
            category: 検索カテゴリ
            **kwargs: 追加の検索パラメータ
            
        Returns:
            検索結果のリスト
        """
        query = f"cat:{category}"
        if 'query' in kwargs:
            query = f"{kwargs['query']} AND {query}"
        
        # search_papersを呼び出し
        return await self.search_papers(
            query=query,
            date_from=kwargs.get('date_from'),
            date_to=kwargs.get('date_to'),
            max_results=kwargs.get('max_results', 100)
        )
    
    async def search_by_date_range(self, date_from: str, date_to: str, **kwargs) -> List[Dict[str, Any]]:
        """
        日付範囲による検索を行う
        
        Args:
            date_from: 開始日（YYYY-MM-DD形式）
            date_to: 終了日（YYYY-MM-DD形式）
            **kwargs: 追加の検索パラメータ
            
        Returns:
            検索結果のリスト
        """
        query = kwargs.get('query', '')
        category = kwargs.get('category')
        
        # search_papersを呼び出し
        return await self.search_papers(
            query=query,
            category=category,
            date_from=date_from,
            date_to=date_to,
            max_results=kwargs.get('max_results', 100)
        )
    
    async def download_full_text(self, document_id: Union[str, UUID], target_path: Optional[str] = None) -> str:
        """
        論文の全文をダウンロードする
        
        Args:
            document_id: ドキュメントID
            target_path: 保存先パス（省略時は標準パスを使用）
            
        Returns:
            保存されたファイルのパス
            
        Raises:
            DownloadError: ダウンロードエラー
        """
        # arXiv IDに変換
        if isinstance(document_id, UUID) or (isinstance(document_id, str) and len(document_id) == 36):
            # UUIDの場合は本来データベースから検索してarXiv IDを取得する
            # ここでは簡単のためNotImplementedError
            raise NotImplementedError("UUID to arXiv ID conversion not implemented yet")
        
        # download_pdfを呼び出し
        return await self.download_pdf(arxiv_id=document_id, target_path=target_path)
    
    async def download_pdf(self, arxiv_id: str, target_path: Optional[str] = None) -> str:
        """
        arXiv論文のPDFをダウンロードする
        
        Args:
            arxiv_id: arXiv論文ID
            target_path: 保存先パス（省略時は標準パスを使用）
            
        Returns:
            保存されたPDFのファイルパス
            
        Raises:
            PDFDownloadError: ダウンロードエラー
        """
        logger.info(f"Downloading PDF for paper: {arxiv_id}")
        
        try:
            # PDFのURLを取得
            paper = await self.get_paper_by_id(arxiv_id)
            pdf_url = paper["pdf_url"]
            
            # 保存先パスの設定
            if target_path is None:
                target_path = os.path.join(self.raw_data_dir, f"{arxiv_id}.pdf")
            
            # PDFをダウンロード
            async with self.session.get(pdf_url) as response:
                if response.status != 200:
                    error_msg = f"Failed to download PDF from {pdf_url}: HTTP {response.status}"
                    logger.error(error_msg)
                    raise PDFDownloadError(error_msg)
                
                # ファイルに保存
                content = await response.read()
                with open(target_path, 'wb') as f:
                    f.write(content)
            
            logger.info(f"PDF downloaded successfully: {target_path}")
            return target_path
            
        except (ArxivAPIError, DataNotFoundError) as e:
            error_msg = f"Error fetching paper info for PDF download: {str(e)}"
            logger.error(error_msg)
            raise PDFDownloadError(error_msg)
        except Exception as e:
            error_msg = f"Error downloading PDF for paper {arxiv_id}: {str(e)}"
            logger.error(error_msg)
            raise PDFDownloadError(error_msg)
    
    async def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        PDFからテキストを抽出する
        
        Args:
            pdf_path: PDFファイルパス
            
        Returns:
            抽出されたテキスト
            
        Raises:
            TextExtractionError: テキスト抽出エラー
        """
        logger.info(f"Extracting text from PDF: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            error_msg = f"PDF file not found: {pdf_path}"
            logger.error(error_msg)
            raise TextExtractionError(error_msg)
        
        try:
            # PDFMinerを使用してテキストを抽出（非同期に処理）
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, lambda: extract_text(pdf_path))
            
            # 基本的なクリーニング
            text = re.sub(r'\n{3,}', '\n\n', text)  # 余分な改行を削除
            
            logger.info(f"Successfully extracted {len(text)} characters from PDF")
            return text
            
        except Exception as e:
            error_msg = f"Error extracting text from PDF {pdf_path}: {str(e)}"
            logger.error(error_msg)
            raise TextExtractionError(error_msg)
    
    async def extract_references(self, document_id: Union[str, UUID]) -> List[Dict[str, Any]]:
        """
        論文から参考文献情報を抽出する
        
        Args:
            document_id: ドキュメントID
            
        Returns:
            参考文献情報のリスト
            
        Raises:
            ExtractionError: 抽出エラー
        """
        # 論文の本文を取得
        try:
            # ドキュメントIDからarXiv IDを取得
            arxiv_id = document_id
            if isinstance(document_id, UUID) or (isinstance(document_id, str) and len(document_id) == 36):
                # UUIDの場合は本来データベースから検索
                # 現段階では未実装
                raise NotImplementedError("UUID to arXiv ID conversion not implemented yet")
            
            # PDFパスを取得または生成
            pdf_path = os.path.join(self.raw_data_dir, f"{arxiv_id}.pdf")
            if not os.path.exists(pdf_path):
                # PDFが存在しない場合はダウンロード
                pdf_path = await self.download_pdf(arxiv_id)
            
            # テキストを抽出
            text = await self.extract_text_from_pdf(pdf_path)
            
            # リファレンスセクションを抽出する簡易的な実装
            references = []
            ref_section = None
            
            # リファレンスセクションを検出
            ref_matches = list(re.finditer(self.section_patterns['reference'], text, re.IGNORECASE))
            if ref_matches:
                ref_start = ref_matches[-1].end()  # 最後のリファレンスセクションを使用
                ref_section = text[ref_start:]
                
                # 参考文献を行ごとに分割して処理
                ref_lines = ref_section.split('\n')
                current_ref = ""
                
                for line in ref_lines:
                    # 新しい参考文献の開始パターン（番号付きリストなど）を検出
                    if re.match(r'^\s*\[\d+\]|\s*\(\d+\)|\s*\d+\.', line):
                        if current_ref:
                            references.append({"text": current_ref.strip()})
                        current_ref = line
                    else:
                        current_ref += " " + line
                
                # 最後の参考文献を追加
                if current_ref:
                    references.append({"text": current_ref.strip()})
            
            logger.info(f"Extracted {len(references)} references from document {arxiv_id}")
            return references
            
        except Exception as e:
            error_msg = f"Error extracting references from document {document_id}: {str(e)}"
            logger.error(error_msg)
            raise RelationExtractionError(error_msg)
    
    async def get_citation_data(self, document_id: Union[str, UUID]) -> Dict[str, Any]:
        """
        引用データを取得する
        
        Args:
            document_id: ドキュメントID
            
        Returns:
            引用データ情報
            
        Raises:
            DataNotFoundError: データが見つからない場合
        """
        # 現段階では引用データの取得は外部APIが必要なため
        # 簡易的な実装を行う
        try:
            # ドキュメントIDからarXiv IDを取得
            arxiv_id = document_id
            if isinstance(document_id, UUID) or (isinstance(document_id, str) and len(document_id) == 36):
                # UUIDの場合は本来データベースから検索
                # 現段階では未実装
                raise NotImplementedError("UUID to arXiv ID conversion not implemented yet")
            
            # 論文の基本情報を取得
            paper = await self.get_paper_by_id(arxiv_id)
            
            # 引用データの簡易的な実装（実際にはSemanticScholarなどの外部APIを使用する）
            citation_data = {
                "arxiv_id": arxiv_id,
                "title": paper["title"],
                "authors": paper["authors"],
                "year": paper["published"][:4],
                "citations_count": 0,  # 実際のデータがないため0
                "reference_count": 0,  # 実際のデータがないため0
                "citation_velocity": 0,  # 実際のデータがないため0
                "influential_citation_count": 0,  # 実際のデータがないため0
                "source": "arXiv",
                "doi": paper.get("doi"),
                "urls": {
                    "arxiv": paper["abstract_url"],
                    "pdf": paper["pdf_url"]
                }
            }
            
            return citation_data
            
        except DataNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Error retrieving citation data for document {document_id}: {str(e)}"
            logger.error(error_msg)
            raise DataNotFoundError(error_msg)
    
    async def segment_paper(self, arxiv_id: str, text_content: Optional[str] = None) -> List[Segment]:
        """
        論文テキストをセグメントに分割する
        
        Args:
            arxiv_id: arXiv論文ID
            text_content: テキスト内容（省略時はIDから取得）
            
        Returns:
            セグメントのリスト
            
        Raises:
            SegmentationError: 分割エラー
            DataNotFoundError: テキストが取得できない場合
        """
        logger.info(f"Segmenting paper: {arxiv_id}")
        
        try:
            # テキストが提供されていない場合はPDFから抽出
            if text_content is None:
                # PDFパスを取得または生成
                pdf_path = os.path.join(self.raw_data_dir, f"{arxiv_id}.pdf")
                if not os.path.exists(pdf_path):
                    # PDFが存在しない場合はダウンロード
                    pdf_path = await self.download_pdf(arxiv_id)
                
                # テキストを抽出
                text_content = await self.extract_text_from_pdf(pdf_path)
            
            # 論文の基本情報を取得
            paper = await self.get_paper_by_id(arxiv_id)
            
            # 共通のメタデータ
            common_metadata = {
                "source": "arxiv",
                "paper_id": arxiv_id,
                "title": paper["title"],
                "authors": paper["authors"],
                "categories": paper["categories"]
            }
            
            # ダミーのドキュメントID（本来はデータベースから取得）
            document_id = uuid4()
            
            # セグメントリスト
            segments = []
            
            # アブストラクトをセグメントとして追加
            abstract_segment = Segment(
                segment_id=uuid4(),
                document_id=document_id,
                content=paper["summary"],
                segment_type=SegmentType.ABSTRACT,
                position=0,
                metadata={**common_metadata, "segment_type": "abstract"}
            )
            segments.append(abstract_segment)
            
            # 本文のセクションを抽出
            position = 1
            current_segment_type = None
            current_segment_content = ""
            
            # 行ごとに処理
            lines = text_content.split('\n')
            for line in lines:
                # セクション見出しを検出
                section_type = None
                for section_name, pattern in self.section_patterns.items():
                    if re.match(pattern, line, re.IGNORECASE):
                        section_type = section_name
                        break
                
                # 新しいセクションの開始
                if section_type:
                    # 前のセグメントが存在する場合は保存
                    if current_segment_type and current_segment_content.strip():
                        segment = Segment(
                            segment_id=uuid4(),
                            document_id=document_id,
                            content=current_segment_content.strip(),
                            segment_type=getattr(SegmentType, current_segment_type.upper(), SegmentType.PARAGRAPH),
                            position=position,
                            metadata={**common_metadata, "segment_type": current_segment_type}
                        )
                        segments.append(segment)
                        position += 1
                    
                    # 新しいセグメント開始
                    current_segment_type = section_type
                    current_segment_content = line + '\n'
                else:
                    # 既存のセグメントに行を追加
                    if current_segment_type:
                        current_segment_content += line + '\n'
                    # セクション見出しがまだ検出されていない場合（前書きや著者情報など）
                    elif not current_segment_type and line.strip():
                        if not any(segments):
                            # 最初のセグメントとして扱う
                            current_segment_type = "introduction"
                            current_segment_content += line + '\n'
            
            # 最後のセグメントを追加
            if current_segment_type and current_segment_content.strip():
                segment = Segment(
                    segment_id=uuid4(),
                    document_id=document_id,
                    content=current_segment_content.strip(),
                    segment_type=getattr(SegmentType, current_segment_type.upper(), SegmentType.PARAGRAPH),
                    position=position,
                    metadata={**common_metadata, "segment_type": current_segment_type}
                )
                segments.append(segment)
            
            # セグメントが少なすぎる場合は簡易的な分割も行う
            if len(segments) < 3:
                # 段落ごとに分割
                paragraphs = re.split(r'\n\s*\n', text_content)
                position = len(segments)
                
                for i, para in enumerate(paragraphs):
                    if len(para.strip()) < 50:  # 短すぎる段落はスキップ
                        continue
                    
                    segment = Segment(
                        segment_id=uuid4(),
                        document_id=document_id,
                        content=para.strip(),
                        segment_type=SegmentType.PARAGRAPH,
                        position=position + i,
                        metadata={**common_metadata, "segment_type": "paragraph", "paragraph_index": i}
                    )
                    segments.append(segment)
            
            logger.info(f"Paper segmented into {len(segments)} segments")
            return segments
            
        except (ArxivAPIError, DataNotFoundError, PDFDownloadError, TextExtractionError) as e:
            error_msg = f"Error during paper segmentation: {str(e)}"
            logger.error(error_msg)
            raise SegmentationError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error segmenting paper {arxiv_id}: {str(e)}"
            logger.error(error_msg)
            raise SegmentationError(error_msg)
    
    async def extract_entities(self, arxiv_id: str, segments: Optional[List[Segment]] = None) -> List[Entity]:
        """
        論文からエンティティを抽出する
        
        Args:
            arxiv_id: arXiv論文ID
            segments: 処理対象のセグメント（省略時はIDから取得）
            
        Returns:
            抽出されたエンティティのリスト
            
        Raises:
            EntityExtractionError: 抽出エラー
        """
        logger.info(f"Extracting entities from paper: {arxiv_id}")
        
        try:
            # セグメントが提供されていない場合は取得
            if segments is None:
                segments = await self.segment_paper(arxiv_id)
            
            # 論文の基本情報を取得
            paper = await self.get_paper_by_id(arxiv_id)
            
            # エンティティリスト
            entities = []
            
            # 実際のエンティティ抽出には自然言語処理モデルが必要
            # 現段階では簡易的な実装を行う
            # 本来はLLMやNERモデルを使用してエンティティを抽出する
            
            # 論文自体をエンティティとして追加
            paper_entity = Entity(
                entity_id=uuid4(),
                name=paper["title"],
                entity_type=EntityType.PAPER,
                aliases=[],
                description=paper["summary"],
                source_segments=[segment.segment_id for segment in segments if segment.segment_type == SegmentType.ABSTRACT],
                confidence=1.0,
                metadata={
                    "arxiv_id": arxiv_id,
                    "authors": paper["authors"],
                    "published": paper["published"],
                    "categories": paper["categories"],
                    "source": "arxiv"
                }
            )
            entities.append(paper_entity)
            
            # 著者をエンティティとして追加
            for author in paper["authors"]:
                author_entity = Entity(
                    entity_id=uuid4(),
                    name=author,
                    entity_type=EntityType.PERSON,
                    aliases=[],
                    description=f"Author of '{paper['title']}'",
                    source_segments=[segment.segment_id for segment in segments if segment.segment_type == SegmentType.ABSTRACT],
                    confidence=1.0,
                    metadata={
                        "role": "author",
                        "paper_id": arxiv_id,
                        "source": "arxiv"
                    }
                )
                entities.append(author_entity)
            
            # カテゴリをエンティティとして追加
            for category in paper["categories"]:
                category_entity = Entity(
                    entity_id=uuid4(),
                    name=category,
                    entity_type=EntityType.CONCEPT,
                    aliases=[],
                    description=f"arXiv category for paper '{paper['title']}'",
                    source_segments=[segment.segment_id for segment in segments if segment.segment_type == SegmentType.ABSTRACT],
                    confidence=1.0,
                    metadata={
                        "type": "category",
                        "paper_id": arxiv_id,
                        "source": "arxiv"
                    }
                )
                entities.append(category_entity)
            
            logger.info(f"Extracted {len(entities)} entities from paper {arxiv_id}")
            return entities
            
        except (ArxivAPIError, DataNotFoundError, SegmentationError) as e:
            error_msg = f"Error during entity extraction: {str(e)}"
            logger.error(error_msg)
            raise EntityExtractionError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error extracting entities from paper {arxiv_id}: {str(e)}"
            logger.error(error_msg)
            raise EntityExtractionError(error_msg)
    
    async def extract_relations(self, arxiv_id: str, entities: Optional[List[Entity]] = None) -> List[Relation]:
        """
        論文内のエンティティ間の関係を抽出する
        
        Args:
            arxiv_id: arXiv論文ID
            entities: 処理対象のエンティティ（省略時はIDから取得）
            
        Returns:
            抽出された関係のリスト
            
        Raises:
            RelationExtractionError: 抽出エラー
        """
        logger.info(f"Extracting relations from paper: {arxiv_id}")
        
        try:
            # エンティティが提供されていない場合は取得
            if entities is None:
                entities = await self.extract_entities(arxiv_id)
            
            # 関係リスト
            relations = []
            
            # 実際の関係抽出には自然言語処理モデルが必要
            # 現段階では簡易的な実装を行う
            
            # 論文エンティティを特定
            paper_entity = next((e for e in entities if e.entity_type == EntityType.PAPER), None)
            if not paper_entity:
                logger.warning(f"Paper entity not found for {arxiv_id}")
                return relations
            
            # 著者関係を追加
            author_entities = [e for e in entities if e.entity_type == EntityType.PERSON]
            for author_entity in author_entities:
                relation = Relation(
                    relation_id=uuid4(),
                    source_entity_id=paper_entity.entity_id,
                    target_entity_id=author_entity.entity_id,
                    relation_type=RelationType.AUTHORED_BY,
                    description=f"'{paper_entity.name}' is authored by {author_entity.name}",
                    source_segments=paper_entity.source_segments,
                    confidence=1.0,
                    metadata={
                        "paper_id": arxiv_id,
                        "source": "arxiv"
                    }
                )
                relations.append(relation)
            
            # カテゴリ関係を追加
            category_entities = [e for e in entities if e.entity_type == EntityType.CONCEPT]
            for category_entity in category_entities:
                relation = Relation(
                    relation_id=uuid4(),
                    source_entity_id=paper_entity.entity_id,
                    target_entity_id=category_entity.entity_id,
                    relation_type=RelationType.PART_OF,
                    description=f"'{paper_entity.name}' is part of category {category_entity.name}",
                    source_segments=paper_entity.source_segments,
                    confidence=1.0,
                    metadata={
                        "paper_id": arxiv_id,
                        "relation_type": "categorization",
                        "source": "arxiv"
                    }
                )
                relations.append(relation)
            
            logger.info(f"Extracted {len(relations)} relations from paper {arxiv_id}")
            return relations
            
        except (ArxivAPIError, DataNotFoundError, EntityExtractionError) as e:
            error_msg = f"Error during relation extraction: {str(e)}"
            logger.error(error_msg)
            raise RelationExtractionError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error extracting relations from paper {arxiv_id}: {str(e)}"
            logger.error(error_msg)
            raise RelationExtractionError(error_msg)
    
    async def get_paper_metadata(self, arxiv_id: str) -> Dict[str, Any]:
        """
        論文のメタデータを取得する
        
        Args:
            arxiv_id: arXiv論文ID
            
        Returns:
            メタデータ辞書
            
        Raises:
            DataNotFoundError: データが見つからない場合
        """
        try:
            # 論文の基本情報を取得
            paper = await self.get_paper_by_id(arxiv_id)
            
            # メタデータを拡張
            metadata = {
                "arxiv_id": arxiv_id,
                "title": paper["title"],
                "authors": paper["authors"],
                "abstract": paper["summary"],
                "published": paper["published"],
                "updated": paper["updated"],
                "categories": paper["categories"],
                "primary_category": paper["categories"][0] if paper["categories"] else None,
                "journal_ref": paper["journal_ref"],
                "doi": paper["doi"],
                "comment": paper["comment"],
                "pdf_url": paper["pdf_url"],
                "abstract_url": paper["abstract_url"],
                "source": "arxiv",
                "retrieved_at": datetime.now().isoformat()
            }
            
            return metadata
            
        except DataNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Error retrieving metadata for paper {arxiv_id}: {str(e)}"
            logger.error(error_msg)
            raise DataNotFoundError(error_msg)
    
    async def get_vector_embeddings(self, arxiv_id: str) -> Dict[str, List[float]]:
        """
        論文のベクトル埋め込みを取得する
        
        Args:
            arxiv_id: arXiv論文ID
            
        Returns:
            ベクトル埋め込み情報
            
        Raises:
            DataNotFoundError: データが見つからない場合
        """
        # 現段階ではベクトル埋め込みの実装は省略
        # 実際には外部のモデル（例：Sentence-BERT）を使用してテキストをベクトル化する
        try:
            # 論文の基本情報を取得
            paper = await self.get_paper_by_id(arxiv_id)
            
            # セグメントを取得
            segments = await self.segment_paper(arxiv_id)
            
            # ダミーのベクトル埋め込み（実際の実装では外部モデルを使用）
            import numpy as np
            
            # 結果を格納するディクショナリ
            embeddings = {}
            
            # タイトルのダミー埋め込み
            embeddings["title"] = list(np.random.rand(384).astype(float))
            
            # 要約のダミー埋め込み
            embeddings["abstract"] = list(np.random.rand(384).astype(float))
            
            # セグメントごとのダミー埋め込み
            segment_embeddings = {}
            for segment in segments:
                segment_id = str(segment.segment_id)
                segment_embeddings[segment_id] = list(np.random.rand(384).astype(float))
            
            embeddings["segments"] = segment_embeddings
            
            # メタデータ
            embeddings["metadata"] = {
                "model": "dummy-embedding-model",
                "dimension": 384,
                "arxiv_id": arxiv_id,
                "generated_at": datetime.now().isoformat()
            }
            
            return embeddings
            
        except DataNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Error generating vector embeddings for paper {arxiv_id}: {str(e)}"
            logger.error(error_msg)
            raise DataNotFoundError(error_msg)