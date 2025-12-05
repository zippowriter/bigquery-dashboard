# BigQuery Dashboard

BigQuery テーブル利用状況分析ツール。組織内の BigQuery テーブルの参照状況を可視化し、未使用・低利用テーブルの特定を支援します。

## 機能

- **テーブル一覧取得**: 複数プロジェクトからテーブルメタデータを収集
- **参照回数分析**: JOBS ログからテーブル参照回数・ユニークユーザー数を集計
- **テーブルリネージ情報取得**: Lineage API からリネージ情報を収集
- **利用状況可視化**: Streamlit ダッシュボードによる視覚的な分析

## 必要条件

- Python 3.13
- [uv](https://docs.astral.sh/uv/) (パッケージマネージャー)
- Google Cloud プロジェクトへのアクセス権限

## セットアップ

```bash
# 依存関係のインストール
uv sync

# Google Cloud 認証（未設定の場合）
gcloud auth application-default login
```

## 使い方

### ダッシュボード起動

```bash
uv run streamlit run main.py
```

### 開発コマンド

```bash
# テスト実行
uv run pytest

# リント
uv run ruff check

# フォーマット
uv run ruff format

# 型チェック
uv run pyright
```

## ライセンス

MIT
