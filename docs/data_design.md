# データ設計

## 概要

情報収集・知識管理サブシステムでは、多様なデータソースから取得したデータを構造化し、効率的に管理・検索・可視化できるように設計されています。本ドキュメントでは、システム内のデータモデル、スキーマ設計、データベース構成、およびデータ間の関連性について詳細に説明します。

## データモデル

### 1. ソースデータモデル

収集元データソースの情報を管理します。

```plaintext
SourceData {
    source_id: UUID         // ソースの一意識別子
    source_type: Enum       // 論文DB/ウェブ/ローカルファイル等
    source_url: String      // 元URL（該当する場合）
    source_name: String     // ソース名
    collection_date: DateTime // 収集日時
    metadata: JSON          // ソース固有のメタデータ
    status: Enum            // 処理状態（収集済/前処理済/分析済等）
}
```

### 2. ドキュメントモデル

収集・処理されたドキュメントを表現します。

```plaintext
Document {
    document_id: UUID       // ドキュメントの一意識別子
    source_id: UUID         // 関連するソースID
    title: String           // ドキュメントタイトル
    authors: Array<String>  // 著者リスト
    publication_date: Date  // 公開/発行日
    content_type: Enum      // テキスト/PDF/HTML等
    raw_content: Binary     // 元コンテンツ
    processed_content: Text // 前処理済みコンテンツ
    language: String        // 言語コード
    version: String         // バージョン情報
    created_at: DateTime    // 作成日時
    updated_at: DateTime    // 更新日時
    metadata: JSON          // 追加メタデータ
}
```

### 3. セグメントモデル

ドキュメントを検索・分析しやすい単位に分割したセグメントを表現します。

```plaintext
Segment {
    segment_id: UUID        // セグメントの一意識別子
    document_id: UUID       // 関連するドキュメントID
    content: Text           // セグメントのテキスト内容
    segment_type: Enum      // 段落/表/リスト/見出し等
    position: Integer       // ドキュメント内の位置
    metadata: JSON          // セグメント固有メタデータ
    vector_embedding: Array<Float> // ベクトル埋め込み
}
```

### 4. 知識エンティティモデル

抽出された知識エンティティを表現します。

```plaintext
Entity {
    entity_id: UUID         // エンティティの一意識別子
    name: String            // エンティティ名
    entity_type: Enum       // 概念/人物/組織/技術/製品等
    aliases: Array<String>  // 別名リスト
    description: Text       // 説明
    source_segments: Array<UUID> // 出典セグメントIDs
    confidence: Float       // 抽出信頼度
    metadata: JSON          // 追加属性
    vector_embedding: Array<Float> // ベクトル埋め込み
}
```

### 5. 関係モデル

エンティティ間の関係を表現します。

```plaintext
Relation {
    relation_id: UUID       // 関係の一意識別子
    source_entity_id: UUID  // 起点エンティティID
    target_entity_id: UUID  // 終点エンティティID
    relation_type: Enum     // 包含/利用/対立/類似等
    description: Text       // 関係の説明
    source_segments: Array<UUID> // 出典セグメントIDs
    confidence: Float       // 抽出信頼度
    metadata: JSON          // 追加属性
}
```

### 6. 分析結果モデル

ドキュメントやセグメントに対する分析結果を表現します。

```plaintext
Analysis {
    analysis_id: UUID       // 分析の一意識別子
    target_type: Enum       // ドキュメント/セグメント
    target_id: UUID         // 対象ID
    analysis_type: Enum     // 要約/キーワード抽出/感情分析等
    result: JSON            // 分析結果
    model_used: String      // 使用したモデル情報
    created_at: DateTime    // 作成日時
    metadata: JSON          // 追加メタデータ
}
```

### 7. 検索インデックスモデル

効率的な検索のためのインデックス情報を表現します。

```plaintext
SearchIndex {
    index_id: UUID          // インデックスの一意識別子
    target_type: Enum       // インデックス対象タイプ
    target_id: UUID         // 対象ID
    index_type: Enum        // ベクトル/キーワード/メタデータ等
    index_data: Binary      // インデックスデータ
    updated_at: DateTime    // 更新日時
}
```

## データベース設計

システムは複数のデータベースを組み合わせて利用します：

### 1. リレーショナルデータベース (PostgreSQL)

メタデータ、構造化データ、および関係情報を管理します。

#### 主要テーブル
- `sources` - データソース情報
- `documents` - ドキュメント情報
- `segments` - セグメント情報
- `entities` - エンティティ情報
- `relations` - 関係情報
- `analyses` - 分析結果
- `jobs` - 処理ジョブ情報
- `users` - ユーザー情報
- `settings` - システム設定

