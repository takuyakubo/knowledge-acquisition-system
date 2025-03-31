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

## ディレクトリ構造

```
knowledge-acquisition-system/
├── src/               # ソースコード
│   ├── api/           # APIサーバー実装
│   ├── common/        # 共通ユーティリティ
│   ├── data_collection/ # データ収集モジュール
│   ├── knowledge_extraction/ # 知識抽出モジュール
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
2. **知識抽出モジュール**: テキストから知識を抽出・ベクトル化
3. **知識グラフモジュール**: エンティティ間の関係を抽出・可視化
4. **ドキュメント管理モジュール**: バージョン管理・知見共有

## API概要

- `/collect` - データ収集ジョブの開始
- `/preprocess` - データ前処理の実行
- `/analyze` - テキスト分析の実行
- `/search` - 知識ベースの検索
- `/graph` - 知識グラフデータの取得
- `/document/{id}` - ドキュメント取得

## 開発TODO

- [x] プロジェクト初期構築
- [x] 基本的なAPI実装
- [x] UI基本画面実装
- [ ] データ収集コネクタ実装
- [ ] ベクトル検索機能実装
- [ ] 知識グラフ構築
- [ ] テスト拡充

## デプロイ方法

1. `.env`ファイルで環境設定
2. `docker-compose up -d`でコンテナ起動
3. `http://localhost:8501`でUIアクセス、`http://localhost:8000`でAPIアクセス