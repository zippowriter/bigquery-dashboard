"""ドメインモデル定義。

BigQuery のデータセットとテーブルのメタデータを表現する型安全なデータ構造。
"""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field


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


class DataSource(StrEnum):
    """データソース種別を表す列挙型。

    テーブル参照回数を取得するデータソースを識別する。
    """

    INFORMATION_SCHEMA = "information_schema"
    AUDIT_LOG = "audit_log"


class TableAccessCount(BaseModel):
    """テーブル参照回数を表現するイミュータブルなデータ構造。

    Attributes:
        project_id: GCP プロジェクト ID
        dataset_id: BigQuery データセット ID
        table_id: BigQuery テーブル ID
        access_count: 参照回数 (0以上)
        source: データソース種別
    """

    model_config = ConfigDict(frozen=True)

    project_id: str
    dataset_id: str
    table_id: str
    access_count: int = Field(ge=0)
    source: DataSource

    @computed_field  # type: ignore[prop-decorator]
    @property
    def full_path(self) -> str:
        """project.dataset.table 形式のフルパスを返す。"""
        return f"{self.project_id}.{self.dataset_id}.{self.table_id}"


class FilterConfig(BaseModel):
    """フィルタリング条件を表現するイミュータブルなデータ構造。

    Attributes:
        days: 過去N日間を対象とする (デフォルト: 30)
        start_date: 明示的な開始日 (オプション)
        end_date: 明示的な終了日 (オプション)
        dataset_filter: データセット名フィルタ (オプション)
        table_pattern: テーブル名パターン (正規表現、オプション)
        min_access_count: 最小参照回数 (デフォルト: 0)
    """

    model_config = ConfigDict(frozen=True)

    days: int = Field(default=30, ge=1)
    start_date: datetime | None = None
    end_date: datetime | None = None
    dataset_filter: str | None = None
    table_pattern: str | None = None
    min_access_count: int = Field(default=0, ge=0)


def _empty_table_access_list() -> list["TableAccessCount"]:
    """TableAccessCount の空リストを生成するファクトリ関数。"""
    return []


def _empty_string_list() -> list[str]:
    """空の文字列リストを生成するファクトリ関数。"""
    return []


class TableAccessResult(BaseModel):
    """テーブル参照回数集計結果を表現するデータ構造。

    Attributes:
        start_date: 集計開始日時
        end_date: 集計終了日時
        project_id: GCP プロジェクト ID
        info_schema_results: INFORMATION_SCHEMA からの結果
        audit_log_results: Audit Log からの結果
        merged_results: 統合された結果
        warnings: 警告メッセージのリスト
    """

    start_date: datetime
    end_date: datetime
    project_id: str
    info_schema_results: list[TableAccessCount] = Field(
        default_factory=_empty_table_access_list
    )
    audit_log_results: list[TableAccessCount] = Field(
        default_factory=_empty_table_access_list
    )
    merged_results: list[TableAccessCount] = Field(
        default_factory=_empty_table_access_list
    )
    warnings: list[str] = Field(default_factory=_empty_string_list)
