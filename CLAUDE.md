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

### テスト実行

全テスト実行:
```
pytest
```

特定ディレクトリのテスト実行:
```
pytest tests/unit/
pytest tests/integration/
```

特定のモジュールテスト実行:
```
pytest tests/unit/data_collection/
```

### テスト構造

```
tests/
├── unit/                 # 単体テスト
│   ├── data_collection/  # データ収集モジュールテスト
│   ├── knowledge_extraction/ # 知識抽出モジュールテスト
│   └── ...
├── integration/          # 統合テスト
│   ├── data_flow/        # データフロー統合テスト
│   └── api/              # API統合テスト
├── fixtures/             # テストフィクスチャ
│   ├── responses/        # モックAPIレスポンス
│   └── documents/        # サンプルデータ
└── conftest.py           # pytest共通設定
```

### テスト設計指針

- **単体テスト**: 各クラスや関数の独立した機能を検証
- **統合テスト**: モジュール間の相互作用やデータフローを検証
- **モック活用**: 外部依存（API、DB等）をモックして分離テスト
- **パラメータ化**: 様々な入力パターンを効率的にテスト
- **非同期テスト**: `pytest-asyncio`プラグインを使用して非同期関数をテスト
  - `@pytest.mark.asyncio`でテスト関数を装飾
  - `@pytest_asyncio.fixture`で非同期フィクスチャを定義

### 非同期テストの実装

```python
# 非同期テスト用プラグイン
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock

# 非同期テストクラス
@pytest.mark.asyncio
class TestAsyncClass:
    # 非同期フィクスチャ
    @pytest_asyncio.fixture
    async def async_fixture(self):
        # 非同期のセットアップコード
        result = await some_async_operation()
        return result
    
    # 非同期テストメソッド
    async def test_async_method(self, async_fixture):
        # テストロジック
        result = await some_other_async_operation()
        assert result == expected_value
```

### コードスタイルチェック

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
    async def get_paper_by_id(self, arxiv_id: str) -> Dict[str, Any]: ...
    
    @abstractmethod
    async def collect_papers(self, query: str, category: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None, max_results: int = 100) -> List[Dict[str, Any]]: ...
    
    @abstractmethod
    async def download_pdf(self, arxiv_id: str, target_path: Optional[str] = None) -> str: ...
    
    @abstractmethod
    async def extract_text_from_pdf(self, pdf_path: str) -> str: ...
    
    @abstractmethod
    async def segment_paper(self, arxiv_id: str, text_content: Optional[str] = None) -> List[Segment]: ...
    
    @abstractmethod
    async def extract_entities(self, arxiv_id: str, segments: Optional[List[Segment]] = None) -> List[Entity]: ...
    
    @abstractmethod
    async def extract_relations(self, arxiv_id: str, entities: Optional[List[Entity]] = None) -> List[Relation]: ...
    
    @abstractmethod
    async def get_paper_metadata(self, arxiv_id: str) -> Dict[str, Any]: ...
    
    @abstractmethod
    async def get_vector_embeddings(self, arxiv_id: str) -> Dict[str, List[float]]: ...
```

### arXivコネクタのテスト

```python
# 単体テスト
class TestArxivConnector:
    @pytest.fixture
    def arxiv_connector(self):
        # モック依存関係を設定
        db_mock = MagicMock()
        vector_db_mock = MagicMock()
        storage_mock = MagicMock()
        
        # テスト用の一時ディレクトリを使用するよう設定
        with patch('os.makedirs'):
            with patch('src.common.config.get_config') as mock_get_config:
                mock_get_config.return_value = {'data_dir': '/tmp/test_data'}
                return ArxivConnector(db_connection=db_mock, vector_db_client=vector_db_mock)
    
    @pytest.mark.asyncio
    async def test_search_papers(self, arxiv_connector):
        # search_papers()メソッドのテスト実装
        # 将来実装される関数の動作を検証
        ...

