# Technology Stack

## Architecture

クリーンアーキテクチャに基づくレイヤー分離設計。ドメイン層を中心に、依存性の方向を内側に保つ。

## Core Technologies

- **Language**: Python 3.13
- **Framework**: Streamlit (ダッシュボード UI)
- **Data**: Google Cloud BigQuery, pandas

## Key Libraries

- **google-cloud-bigquery**: BigQuery API クライアント
- **pydantic**: データバリデーション・モデル定義
- **pandas**: データ加工・分析
- **streamlit**: インタラクティブダッシュボード

## Development Standards

### Type Safety
- pyright による静的型チェック
- Pydantic BaseModel によるランタイム型検証

### Code Quality
- ruff によるリント・フォーマット統一
- pytest によるテスト（unit / integration 分離）

### Testing
```bash
uv run pytest tests/unit -v      # ユニットテスト
uv run pytest tests/integration  # 統合テスト
```

## Development Environment

### Required Tools
- Python 3.13
- uv (パッケージマネージャー)
- mise (バージョン管理、optional)

### Common Commands
```bash
# Dev: uv run streamlit run main.py
# Build: uv build
# Test: uv run pytest
# Lint: uv run ruff check
# Format: uv run ruff format
# Type check: uv run pyright
```

## Key Technical Decisions

- **uv 採用**: 高速な依存解決・仮想環境管理
- **Pydantic v2**: ドメインモデルの型安全性確保
- **Protocol ベース DI**: インフラ層の差し替え可能性

---
_Document standards and patterns, not every dependency_
