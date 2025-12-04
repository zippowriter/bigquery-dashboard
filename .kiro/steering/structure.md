# Project Structure

## Organization Philosophy

クリーンアーキテクチャ（レイヤードアーキテクチャ）を採用。ドメイン層を中心に、外側のレイヤーから内側への依存のみ許可。

## Directory Patterns

### Domain Layer (`/src/domain/`)
**Purpose**: ビジネスロジックとルールの定義
**依存**: 外部依存なし（Pure Python + Pydantic のみ）

- `entities/`: ドメインエンティティ（Table, CheckedTable など）
- `value_objects/`: 値オブジェクト（TableId など）
- `repositories/`: リポジトリインターフェース（Protocol）
- `services/`: ドメインサービス

### Application Layer (`/src/application/`)
**Purpose**: ユースケースの実装
**依存**: domain のみ

- `usecases/`: アプリケーションユースケース

### Infrastructure Layer (`/src/infra/`)
**Purpose**: 外部サービスとの接続実装
**依存**: domain, 外部ライブラリ

サブディレクトリは外部サービス単位で分割:
- `bigquery/`: BigQuery API 関連
- `lineage/`: Data Catalog Lineage API 関連
- `file/`: ファイル I/O 関連

**共通パターン**:
- `client.py`: クライアントファクトリ
- `*_repository_impl.py`: domain の Protocol 実装
- `exceptions.py`: インフラ層固有の例外
- `queries/`: SQL クエリビルダー（BigQuery のみ）

### Output Files (`/output/`)
**Purpose**: 実行結果の出力ファイル（CSV, JSON など）
**Note**: .gitignore 対象推奨

## Naming Conventions

- **Files**: snake_case (`table_repository.py`)
- **Classes**: PascalCase (`BigQueryTableRepository`)
- **Functions/Methods**: snake_case (`list_tables`)
- **Constants**: UPPER_SNAKE_CASE (`DATA_SOURCE_PATH`)

## Import Organization

```python
# 1. 標準ライブラリ
from collections.abc import Sequence
from typing import Protocol

# 2. サードパーティ
from pydantic import BaseModel
from google.cloud import bigquery

# 3. ローカル（相対インポート不使用）
from domain.entities.table import Table
from infra.bigquery.client import BigQueryClientFactory
```

**Path Aliases**: なし（src ディレクトリからの絶対インポート）

## Code Organization Principles

- **依存方向**: infra → application → domain
- **Protocol パターン**: リポジトリは domain で Protocol 定義、infra で実装
- **Pydantic モデル**: すべてのエンティティ・値オブジェクトは BaseModel 継承

---
_Document patterns, not file trees. New files following patterns shouldn't require updates_
