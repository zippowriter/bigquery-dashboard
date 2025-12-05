"""リネージ関連のドメインエンティティ."""

from pydantic import computed_field

from domain.entities.base import Entity
from domain.value_objects.table_id import TableId


class LineageNode(Entity[TableId]):
    """テーブルのリネージ情報を表すエンティティ.

    あるテーブルの上流（参照元）と下流（参照先）の関係を保持する。
    """

    table_id: TableId
    upstream_tables: list[TableId]
    downstream_tables: list[TableId]

    @property
    def id(self) -> TableId:
        """エンティティの識別子を返す."""
        return self.table_id

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


class LeafTable(Entity[TableId]):
    """リーフノードと判定されたテーブル.

    他のテーブルから参照されていない末端テーブルを表す。
    """

    table_id: TableId
    upstream_count: int

    @property
    def id(self) -> TableId:
        """エンティティの識別子を返す."""
        return self.table_id

    def has_dependencies(self) -> bool:
        """上流依存があるか."""
        return self.upstream_count > 0
