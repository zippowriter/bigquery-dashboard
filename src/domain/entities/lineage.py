"""リネージ関連のドメインエンティティ."""

from pydantic import BaseModel, computed_field

from domain.value_objects.table_id import TableId


class LineageNode(BaseModel):
    """テーブルのリネージ情報を表すエンティティ.

    あるテーブルの上流（参照元）と下流（参照先）の関係を保持する。
    """

    table_id: TableId
    upstream_tables: list[TableId]
    downstream_tables: list[TableId]

    @computed_field
    @property
    def is_leaf(self) -> bool:
        """下流テーブルがない場合にリーフノードと判定."""
        return len(self.downstream_tables) == 0

    def has_upstream(self) -> bool:
        """上流テーブルが存在するか."""
        return len(self.upstream_tables) > 0

    def has_downstream(self) -> bool:
        """下流テーブルが存在するか."""
        return len(self.downstream_tables) > 0


class LeafTable(BaseModel):
    """リーフノードと判定されたテーブル.

    他のテーブルから参照されていない末端テーブルを表す。
    """

    table_id: TableId
    upstream_count: int

    def has_dependencies(self) -> bool:
        """上流依存があるか."""
        return self.upstream_count > 0
