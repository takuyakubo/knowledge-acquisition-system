# 情報収集・知識管理サブシステム

## 概要

本リポジトリは、R&Dワークフロー自動化システムの一部として機能する情報収集・知識管理サブシステムの実装です。多様なソースからデータを収集し、前処理を行い、知識として構造化・保存・可視化するための基盤となるサブシステムを提供します。

## 主要機能

- 学術論文、Webページ、ローカルファイルなど多様なソースからのデータ収集
- テキストの前処理と構造化
- LLMを活用した知識抽出とベクトル化
- セマンティック検索機能
- 知識グラフの構築と可視化
- ドキュメント管理と知見共有

## インストールと実行方法

### 必要環境
- Python 3.9以上
- pip
- Git
- Docker (オプション)

### セットアップ手順

1. リポジトリのクローン
   ```bash
   git clone https://github.com/takuyakubo/knowledge-acquisition-system.git
   cd knowledge-acquisition-system
   ```

2. 仮想環境の作成と有効化
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS / Linux
   source venv/bin/activate
   ```

3. 依存パッケージのインストール
   ```bash
   pip install -r requirements.txt
   ```

4. 環境変数の設定
   ```bash
   cp .env.example .env
   # .envファイルを編集して必要な設定を行ってください
   ```

5. アプリケーションの実行

   APIサーバーの起動:
   ```bash
   python -m src.api.main
   ```

   Streamlit UIの起動:
   ```bash
   streamlit run src/ui/app.py
   ```

### Dockerでの実行

```bash
# コンテナのビルドと起動
docker-compose up --build

# バックグラウンドで実行
docker-compose up -d
```

## 開発ガイド

### テストの実行
```bash
pytest
```

### コードスタイルチェック
```bash
flake8
```

## リポジトリ構成

```
knowledge-acquisition-system/
├── .github/workflows/    # GitHub Actions ワークフロー
├── data/                 # データファイル（自動生成）
├── docs/                 # 設計ドキュメント
│   ├── architecture.md   # アーキテクチャ設計
│   ├── api.md            # API仕様
│   ├── data_flow.md      # データフロー
│   └── modules.md        # モジュール詳細設計
├── logs/                 # ログファイル（自動生成）
├── src/                  # ソースコード
├── tests/                # テストコード
├── .env.example          # 環境変数テンプレート
├── .gitignore            # Git除外設定
├── docker-compose.yml    # Docker Compose設定
├── Dockerfile            # Dockerファイル
├── LICENSE               # ライセンス
├── README.md             # 本ファイル
└── requirements.txt      # 依存パッケージリスト
```

## 開発環境

- Python 3.9以上
- 依存ライブラリ: Langchain, FastAPI, Streamlit, その他

## 詳細情報

システムの詳細な設計や仕様については、[docs](docs/)ディレクトリ内のドキュメントを参照してください。

## コントリビュート

プロジェクトへの貢献を歓迎します。貢献方法については[CONTRIBUTING.md](CONTRIBUTING.md)を参照してください。

## 変更履歴

プロジェクトの変更履歴については[CHANGELOG.md](CHANGELOG.md)を参照してください。
