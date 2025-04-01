"""
エンティティモデル定義モジュール

このモジュールでは、知識抽出プロセスで利用されるPydanticモデルを定義しています。
各モデルはデータベーススキーマと対応し、APIやバックエンド処理間でのデータ転送に使用されます。
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SourceType(str, Enum):
    """データソースの種類を定義する列挙型"""
    ACADEMIC_DB = "academic_db"  # 学術論文データベース
    WEB = "web"  # Webページ
    LOCAL_FILE = "local_file"  # ローカルファイル
    API = "api"  # 外部API
    ARXIV = "arxiv"  # arXiv API


class ProcessingStatus(str, Enum):
    """データ処理状態を定義する列挙型"""
    COLLECTED = "collected"  # 収集済み
    PREPROCESSED = "preprocessed"  # 前処理済み
    ANALYZED = "analyzed"  # 分析済み
    INDEXED = "indexed"  # インデックス済み
    ERROR = "error"  # エラー発生


class ContentType(str, Enum):
    """コンテンツタイプを定義する列挙型"""
    TEXT = "text"  # プレーンテキスト
    PDF = "pdf"  # PDF文書
    HTML = "html"  # HTMLページ
    JSON = "json"  # JSONデータ
    XML = "xml"  # XMLデータ


class SegmentType(str, Enum):
    """セグメントタイプを定義する列挙型"""
    PARAGRAPH = "paragraph"  # 段落
    HEADING = "heading"  # 見出し
    TABLE = "table"  # 表
    LIST = "list"  # リスト
    FIGURE = "figure"  # 図表
    CODE = "code"  # コードブロック
    QUOTE = "quote"  # 引用
    ABSTRACT = "abstract"  # 要約・概要
    INTRODUCTION = "introduction"  # 導入
    METHOD = "method"  # 手法
    RESULT = "result"  # 結果
    DISCUSSION = "discussion"  # 考察
    CONCLUSION = "conclusion"  # 結論
    REFERENCE = "reference"  # 参考文献


class EntityType(str, Enum):
    """エンティティタイプを定義する列挙型"""
    CONCEPT = "concept"  # 概念
    PERSON = "person"  # 人物
    ORGANIZATION = "organization"  # 組織
    TECHNOLOGY = "technology"  # 技術
    PRODUCT = "product"  # 製品
    METHOD = "method"  # 手法
    DATASET = "dataset"  # データセット
    ALGORITHM = "algorithm"  # アルゴリズム
    TERM = "term"  # 専門用語
    LOCATION = "location"  # 場所
    EVENT = "event"  # イベント
    PAPER = "paper"  # 論文
    JOURNAL = "journal"  # ジャーナル
    CONFERENCE = "conference"  # 会議


class RelationType(str, Enum):
    """関係タイプを定義する列挙型"""
    INCLUDES = "includes"  # 包含関係
    USES = "uses"  # 利用関係
    OPPOSES = "opposes"  # 対立関係
    SIMILAR_TO = "similar_to"  # 類似関係
    PRECEDES = "precedes"  # 先行関係
    CAUSES = "causes"  # 因果関係
    PART_OF = "part_of"  # 構成関係
    CITES = "cites"  # 引用関係
    AUTHORED_BY = "authored_by"  # 著者関係
    BASED_ON = "based_on"  # 基づく関係
    IMPROVES = "improves"  # 改善関係


class VectorEmbedding(BaseModel):
    """ベクトル埋め込みを表現するモデル"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    vector: List[float]
    model_name: str
    dimension: int
    created_at: datetime = Field(default_factory=datetime.now)

    @model_validator(mode='after')
    def validate_dimension(self):
        """ベクトルの次元数を検証"""
        if len(self.vector) != self.dimension:
            raise ValueError(f"Vector dimension mismatch: expected {self.dimension}, got {len(self.vector)}")
        return self


