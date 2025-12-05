"""Lineageエンティティのテスト."""

import pytest

from domain.entities.lineage import LeafTable, LineageNode
from domain.value_objects.table_id import TableId


class TestLineageNode:
    """LineageNodeエンティティのテスト."""

    @pytest.fixture
    def table_id(self) -> TableId:
        """テスト用のTableId."""
        return TableId(project_id="project", dataset_id="dataset", table_id="table")

    @pytest.fixture
    def upstream_table_id(self) -> TableId:
        """上流テーブルのTableId."""
        return TableId(project_id="project", dataset_id="dataset", table_id="upstream")

    @pytest.fixture
    def downstream_table_id(self) -> TableId:
        """下流テーブルのTableId."""
        return TableId(
            project_id="project", dataset_id="dataset", table_id="downstream"
        )

    def test_is_leaf_returns_true_when_no_downstream(self, table_id: TableId) -> None:
        """下流テーブルがない場合にTrueを返す."""
        node = LineageNode(
            table_id=table_id,
            upstream_tables=[],
            downstream_tables=[],
        )
        assert node.is_leaf is True

    def test_is_leaf_returns_false_when_has_downstream(
        self, table_id: TableId, downstream_table_id: TableId
    ) -> None:
        """下流テーブルがある場合にFalseを返す."""
        node = LineageNode(
            table_id=table_id,
            upstream_tables=[],
            downstream_tables=[downstream_table_id],
        )
        assert node.is_leaf is False

    def test_has_upstream_returns_true_when_has_upstream(
        self, table_id: TableId, upstream_table_id: TableId
    ) -> None:
        """上流テーブルがある場合にTrueを返す."""
        node = LineageNode(
            table_id=table_id,
            upstream_tables=[upstream_table_id],
            downstream_tables=[],
        )
        assert node.has_upstream() is True

    def test_has_upstream_returns_false_when_no_upstream(
        self, table_id: TableId
    ) -> None:
        """上流テーブルがない場合にFalseを返す."""
        node = LineageNode(
            table_id=table_id,
            upstream_tables=[],
            downstream_tables=[],
        )
        assert node.has_upstream() is False

    def test_has_downstream_returns_true_when_has_downstream(
        self, table_id: TableId, downstream_table_id: TableId
    ) -> None:
        """下流テーブルがある場合にTrueを返す."""
        node = LineageNode(
            table_id=table_id,
            upstream_tables=[],
            downstream_tables=[downstream_table_id],
        )
        assert node.has_downstream() is True

    def test_has_downstream_returns_false_when_no_downstream(
        self, table_id: TableId
    ) -> None:
        """下流テーブルがない場合にFalseを返す."""
        node = LineageNode(
            table_id=table_id,
            upstream_tables=[],
            downstream_tables=[],
        )
        assert node.has_downstream() is False

    def test_is_leaf_is_computed_field(
        self, table_id: TableId, downstream_table_id: TableId
    ) -> None:
        """is_leafがcomputed_fieldとしてシリアライズされる."""
        node = LineageNode(
            table_id=table_id,
            upstream_tables=[],
            downstream_tables=[downstream_table_id],
        )
        data = node.model_dump()
        assert "is_leaf" in data
        assert data["is_leaf"] is False


class TestLeafTable:
    """LeafTableエンティティのテスト."""

    @pytest.fixture
    def table_id(self) -> TableId:
        """テスト用のTableId."""
        return TableId(project_id="project", dataset_id="dataset", table_id="leaf")

    def test_has_dependencies_returns_true_when_has_upstream(
        self, table_id: TableId
    ) -> None:
        """上流依存がある場合にTrueを返す."""
        leaf = LeafTable(table_id=table_id, upstream_count=3)
        assert leaf.has_dependencies() is True

    def test_has_dependencies_returns_false_when_no_upstream(
        self, table_id: TableId
    ) -> None:
        """上流依存がない場合にFalseを返す."""
        leaf = LeafTable(table_id=table_id, upstream_count=0)
        assert leaf.has_dependencies() is False