# 統合テスト
@pytest.mark.asyncio
class TestArxivDataFlow:
    @pytest_asyncio.fixture
    async def mock_arxiv_connector(self):
        # モック化されたarXivコネクタを提供するフィクスチャ
        # 実際のAPIを呼び出さずにテストできるようにするためのモック
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
            }
        ]
        
        # search_papers のモック実装
        async def mock_search_papers(*args, **kwargs):
            return sample_papers
        
        # 各メソッドをモック実装
        connector.search_papers = AsyncMock(side_effect=mock_search_papers)
        connector.download_pdf = AsyncMock(return_value="/tmp/test_data/raw/arxiv/2301.12345.pdf")
        connector.extract_text_from_pdf = AsyncMock(return_value="Sample text content...")
        
        # セグメント化のモック
        async def mock_segment_paper(arxiv_id, text_content=None):
            segments = [
                Segment(
                    segment_id=uuid4(),
                    document_id=UUID('11111111-1111-1111-1111-111111111111'),
                    content="Abstract content",
                    segment_type="abstract",
                    position=0,
                    metadata={"source": "arxiv", "paper_id": arxiv_id}
                ),
                Segment(
                    segment_id=uuid4(),
                    document_id=UUID('11111111-1111-1111-1111-111111111111'),
                    content="Introduction content",
                    segment_type="introduction",
                    position=1,
                    metadata={"source": "arxiv", "paper_id": arxiv_id}
                )
            ]
            return segments
            
        connector.segment_paper = AsyncMock(side_effect=mock_segment_paper)
        
        return connector
    
    async def test_complete_paper_processing_flow(self, mock_arxiv_connector):
        # 論文処理の完全なフローをテスト
        papers = await mock_arxiv_connector.search_papers(query="quantum")
        assert len(papers) == 1
        assert papers[0]["id"] == "2301.12345"
        
        # 最初の論文を処理
        paper_id = papers[0]["id"]
        
        # PDFをダウンロード
        pdf_path = await mock_arxiv_connector.download_pdf(paper_id)
        assert pdf_path.endswith(f"{paper_id}.pdf")
        
        # テキストを抽出
        text_content = await mock_arxiv_connector.extract_text_from_pdf(pdf_path)
        
        # テキストをセグメント化
        segments = await mock_arxiv_connector.segment_paper(paper_id, text_content)
        assert len(segments) == 2
        assert segments[0].segment_type == "abstract"
        assert segments[1].segment_type == "introduction"
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
   - 適切な例外処理と伝播

4. **データバリデーション**:
   - Pydanticによる強力な型チェックとバリデーション
   - モデル間の関係整合性の保証

5. **テスト駆動開発**:
   - インターフェース実装前にテストを先行して作成
   - モックとスタブを活用した依存関係の分離
   - 単体テストと統合テストの使い分け

6. **ユーティリティ関数の実装**:
   - `get_logger`関数: モジュールごとのログ管理
   - `get_config`関数: 設定情報の一元管理

7. **Pydanticモデルの最新スタイル対応**:
   - Pydantic v2形式でのモデル定義
   - `model_config = ConfigDict()`を使用したメタデータ設定
   - バリデーターとエニュメレーション型の活用

## 開発知見：ArXivコネクタ実装

### 実装アプローチ

1. **非同期処理の活用**:
   - `asyncio`と`aiohttp`を使用して効率的な非同期処理を実現
   - API呼び出しやファイル操作を並行実行して処理速度を向上

2. **外部ライブラリの活用**:
   - `arxiv`: arXiv APIへのアクセスを簡素化するライブラリ
   - `pdfminer.six`: PDFからテキスト抽出用ライブラリ
   - `numpy`: ベクトル演算用（ダミー実装に使用）

3. **段階的データ処理パイプライン**:
   - 検索 → PDF取得 → テキスト抽出 → セグメント化 → エンティティ抽出 → 関係抽出
   - 各段階でエラーハンドリングを実装し、部分的な成功も記録

4. **セグメント化アルゴリズム**:
   - 正規表現パターンを用いて論文の各セクション（序論、方法、結果など）を検出
   - アブストラクトを最初のセグメントとして特別処理
   - セグメント数が少ない場合は段落分割をフォールバックとして使用

5. **エンティティ抽出の簡易実装**:
   - 論文自体、著者、カテゴリを基本エンティティとして抽出
   - 将来的にはLLMベースの高度な抽出を実装予定

6. **モックとスタブの利用**:
   - テスト時には実際のAPIを呼び出さずにモックを使用
   - ベクトル化処理もダミー実装で対応

### テスト設計の改善点

1. **単体テストの強化**:
   - 全メソッドを網羅するテストケースの作成
   - 依存関係をモック化して独立した検証
   - 非同期テスト用の`pytest.mark.asyncio`デコレータの活用

2. **統合テスト**:
   - データフロー全体を検証する統合テスト
   - 一連の処理（検索→ダウンロード→抽出→分析）の検証

3. **エラーケースのテスト**:
   - 様々なエラー状況（API障害、ファイル不存在など）のテスト
   - エラー伝播の検証

### 今後の改善点

1. **実際のLLM統合**:
   - セグメント化、エンティティ抽出、関係抽出でのLLM活用
   - ベクトル埋め込みの本格実装（外部埋め込みAPIの利用）

2. **パフォーマンスチューニング**:
   - 大量論文処理時の最適化
   - キャッシュ機構の導入

3. **データ永続化**:
   - データベースへの保存機能の実装
   - ベクトルデータベース連携

## 開発TODO

- [x] プロジェクト初期構築
- [x] 基本的なAPI実装
- [x] UI基本画面実装
- [x] データモデル設計（Pydantic）
- [x] インターフェース設計
- [x] テスト基盤整備（単体/統合テスト）
- [x] arXivコネクタ実装
- [ ] ベクトル検索機能実装
- [ ] 知識グラフ構築
- [ ] Web情報収集コネクタ実装

## デプロイ方法

1. `.env`ファイルで環境設定
2. `docker-compose up -d`でコンテナ起動
3. `http://localhost:8501`でUIアクセス、`http://localhost:8000`でAPIアクセス