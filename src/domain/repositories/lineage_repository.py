"""リネージリポジトリのインターフェース定義."""

from collections.abc import Sequence
from typing import Protocol

from domain.entities.lineage import LeafTable, TableLineageInfo
from domain.value_objects.table_id import TableId


class LineageRepository(Protocol):
    """リネージ情報を取得するリポジトリのインターフェース."""

    def get_table_lineage(self, table_id: TableId) -> TableLineageInfo:
        """指定されたテーブルのリネージ情報を取得する.

        Args:
            table_id: 対象テーブルのID

        Returns:
            TableLineageInfo エンティティ

        Raises:
            LineageRepositoryError: リネージ情報取得に失敗した場合
        """
        ...

    def get_leaf_tables(
        self,
        table_ids: Sequence[TableId],
    ) -> list[LeafTable]:
        """指定されたテーブルの中からリーフノードを特定する.

        リーフノード = 下流に他のテーブルを持たないテーブル（最終的なアウトプット）

        Args:
            table_ids: 対象テーブルIDのリスト

        Returns:
            LeafTable エンティティのリスト

        Raises:
            LineageRepositoryError: リーフノード判定に失敗した場合
        """
        ...

    def find_leaf_tables_from_roots(
        self,
        root_tables: Sequence[TableId],
    ) -> list[LeafTable]:
        """指定されたルートテーブルから下流を辿り、リーフノードを取得する.

        BFS（幅優先探索）でルートテーブルから下流を辿り、
        下流を持たないテーブル（リーフノード）を収集する。
        訪問済みテーブルをスキップすることで循環参照に対応する。

        Args:
            root_tables: 探索の起点となるテーブルIDのリスト

        Returns:
            LeafTable エンティティのリスト

        Raises:
            LineageRepositoryError: リーフノード探索に失敗した場合
        """
        ...
