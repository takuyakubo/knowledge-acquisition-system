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
