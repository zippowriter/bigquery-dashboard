# Project Structure

## Organization Philosophy

Clean Architecture / DDDスタイルのレイヤードアーキテクチャ。`src/` 配下にドメイン別パッケージを配置し、
各パッケージ内で `domain/`, `infra/`, `presentation/` のレイヤーに分離する。

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
- **Root modules**:
  - `config.py`: Pydanticモデルによるアプリ設定
  - `app.py`: Dashインスタンス生成
  - `server.py`: サーバー起動ロジック

### Domain Layer (`/src/dashboard/domain/`)
- **Location**: `/src/dashboard/domain/`
- **Purpose**: ビジネスロジックとドメインモデル（外部依存なし）
- **Structure**:
  - `models.py`: ドメインモデル（dataclass, frozen=True）
  - `repositories.py`: リポジトリインターフェース（Protocol）
  - `services.py`: ビジネスロジックサービス

### Infrastructure Layer (`/src/dashboard/infra/`)
- **Location**: `/src/dashboard/infra/`
- **Purpose**: 外部システムとの連携（リポジトリ実装）
- **Structure**:
  - `bigquery.py`: BigQuery APIクライアント実装

### Presentation Layer (`/src/dashboard/presentation/`)
- **Location**: `/src/dashboard/presentation/`
- **Purpose**: UI表示・レイアウト構築
- **Structure**:
  - `layout.py`: レイアウトオーケストレーション
  - `components.py`: 再利用可能なUIコンポーネント

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
- **依存関係の方向**: presentation -> domain <- infra（依存性逆転）
- **レイヤー間境界**: domainは外部依存なし、infraがdomainのProtocolを実装
- **テスト対応**: 各モジュールに対応するテストファイル（レイヤー構造をミラー）
- **docstring**: 全モジュール・関数にdocstring必須

---
_Document patterns, not file trees. New files following patterns should not require updates_

<!-- updated_at: 2025-12-02 -->
<!-- sync: Clean Architecture / DDD layered structure adopted (domain/infra/presentation) -->
