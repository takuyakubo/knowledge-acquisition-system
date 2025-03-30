# API仕様

## 内部APIエンドポイント

本システムは以下の内部APIエンドポイントを提供し、他のサブシステムとの連携や管理インターフェースからの利用を可能にします。

### データ収集 API

#### `POST /collect`
データ収集ジョブを開始します。

**リクエスト例**:
```json
{
  "source_type": "arxiv",
  "query": "artificial intelligence",
  "max_results": 50,
  "schedule": "daily"
}
```

**レスポンス**:
```json
{
  "job_id": "collect-123",
  "status": "scheduled",
  "estimated_completion": "2025-03-31T10:00:00Z"
}
```

### 前処理 API

#### `POST /preprocess`
収集済みデータの前処理を実行します。

**リクエスト例**:
```json
{
  "data_id": "data-456",
  "pipeline": ["clean_text", "extract_metadata", "segment"]
}
```

### 分析 API

#### `POST /analyze`
テキスト分析を実行します。

**リクエスト例**:
```json
{
  "text_id": "text-789",
  "analysis_types": ["summarize", "keywords", "entities"]
}
```

### 検索 API

#### `GET /search`
知識ベースを検索します。

**リクエスト例**:
```
/search?q=machine%20learning&type=semantic&limit=10
```

**レスポンス**:
```json
{
  "results": [
    {
      "id": "doc-123",
      "title": "Introduction to Machine Learning",
      "snippet": "...",
      "score": 0.92,
      "metadata": { ... }
    },
    ...
  ],
  "total": 42
}
```

### グラフ API

#### `GET /graph`
知識グラフデータにアクセスします。

**リクエスト例**:
```
/graph?entity=neural_networks&depth=2&relations=uses,part_of
```

### ドキュメント API

#### `GET /document/{id}`
特定のドキュメントを取得します。

**レスポンス例**:
```json
{
  "id": "doc-123",
  "title": "...",
  "content": "...",
  "metadata": { ... },
  "vectors": { ... },
  "version": "1.2"
}
```

## 外部連携インターフェース

### 仮説生成・検証サブシステム連携

知識ベースから関連情報を提供するためのインターフェースを公開します。

#### `GET /knowledge/relevant`
特定のクエリに関連する知識を返します。

### フィードバック受信インターフェース

#### `POST /feedback`
他サブシステムからのフィードバックを受け取り、知識ベースを改善します。

### 認証・設定連携

#### `GET /config`
共通基盤サブシステムから設定情報を取得します。