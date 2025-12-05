"""Tableエンティティのテスト."""

import pytest

from domain.entities.table import CheckedTable, Table
from domain.value_objects.table_id import TableId


class TestTable:
    """Tableエンティティのテスト."""

    @pytest.fixture
    def table_id(self) -> TableId:
        """テスト用のTableId."""
        return TableId(project_id="project", dataset_id="dataset", table_id="table")

    def test_is_base_table_returns_true_for_base_table(self, table_id: TableId) -> None:
        """BASE TABLEの場合にTrueを返す."""
        table = Table(table_id=table_id, table_type="BASE TABLE")
        assert table.is_base_table() is True

    def test_is_base_table_returns_false_for_view(self, table_id: TableId) -> None:
        """VIEWの場合にFalseを返す."""
        table = Table(table_id=table_id, table_type="VIEW")
        assert table.is_base_table() is False

    def test_equality_based_on_table_id(self, table_id: TableId) -> None:
        """同じtable_idを持つTableは等価とみなされる."""
        table1 = Table(table_id=table_id, table_type="BASE TABLE")
        table2 = Table(table_id=table_id, table_type="VIEW")
        assert table1 == table2

    def test_inequality_with_different_table_id(self) -> None:
        """異なるtable_idを持つTableは等価ではない."""
        table1 = Table(
            table_id=TableId(project_id="p1", dataset_id="d1", table_id="t1"),
            table_type="BASE TABLE",
        )
        table2 = Table(
            table_id=TableId(project_id="p2", dataset_id="d2", table_id="t2"),
            table_type="BASE TABLE",
        )
        assert table1 != table2

    def test_hash_based_on_table_id(self, table_id: TableId) -> None:
        """同じtable_idを持つTableは同じハッシュ値を持つ."""
        table1 = Table(table_id=table_id, table_type="BASE TABLE")
        table2 = Table(table_id=table_id, table_type="VIEW")
        assert hash(table1) == hash(table2)

    def test_can_be_used_in_set(self, table_id: TableId) -> None:
        """Tableをsetで使用できる."""
        table1 = Table(table_id=table_id, table_type="BASE TABLE")
        table2 = Table(table_id=table_id, table_type="VIEW")
        table_set = {table1, table2}
        assert len(table_set) == 1

    def test_id_property_returns_table_id(self, table_id: TableId) -> None:
        """idプロパティがtable_idを返す."""
        table = Table(table_id=table_id, table_type="BASE TABLE")
        assert table.id == table_id


class TestCheckedTable:
    """CheckedTableエンティティのテスト."""

    @pytest.fixture
    def table_id(self) -> TableId:
        """テスト用のTableId."""
        return TableId(project_id="project", dataset_id="dataset", table_id="table")

    def test_is_unused_returns_true_when_job_count_is_zero(
        self, table_id: TableId
    ) -> None:
        """job_countが0の場合にTrueを返す."""
        table = CheckedTable(
            table_id=table_id,
            table_type="BASE TABLE",
            job_count=0,
            unique_user=0,
        )
        assert table.is_unused() is True

    def test_is_unused_with_threshold(self, table_id: TableId) -> None:
        """閾値を指定した場合のテスト."""
        table = CheckedTable(
            table_id=table_id,
            table_type="BASE TABLE",
            job_count=3,
            unique_user=1,
        )
        assert table.is_unused(threshold=5) is True
        assert table.is_unused(threshold=2) is False

    def test_usage_summary_returns_formatted_string(self, table_id: TableId) -> None:
        """フォーマットされた文字列を返す."""
        table = CheckedTable(
            table_id=table_id,
            table_type="BASE TABLE",
            job_count=10,
            unique_user=3,
        )
        assert table.usage_summary() == "10 jobs, 3 users"