### 2. ベクトルデータベース (FAISS/Chroma)

セマンティック検索のためのベクトル埋め込みを管理します。

#### 主要コレクション
- `document_embeddings` - ドキュメントレベルの埋め込み
- `segment_embeddings` - セグメントレベルの埋め込み
- `entity_embeddings` - エンティティの埋め込み

### 3. グラフデータベース (Neo4j)

エンティティ間の関係性を管理し、グラフクエリと可視化をサポートします。

#### 主要ノードとエッジ
- ノード: `Entity` (type属性で分類)
- エッジ: `Relation` (type属性で関係タイプを分類)

### 4. ファイルシステム

生のドキュメントデータと処理済みファイルを保存します。

#### ディレクトリ構造
```
data/
├── raw/                  # 収集された生データ
│   ├── {source_type}/    # ソースタイプ別
│   └── {date}/           # 日付別
├── processed/            # 前処理済みデータ
│   ├── {source_type}/    # ソースタイプ別
│   └── {date}/           # 日付別
├── exports/              # エクスポートされたデータ
└── temp/                 # 一時ファイル
```

## データスキーマの詳細

### PostgreSQLデータベーススキーマ

```sql
-- ソーステーブル
CREATE TABLE sources (
    source_id UUID PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,
    source_url TEXT,
    source_name VARCHAR(255) NOT NULL,
    collection_date TIMESTAMP NOT NULL,
    metadata JSONB,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ドキュメントテーブル
CREATE TABLE documents (
    document_id UUID PRIMARY KEY,
    source_id UUID REFERENCES sources(source_id),
    title TEXT NOT NULL,
    authors TEXT[],
    publication_date DATE,
    content_type VARCHAR(50) NOT NULL,
    raw_content_path TEXT, -- ファイルパス
    processed_content_path TEXT, -- ファイルパス
    language VARCHAR(10),
    version VARCHAR(20),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- セグメントテーブル
CREATE TABLE segments (
    segment_id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(document_id),
    content TEXT NOT NULL,
    segment_type VARCHAR(50) NOT NULL,
    position INTEGER NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- エンティティテーブル
CREATE TABLE entities (
    entity_id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    aliases TEXT[],
    description TEXT,
    confidence FLOAT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- エンティティ出典関連テーブル
CREATE TABLE entity_sources (
    entity_id UUID REFERENCES entities(entity_id),
    segment_id UUID REFERENCES segments(segment_id),
    PRIMARY KEY (entity_id, segment_id)
);

-- 関係テーブル
CREATE TABLE relations (
    relation_id UUID PRIMARY KEY,
    source_entity_id UUID REFERENCES entities(entity_id),
    target_entity_id UUID REFERENCES entities(entity_id),
    relation_type VARCHAR(50) NOT NULL,
    description TEXT,
    confidence FLOAT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 関係出典関連テーブル
CREATE TABLE relation_sources (
    relation_id UUID REFERENCES relations(relation_id),
    segment_id UUID REFERENCES segments(segment_id),
    PRIMARY KEY (relation_id, segment_id)
);

-- 分析結果テーブル
CREATE TABLE analyses (
    analysis_id UUID PRIMARY KEY,
    target_type VARCHAR(50) NOT NULL,
    target_id UUID NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    result JSONB NOT NULL,
    model_used VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);
```

### ベクトルデータベーススキーマ (Chroma例)

```python
# ベクトル埋め込みコレクション定義
segment_collection = chromadb.create_collection(
    name="segment_embeddings",
    metadata={"description": "Embeddings for document segments"}
)

# メタデータを含むベクトル追加例
segment_collection.add(
    ids=[segment.segment_id],
    embeddings=[segment.vector_embedding],
    metadatas=[{
        "document_id": segment.document_id,
        "segment_type": segment.segment_type,
        "position": segment.position,
        "language": document.language
    }],
    documents=[segment.content]
)
```

### Neo4jグラフデータベーススキーマ

```cypher
// エンティティノード作成
CREATE (e:Entity {
    entity_id: $entity_id,
    name: $name,
    entity_type: $entity_type,
    description: $description,
    confidence: $confidence
})

// エンティティタイプ別インデックス
CREATE INDEX entity_type_idx FOR (e:Entity) ON (e.entity_type)

// 関係定義
CREATE (source:Entity {entity_id: $source_id})
-[:RELATES_TO {
    relation_id: $relation_id,
    relation_type: $relation_type,
    description: $description,
    confidence: $confidence
}]->
(target:Entity {entity_id: $target_id})
```

## データ関連性

システム内の様々なデータモデル間の関連性は以下のとおりです：

