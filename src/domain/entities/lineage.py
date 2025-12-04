"""リネージ関連のドメインエンティティ."""

from pydantic import BaseModel

from domain.value_objects.table_id import TableId


class TableLineageInfo(BaseModel):
    """テーブルのリネージ情報を表すエンティティ.

    あるテーブルの上流（参照元）と下流（参照先）の関係を保持する。
    """

    table_id: TableId
    upstream_tables: list[TableId]
    downstream_tables: list[TableId]
    is_leaf: bool


class LeafTable(BaseModel):
    """リーフノードと判定されたテーブル.

    他のテーブルから参照されていない末端テーブルを表す。
    """

    table_id: TableId
    upstream_count: int
