from typing import Literal

from domain.entities.base import Entity
from domain.value_objects.table_id import TableId


TableType = Literal[
    "BASE TABLE",
    "VIEW",
    "EXTERNAL",
    "CLONE",
    "SNAPSHOT",
    "MATERIALIZED VIEW",
]


class Table(Entity[TableId]):
    """BigQueryのテーブルのモデル"""

    table_id: TableId
    table_type: TableType

    @property
    def id(self) -> TableId:
        """エンティティの識別子を返す."""
        return self.table_id

    def __hash__(self) -> int:
        """識別子に基づいてハッシュ値を計算する."""
        return hash(self.id)

    def is_base_table(self) -> bool:
        """ベーステーブルかどうか."""
        return self.table_type == "BASE TABLE"

    def is_view(self) -> bool:
        """ビューかどうか."""
        return self.table_type == "VIEW"

    def is_external(self) -> bool:
        """外部テーブルかどうか."""
        return self.table_type == "EXTERNAL"

    def is_clone(self) -> bool:
        """クローンテーブルかどうか."""
        return self.table_type == "CLONE"

    def is_snapshot(self) -> bool:
        """スナップショットテーブルかどうか."""
        return self.table_type == "SNAPSHOT"

    def is_materialized_view(self) -> bool:
        """マテリアライズドビューかどうか."""
        return self.table_type == "MATERIALIZED VIEW"


class CheckedTable(Table):
    """参照回数が調べられたテーブルのモデル"""

    job_count: int
    unique_user: int

    def is_unused(self, threshold: int = 0) -> bool:
        """未使用テーブルかどうか."""
        return self.job_count <= threshold

    def usage_summary(self) -> str:
        """利用状況のサマリー."""
        return f"{self.job_count} jobs, {self.unique_user} users"


class CandidateTable(Table):
    """削除候補となるテーブルのモデル"""

    data_owner: str