1. **ソース → ドキュメント**: 1対多の関係。一つのソースから複数のドキュメントが生成される場合があります。

2. **ドキュメント → セグメント**: 1対多の関係。各ドキュメントは複数のセグメントに分割されます。

3. **セグメント → エンティティ**: 多対多の関係。一つのセグメントから複数のエンティティが抽出され、一つのエンティティが複数のセグメントから参照される場合があります。

4. **エンティティ → 関係**: 多対多の関係。各エンティティは他の複数のエンティティと関係を持ち得ます。

5. **ドキュメント/セグメント → 分析結果**: 1対多の関係。一つのドキュメントやセグメントに対して複数の分析が実行される場合があります。

## データアクセスパターン

主要なデータアクセスパターンと最適化方針は以下のとおりです：

1. **セマンティック検索**: ベクトル埋め込みを使用したセマンティック類似性検索に最適化
   - インデックス: `segment_embeddings`のベクトルインデックス

2. **メタデータフィルタリング**: ドキュメント属性による絞り込み検索に最適化
   - インデックス: `documents`テーブルの`publication_date`, `authors`, `language`等

3. **グラフ探索**: エンティティ間の関係性探索に最適化
   - インデックス: エンティティタイプ、関係タイプによるインデックス

4. **全文検索**: キーワードベースの検索に最適化
   - インデックス: `segments.content`のテキストインデックス

## データ整合性と参照整合性

1. **外部キー制約**: ドキュメント-ソース、セグメント-ドキュメント間の参照整合性を保証

2. **一意性制約**: エンティティの一意性を保証
   ```cypher
   CREATE CONSTRAINT entity_name_type_unique FOR (e:Entity) REQUIRE (e.name, e.entity_type) IS UNIQUE
   ```

3. **データの更新と伝播**: 元データが更新された場合の派生データの更新戦略
   - ドキュメント更新時のセグメント再生成
   - エンティティ更新時の関連ベクトル再計算

## データマイグレーション戦略

1. **スキーマバージョニング**: データベーススキーマのバージョン管理
   - バージョンテーブルによるマイグレーション追跡

2. **段階的マイグレーション**: 大規模データセットの移行手順
   - バッチ処理による段階的データ移行
   - ダウンタイムを最小化する更新戦略

3. **バックアップと復元**: マイグレーション前のデータ保護
   - 完全バックアップとポイントインタイムリカバリ機能

## データ処理のパイプライン

各データモデルがデータフローの中でどのように生成・変換・保存されるかを示します。

```
ソース取得 → ドキュメント抽出 → セグメント分割 → ベクトル化 → エンティティ抽出 → 関係抽出 → グラフ構築
```

各ステップで必要なデータ変換と保存先データベースを適切に選択し、効率的なデータ処理フローを実現します。

## 拡張性への考慮

1. **スキーマ拡張性**: 新しい属性やエンティティタイプの追加が容易な設計
   - メタデータフィールドの活用
   - エンティティタイプの動的追加

2. **スケーラビリティ**: データ量の増加に対応する設計
   - パーティショニング戦略
   - シャーディング考慮点

3. **新データソース対応**: 新たなデータソースの統合を容易にする設計
   - プラグイン形式のデータコネクタ
   - 柔軟なスキーママッピング

## データ保護とセキュリティ

1. **アクセス制御**: データアクセスの制限と監視
   - ロールベースアクセス制御（RBAC）
   - 操作ログの記録

2. **データ暗号化**: 機密データの保護
   - 保存データの暗号化
   - 通信経路の暗号化

3. **監査追跡**: データ変更の追跡
   - 変更履歴の保持
   - 監査ログの生成

## パフォーマンス最適化

1. **クエリ最適化**: 頻繁に実行されるクエリの最適化
   - クエリプランの分析と改善
   - 適切なインデックス戦略

2. **キャッシュ戦略**: 頻繁にアクセスされるデータのキャッシュ
   - 検索結果キャッシュ
   - メタデータキャッシュ

3. **非同期処理**: 重い処理の非同期実行
   - バックグラウンドジョブによるインデックス更新
   - 定期的なデータ集計と前計算

## 実装ガイドライン

1. **ORMマッピング**: SQLデータベースとのマッピング
   - SQLAlchemyを使用したモデル定義
   - マイグレーションスクリプトの管理

2. **ベクトルデータベース連携**: 効率的なベクトル操作
   - バッチ処理による埋め込み生成
   - 近似最近傍検索の活用

3. **グラフデータベース連携**: 関係データの効率的な管理
   - バルクインポート処理
   - 効率的なサブグラフ取得