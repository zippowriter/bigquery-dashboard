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

- `bigquery/`: BigQuery 関連の実装
  - `client.py`: クライアントファクトリ
  - `queries/`: SQL クエリビルダー
  - `*_repository_impl.py`: リポジトリ実装

### SQL Queries (`/sql/`)
**Purpose**: 生 SQL ファイル（複雑なクエリ用）
**Naming**: `{purpose}.sql` (snake_case)

### Data Files (`/source_data/`)
**Purpose**: キャッシュされた CSV データ
**Note**: .gitignore 対象

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
