# Technology Stack

## Architecture

レイヤードアーキテクチャを採用。設定、レイアウト、サーバー実行を分離し、テスト容易性と保守性を確保。

## Core Technologies

- **Language**: Python 3.13+
- **Framework**: Dash 2.18.x (Plotly製ダッシュボードフレームワーク)
- **Runtime**: Python (uv によるパッケージ管理)

## Key Libraries

- **google-cloud-bigquery**: BigQuery APIクライアント
- **pydantic**: 設定・データモデルのバリデーション
- **dash**: Webダッシュボードフレームワーク

## Development Standards

### Type Safety
- Pyright による静的型検査
- `reportUnknownVariableType: error` で厳格な型チェック
- 全関数に型アノテーション必須

### Code Quality
- Ruff によるリンティング・フォーマット
- 最大行長: 200文字
- isort 設定: `combine-as-imports`, `lines-between-types=1`

### Docstring & Comment
- Docstringとコメントは日本語で記述
- プロダクトコードとテストコードの両方にDocstringを記述する
- モジュール、クラス、メソッドのDocstringはGoogle Styleを採用する
- コメントにはwhy notを記述

### Testing
- pytest による単体テスト
- `tests/unit/` に単体テスト配置
- テスト関数: `test_*` パターン

#### Unit Test Principles
- フレームワークやライブラリの動作をテストしない（Pydantic、Dashの動作はそれぞれのプロジェクトがテスト済み）
- 同じことを複数の方法でテストしない（引数を変えて同じ関数を何度もテストするのは冗長）
- 存在確認テストは不要（関数が存在するかどうかはimportエラーでわかる）
- 定数の値をテストしない（定数を変えたらテストも変えるだけで何も守れない）
- コード構造（AST）をテストしない（`if __name__`があるかどうかは人間がレビューすべき）

## Development Environment

### Required Tools
- Python 3.13+
- uv (パッケージマネージャ)

### Common Commands
```bash
# Format: task format
uv run ruff format

# Lint: task lint
uv run ruff check

# Test: task test
uv run pytest

# Type check: task type-check
uv run pyright
```

## Key Technical Decisions

- **Dash選択**: Plotlyエコシステム活用、Pythonのみでリアクティブダッシュボード構築
- **Pydantic設定**: 型安全な設定管理、バリデーション自動化
- **uv採用**: 高速なパッケージ管理、lockファイルによる再現性確保
- **レイヤー分離**: `config`, `layout`, `server`, `app` の責務分離

---
_Document standards and patterns, not every dependency_
