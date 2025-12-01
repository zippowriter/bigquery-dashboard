# プロジェクト構造

## 構成方針

レイヤードアーキテクチャを採用。責務ごとにモジュールを分割し、依存関係の方向を制御する。

## ディレクトリパターン

### ルートディレクトリ
**場所**: `/`
**目的**: プロジェクト設定ファイル
**例**: `pyproject.toml`, `README.md`, `pyrightconfig.json`

### ソースディレクトリ
**場所**: `/src/bq_table_reference/`
**目的**: メインパッケージ。レイヤードアーキテクチャで構成

**レイヤー構成**:
- `/domain/` - ドメインモデルと例外定義（ビジネスロジックの中核）
- `/application/` - アプリケーションサービス（ユースケースの実装）
- `/infrastructure/` - 外部システムとの連携（BigQuery APIアダプター）

**依存関係の方向**:
```
infrastructure → application → domain
        ↓            ↓
      domain       domain
```

### テストディレクトリ
**場所**: `/tests/`
**目的**: pytestによるテストコード
**構成**:
- `/tests/unit/` - 単体テスト（モック使用、高速実行）
  - ソース構造をミラー: `unit/domain/`, `unit/application/`, `unit/infrastructure/`
- `/tests/integration/` - 統合テスト（実環境API使用）
**例**: `test_*.py` 形式のファイル

### 仮想環境
**場所**: `/.venv/`
**目的**: uv管理のPython仮想環境 (git管理外)

## 命名規約

- **ファイル**: snake_case (`bq_client.py`, `query_builder.py`)
- **クラス**: PascalCase (`BigQueryClient`, `TableReference`)
- **関数/変数**: snake_case (`get_table_references`, `project_id`)
- **定数**: UPPER_SNAKE_CASE (`DEFAULT_TIMEOUT`, `MAX_RESULTS`)

## インポート構成

```python
# 標準ライブラリ
import logging
from datetime import datetime
from typing import Protocol

# サードパーティ
from google.cloud import bigquery
from pydantic import BaseModel

# ローカルモジュール（絶対インポート）
from bq_table_reference.domain.models import DatasetInfo
from bq_table_reference.domain.exceptions import DatasetLoaderError
```

**原則**:
- 標準ライブラリ → サードパーティ → ローカルの順序
- パッケージ内は絶対インポートを使用（`bq_table_reference.` prefix）
- レイヤー間の依存方向を遵守（infrastructure → application → domain）

## コード構成原則

- **単一責任**: 1ファイル = 1つの責務
- **エントリーポイント**: `/src/main.py`がCLIの起点
- **レイヤー分離**: domain は他レイヤーに依存しない
- **アダプターパターン**: 外部APIはinfrastructure層でラップ

---
_パターンを文書化。ファイルツリーではない。パターンに従う新規ファイルは更新不要_
