# プロジェクト構造

## 構成方針

シンプルなフラット構造からスタート。機能が増加した場合は、責務ごとにモジュール分割を検討する。

## ディレクトリパターン

### ルートディレクトリ
**場所**: `/`
**目的**: プロジェクト設定ファイルとエントリーポイント
**例**: `main.py`, `pyproject.toml`, `README.md`

### テストディレクトリ
**場所**: `/tests/`
**目的**: pytestによるテストコード
**構成**:
- `/tests/unit/` - 単体テスト（モック使用、高速実行）
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
import os
from datetime import datetime

# サードパーティ
from google.cloud import bigquery

# ローカルモジュール
from .query_builder import build_query
```

**原則**:
- 標準ライブラリ → サードパーティ → ローカルの順序
- 相対インポートはパッケージ内部で使用

## コード構成原則

- **単一責任**: 1ファイル = 1つの責務
- **エントリーポイント**: `main.py`がCLIの起点
- **将来の拡張**: 機能増加時は`src/`ディレクトリ導入を検討

---
_パターンを文書化。ファイルツリーではない。パターンに従う新規ファイルは更新不要_
