# ソースコード構成

このディレクトリには情報収集・知識管理サブシステムの実装コードが含まれています。

## ディレクトリ構造

```
src/
├── data_collection/      # データ収集・前処理モジュール
│   ├── connectors/       # 各種データソースコネクタ
│   ├── processors/       # 前処理パイプライン
│   └── scheduler.py      # スケジューリング機能
│
├── knowledge_extraction/ # 知識抽出・インデキシングモジュール
│   ├── analyzers/        # テキスト分析コンポーネント
│   ├── vectorization/    # ベクトル化機能
│   └── search/           # 検索エンジン
│
├── knowledge_graph/      # 知識グラフ構築・可視化モジュール
│   ├── relation_extraction/ # 関係抽出コンポーネント
│   ├── graph_db/         # グラフDBコネクタ
│   └── visualization/    # 可視化コンポーネント
│
├── document_management/  # ドキュメント管理モジュール
│   ├── version_control/  # バージョン管理機能
│   ├── metadata/         # メタデータ管理
│   └── export/           # エクスポート機能
│
├── api/                  # API実装
│   ├── routes/           # APIエンドポイント
│   └── middleware/       # APIミドルウェア
│
├── common/               # 共通ユーティリティ
│   ├── config/           # 設定管理
│   ├── db/               # データベース接続
│   └── logger/           # ロギング機能
│
└── ui/                   # ユーザーインターフェース(Streamlit)
    ├── pages/            # UIページ
    └── components/       # UI共通コンポーネント
```

## 実装方針

- モジュール性と疎結合を重視
- 依存性注入パターンの活用
- プラグイン形式の拡張性確保
- 十分なテストカバレッジ
- ロギングと監視の充実