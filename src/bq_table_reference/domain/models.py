"""ドメインモデル定義。

BigQuery のデータセットとテーブルのメタデータを表現する型安全なデータ構造。
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

# テーブル種別の型定義
TableType = Literal["TABLE", "VIEW", "MATERIALIZED_VIEW", "EXTERNAL"]


class DatasetInfo(BaseModel):
    """BigQuery データセットのメタデータを表現するイミュータブルなデータ構造。

    Attributes:
        dataset_id: BigQuery データセット ID
        project: GCP プロジェクト ID
        full_path: "project.dataset" 形式のフルパス
        created: データセット作成日時（オプショナル）
        modified: データセット最終更新日時（オプショナル）
        location: データセットのロケーション（オプショナル）
    """

    model_config = ConfigDict(frozen=True)

    dataset_id: str
    project: str
    full_path: str
    created: datetime | None
    modified: datetime | None
    location: str | None


class TableInfo(BaseModel):
    """BigQuery テーブルのメタデータを表現するイミュータブルなデータ構造。

    Attributes:
        table_id: BigQuery テーブル ID
        dataset_id: 親データセットの ID
        project: GCP プロジェクト ID
        full_path: "project.dataset.table" 形式のフルパス
        table_type: テーブル種別（TABLE/VIEW/MATERIALIZED_VIEW/EXTERNAL）
    """

    model_config = ConfigDict(frozen=True)

    table_id: str
    dataset_id: str
    project: str
    full_path: str
    table_type: TableType


class LoadResult(BaseModel):
    """一括ロード処理の結果サマリーを表現するデータ構造。

    Attributes:
        datasets_success: ロード成功したデータセット数
        datasets_failed: ロード失敗したデータセット数
        tables_total: ロードしたテーブル総数
        errors: 失敗したデータセットのエラー詳細（dataset_id -> エラーメッセージ）
    """

    datasets_success: int
    datasets_failed: int
    tables_total: int
    errors: dict[str, str] = {}
