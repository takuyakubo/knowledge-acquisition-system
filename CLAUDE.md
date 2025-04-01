# CLAUDE.md - 知識収集システム開発ガイド

このドキュメントは、「情報収集・知識管理サブシステム」プロジェクトに関するClaudeの開発支援情報を記録しています。

## プロジェクト概要

本システムは、R&Dワークフロー自動化システムの一部として機能する情報収集・知識管理サブシステムです。
多様なソースからデータを収集し、前処理を行い、知識として構造化・保存・可視化する基盤を提供します。

### 主要機能

- 学術論文、Webページ、ローカルファイルからのデータ収集
- テキストの前処理と構造化
- LLMを活用した知識抽出とベクトル化
- セマンティック検索機能
- 知識グラフの構築と可視化
- ドキュメント管理と知見共有

## 開発環境

- Python 3.9以上
- 主要パッケージ: 
  - FastAPI (API実装)
  - Streamlit (UI実装)
  - Langchain (LLM連携)
  - FAISS/Chroma (ベクトルDB)
  - Pydantic (データモデル定義)

## ディレクトリ構造

```
knowledge-acquisition-system/
├── src/               # ソースコード
│   ├── api/           # APIサーバー実装
│   ├── common/        # 共通ユーティリティ
│   ├── data_collection/ # データ収集モジュール
│   │   ├── arxiv/     # arXivコネクタ
│   │   ├── interfaces.py # コネクタインターフェース
│   │   └── factory.py # コネクタファクトリー
│   ├── knowledge_extraction/ # 知識抽出モジュール
│   │   └── entity_model.py # エンティティモデル定義
│   ├── knowledge_graph/ # 知識グラフモジュール
│   ├── document_management/ # ドキュメント管理
│   └── ui/           # Streamlit UI
├── tests/            # テストコード
├── data/             # 収集・生成データ
├── logs/             # ログファイル
└── docs/             # ドキュメント
```

## 開発ガイドライン

### コーディング規約

- PEP 8スタイルガイドに準拠
- Black/Flake8/isortによるフォーマット
- Docstringを各関数・クラスに記述（Google Style推奨）
- Pydanticモデルを活用したデータバリデーション

### テスト

テスト実行:
```
pytest
```

コードスタイルチェック:
```
flake8
black --check .
isort --check-only .
```

### 実行方法

#### ローカル環境

1. APIサーバー起動:
```
python -m src.api.main
```

2. Streamlit UI起動:
```
streamlit run src/ui/app.py
```

#### Docker環境

コンテナビルド・起動:
```
docker-compose up --build
```

## 主要モジュール

1. **データ収集モジュール**: 多様なソースからデータを収集
   - **インターフェース設計**: `DataSourceConnector`, `AcademicDataConnector`, `ArxivConnectorInterface`
   - **コネクタパターン**: 各データソース用の専用コネクタ実装
   - **ファクトリーパターン**: コネクタの動的生成と管理

2. **知識抽出モジュール**: テキストから知識を抽出・ベクトル化
   - **エンティティモデル**: `Entity`, `Relation`, `Segment`などのPydanticモデル
   - **列挙型の活用**: `EntityType`, `RelationType`などでデータの一貫性確保
   - **バリデーション**: Pydanticバリデータでデータ整合性を検証

3. **知識グラフモジュール**: エンティティ間の関係を抽出・可視化

4. **ドキュメント管理モジュール**: バージョン管理・知見共有

## データモデル設計

### エンティティモデル

```python
class Entity(BaseModel):
    entity_id: UUID
    name: str
    entity_type: EntityType
    aliases: List[str]
    description: Optional[str]
    source_segments: List[UUID]
    confidence: float
    metadata: Dict[str, Any]
    vector_embedding: Optional[VectorEmbedding]
```

### 関係モデル

```python
class Relation(BaseModel):
    relation_id: UUID
    source_entity_id: UUID
    target_entity_id: UUID
    relation_type: RelationType
    description: Optional[str]
    source_segments: List[UUID]
    confidence: float
    metadata: Dict[str, Any]
```

## コネクタインターフェース設計

### データソースコネクタ

```python
class DataSourceConnector(ABC):
    @abstractmethod
    async def initialize(self) -> None: ...
    
    @abstractmethod
    async def get_source_info(self) -> SourceData: ...
    
    @abstractmethod
    async def search(self, query: str, **kwargs) -> List[Dict[str, Any]]: ...
    
    @abstractmethod
    async def collect(self, query: str, **kwargs) -> List[Dict[str, Any]]: ...
    
    @abstractmethod
    async def get_document(self, document_id: Union[str, UUID]) -> Document: ...
```

### arXivコネクタ

```python
class ArxivConnectorInterface(AcademicDataConnector):
    @abstractmethod
    async def search_papers(self, query: str, category: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None, max_results: int = 100) -> List[Dict[str, Any]]: ...
    
    @abstractmethod
    async def download_pdf(self, arxiv_id: str, target_path: Optional[str] = None) -> str: ...
    
    @abstractmethod
    async def extract_entities(self, arxiv_id: str, segments: Optional[List[Segment]] = None) -> List[Entity]: ...
```

## API概要

- `/collect` - データ収集ジョブの開始
- `/preprocess` - データ前処理の実行
- `/analyze` - テキスト分析の実行
- `/search` - 知識ベースの検索
- `/graph` - 知識グラフデータの取得
- `/document/{id}` - ドキュメント取得

## 実装のポイント

1. **インターフェース先行設計**:
   - 抽象基底クラスでデータソースの操作を標準化
   - 具体的な実装を後で追加可能な柔軟な設計

2. **エラー処理の一貫性**:
   - 専用例外クラスで様々なエラー状態を表現
   - 例外階層を活用した細かいエラーハンドリング

3. **非同期処理**:
   - asyncioを活用した効率的な非同期IO処理
   - リトライ機能付きAPI呼び出し

4. **データバリデーション**:
   - Pydanticによる強力な型チェックとバリデーション
   - モデル間の関係整合性の保証

## 開発TODO

- [x] プロジェクト初期構築
- [x] 基本的なAPI実装
- [x] UI基本画面実装
- [x] データモデル設計（Pydantic）
- [x] インターフェース設計
- [ ] データ収集コネクタ実装
- [ ] ベクトル検索機能実装
- [ ] 知識グラフ構築
- [ ] テスト拡充

## デプロイ方法

1. `.env`ファイルで環境設定
2. `docker-compose up -d`でコンテナ起動
3. `http://localhost:8501`でUIアクセス、`http://localhost:8000`でAPIアクセス