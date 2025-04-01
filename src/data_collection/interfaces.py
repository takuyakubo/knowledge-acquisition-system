"""
データ収集インターフェース

このモジュールは、様々なデータソースからのデータ収集のための共通インターフェースを定義します。
各データコネクタはこれらのインターフェースを実装する必要があります。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from src.knowledge_extraction.entity_model import (Document, Entity, Relation,
                                                   Segment, SourceData)


class DataSourceConnector(ABC):
    """
    データソースコネクタの基本インターフェース
    
    すべてのデータソースコネクタはこのインターフェースを実装する必要があります。
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        コネクタを初期化する
        
        必要なリソースへの接続、認証、初期設定などを行います。
        
        Raises:
            ConnectionError: 接続エラー
            AuthenticationError: 認証エラー
        """
        pass
    
    @abstractmethod
    async def get_source_info(self) -> SourceData:
        """
        データソース情報を取得する
        
        Returns:
            データソース情報
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def get_document(self, document_id: Union[str, UUID]) -> Document:
        """
        特定のドキュメントを取得する
        
        Args:
            document_id: ドキュメントID
            
        Returns:
            ドキュメント情報
            
        Raises:
            DocumentNotFoundError: ドキュメントが見つからない場合
        """
        pass


class AcademicDataConnector(DataSourceConnector):
    """
    学術データソースコネクタのインターフェース拡張
    
    学術論文DBなどの学術データソースに固有の機能を提供します。
    """
    
    @abstractmethod
    async def search_by_category(self, category: str, **kwargs) -> List[Dict[str, Any]]:
        """
        カテゴリによる検索を行う
        
        Args:
            category: 検索カテゴリ
            **kwargs: 追加の検索パラメータ
            
        Returns:
            検索結果のリスト
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass


class ArxivConnectorInterface(AcademicDataConnector):
    """
    arXivコネクタのインターフェース
    
    arXiv APIを使用して論文データを収集・管理するための機能を定義します。
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def get_paper_by_id(self, arxiv_id: str) -> Dict[str, Any]:
        """
        arXiv IDを使用して特定の論文を取得する
        
        Args:
            arxiv_id: arXiv論文ID（例: "2103.13630"）
            
        Returns:
            論文メタデータ
            
        Raises:
            ArxivAPIError: API通信エラーまたは論文が見つからない場合
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def download_pdf(self, arxiv_id: str, target_path: Optional[str] = None) -> str:
        """
        arXiv論文のPDFをダウンロードする
        
        Args:
            arxiv_id: arXiv論文ID
            target_path: 保存先パス（省略時は標準パスを使用）
            
        Returns:
            保存されたPDFのファイルパス
            
        Raises:
            DownloadError: ダウンロードエラー
        """
        pass
    
    @abstractmethod
    async def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        PDFからテキストを抽出する
        
        Args:
            pdf_path: PDFファイルパス
            
        Returns:
            抽出されたテキスト
            
        Raises:
            ExtractionError: テキスト抽出エラー
        """
        pass
    
    @abstractmethod
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
        """
        pass
    
    @abstractmethod
    async def extract_entities(self, arxiv_id: str, segments: Optional[List[Segment]] = None) -> List[Entity]:
        """
        論文からエンティティを抽出する
        
        Args:
            arxiv_id: arXiv論文ID
            segments: 処理対象のセグメント（省略時はIDから取得）
            
        Returns:
            抽出されたエンティティのリスト
            
        Raises:
            ExtractionError: 抽出エラー
        """
        pass
    
    @abstractmethod
    async def extract_relations(self, arxiv_id: str, entities: Optional[List[Entity]] = None) -> List[Relation]:
        """
        論文内のエンティティ間の関係を抽出する
        
        Args:
            arxiv_id: arXiv論文ID
            entities: 処理対象のエンティティ（省略時はIDから取得）
            
        Returns:
            抽出された関係のリスト
            
        Raises:
            ExtractionError: 抽出エラー
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass