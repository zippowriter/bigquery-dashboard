# Project Structure

## Organization Philosophy

機能別レイヤードアーキテクチャ。`src/` 配下にドメイン別パッケージを配置し、
各パッケージ内で責務ごとにモジュールを分割する。

## Directory Patterns

### Application Entry (`/`)
- **Location**: `/app.py`
- **Purpose**: アプリケーションのエントリーポイント
- **Example**: `main()` 関数でDashアプリを初期化・起動

### Source Packages (`/src/`)
- **Location**: `/src/{package}/`
- **Purpose**: ドメイン別パッケージ
- **Example**: `src/dashboard/` - ダッシュボード関連機能

### Dashboard Package (`/src/dashboard/`)
- **Location**: `/src/dashboard/`
- **Purpose**: Dashアプリケーション構成要素
- **Structure**:
  - `config.py`: Pydanticモデルによるアプリ設定
  - `layout.py`: UIコンポーネント・レイアウト構築
  - `app.py`: Dashインスタンス生成
  - `server.py`: サーバー起動ロジック
  - `bigquery_client.py`: BigQuery APIクライアント・データ取得

### Tests (`/tests/`)
- **Location**: `/tests/unit/{package}/` - 単体テスト、`/tests/integration/` - 統合テスト
- **Purpose**: テストコード配置
- **Naming**: `test_{module}.py` パターン
- **Structure**: ソースパッケージ構造をミラー（例: `src/dashboard/` -> `tests/unit/dashboard/`）

## Naming Conventions

- **Files**: snake_case (例: `test_config.py`, `layout.py`)
- **Classes**: PascalCase (例: `AppConfig`, `TestCreateApp`)
- **Functions**: snake_case (例: `create_app`, `build_layout`)
- **Constants**: UPPER_SNAKE_CASE (例: `TITLE`)

## Import Organization

```python
# 標準ライブラリ
from typing import Optional

# サードパーティ
from dash import Dash, html
from pydantic import BaseModel

# ローカル (絶対インポート)
from src.dashboard.config import AppConfig
from src.dashboard.layout import build_layout
```

**Import Rules**:
- 絶対インポート優先 (`from src.dashboard.config import ...`)
- 同一パッケージ内は相対インポート可
- `combine-as-imports` でインポート統合

## Code Organization Principles

- **単一責任**: 1モジュール = 1責務
- **依存関係**: `app.py` -> `config.py`, `layout.py` -> `bigquery_client.py`
- **テスト対応**: 各モジュールに対応するテストファイル
- **docstring**: 全モジュール・関数にdocstring必須

---
_Document patterns, not file trees. New files following patterns should not require updates_

<!-- updated_at: 2025-12-02 -->