class SourceData(BaseModel):
    """データソースを表現するモデル"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    source_id: UUID = Field(default_factory=uuid4)
    source_type: SourceType
    source_url: Optional[str] = None
    source_name: str
    collection_date: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: ProcessingStatus = ProcessingStatus.COLLECTED
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator('source_url')
    def validate_url(cls, v, values):
        """URL形式の検証（source_typeがWEBまたはACADEMIC_DBの場合）"""
        if v is None and values.data.get('source_type') in [SourceType.WEB, SourceType.ACADEMIC_DB, SourceType.ARXIV]:
            raise ValueError("Web/Academic DB sources must have a URL")
        return v


class Document(BaseModel):
    """収集・処理されたドキュメントを表現するモデル"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    document_id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    title: str
    authors: List[str] = Field(default_factory=list)
    publication_date: Optional[datetime] = None
    content_type: ContentType
    raw_content_path: Optional[str] = None  # ファイルパス
    processed_content_path: Optional[str] = None  # ファイルパス
    language: Optional[str] = None
    version: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Segment(BaseModel):
    """ドキュメントのセグメントを表現するモデル"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    segment_id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    content: str
    segment_type: SegmentType
    position: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    vector_embedding: Optional[VectorEmbedding] = None
    created_at: datetime = Field(default_factory=datetime.now)


class Entity(BaseModel):
    """抽出された知識エンティティを表現するモデル"""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "entity_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "name": "Transformer",
                "entity_type": "technology",
                "aliases": ["Transformer model", "Transformer architecture"],
                "description": "自己注意機構を基盤とした自然言語処理モデルで、2017年にGoogle Researchによって発表された。",
                "confidence": 0.95,
                "metadata": {
                    "first_appearance_year": 2017,
                    "creator": "Google Research",
                    "related_papers": ["Attention is All You Need"],
                    "domain": "natural language processing"
                }
            }
        }
    )
    
    entity_id: UUID = Field(default_factory=uuid4)
    name: str
    entity_type: EntityType
    aliases: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    source_segments: List[UUID] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    vector_embedding: Optional[VectorEmbedding] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Relation(BaseModel):
    """エンティティ間の関係を表現するモデル"""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "relation_id": "a1b2c3d4-e5f6-4a5b-9c7d-8e9f0a1b2c3d",
                "source_entity_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "target_entity_id": "11223344-5566-7788-99aa-bbccddeeff00",
                "relation_type": "based_on",
                "description": "Transformerアーキテクチャは自己注意機構に基づいている",
                "confidence": 0.9,
                "metadata": {
                    "first_observed": "2017-06-12",
                    "citation_count": 45,
                    "importance": "high"
                }
            }
        }
    )
    
    relation_id: UUID = Field(default_factory=uuid4)
    source_entity_id: UUID
    target_entity_id: UUID
    relation_type: RelationType
    description: Optional[str] = None
    source_segments: List[UUID] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

    @model_validator(mode='after')
    def validate_different_entities(self):
        """ソースとターゲットが異なるエンティティであることを検証"""
        if self.source_entity_id == self.target_entity_id:
            raise ValueError("Source and target entities must be different")
        return self


class AnalysisType(str, Enum):
    """分析タイプを定義する列挙型"""
    SUMMARY = "summary"  # 要約
    KEYWORDS = "keywords"  # キーワード抽出
    SENTIMENT = "sentiment"  # 感情分析
    TOPIC = "topic"  # トピックモデリング
    CLASSIFICATION = "classification"  # 分類


class TargetType(str, Enum):
    """分析対象タイプを定義する列挙型"""
    DOCUMENT = "document"  # ドキュメント
    SEGMENT = "segment"  # セグメント


class Analysis(BaseModel):
    """分析結果を表現するモデル"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    analysis_id: UUID = Field(default_factory=uuid4)
    target_type: TargetType
    target_id: UUID
    analysis_type: AnalysisType
    result: Dict[str, Any]
    model_used: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchQuery(BaseModel):
    """検索クエリを表現するモデル"""
    query_text: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    limit: int = 10
    offset: int = 0
    semantic_search: bool = True