"""Tableエンティティのテスト."""

import pytest

from domain.entities.analyzed_table import AnalyzedTable
from domain.entities.table import Table
from domain.value_objects.table_id import TableId
from domain.value_objects.usage_info import UsageInfo


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


class TestUsageInfo:
    """UsageInfo値オブジェクトのテスト."""

    def test_is_unused_returns_true_when_job_count_is_zero(self) -> None:
        """job_countが0の場合にTrueを返す."""
        usage_info = UsageInfo(job_count=0, unique_user=0)
        assert usage_info.is_unused() is True

    def test_is_unused_with_threshold(self) -> None:
        """閾値を指定した場合のテスト."""
        usage_info = UsageInfo(job_count=3, unique_user=1)
        assert usage_info.is_unused(threshold=5) is True
        assert usage_info.is_unused(threshold=2) is False


class TestAnalyzedTable:
    """AnalyzedTableエンティティのテスト."""

    @pytest.fixture
    def table_id(self) -> TableId:
        """テスト用のTableId."""
        return TableId(project_id="project", dataset_id="dataset", table_id="table")

    @pytest.fixture
    def table(self, table_id: TableId) -> Table:
        """テスト用のTable."""
        return Table(table_id=table_id, table_type="BASE TABLE")

    def test_id_returns_table_id(self, table: Table, table_id: TableId) -> None:
        """idプロパティがtable_idを返す."""
        analyzed = AnalyzedTable(table=table)
        assert analyzed.id == table_id

    def test_is_checked_returns_false_when_no_usage_info(self, table: Table) -> None:
        """usage_infoがない場合はFalseを返す."""
        analyzed = AnalyzedTable(table=table)
        assert analyzed.is_checked is False

    def test_is_checked_returns_true_when_usage_info_set(self, table: Table) -> None:
        """usage_infoが設定されている場合はTrueを返す."""
        analyzed = AnalyzedTable(
            table=table,
            usage_info=UsageInfo(job_count=10, unique_user=3),
        )
        assert analyzed.is_checked is True

    def test_with_usage_info_returns_new_instance(self, table: Table) -> None:
        """with_usage_infoは新しいインスタンスを返す."""
        analyzed = AnalyzedTable(table=table)
        usage_info = UsageInfo(job_count=5, unique_user=2)
        new_analyzed = analyzed.with_usage_info(usage_info)

        assert new_analyzed is not analyzed
        assert new_analyzed.usage_info == usage_info
        assert analyzed.usage_info is None

    def test_is_unused_raises_when_no_usage_info(self, table: Table) -> None:
        """usage_infoがない場合はValueErrorを発生させる."""
        analyzed = AnalyzedTable(table=table)
        with pytest.raises(ValueError, match="Usage info is not set"):
            analyzed.is_unused()

    def test_is_unused_delegates_to_usage_info(self, table: Table) -> None:
        """is_unusedはusage_infoに委譲する."""
        analyzed = AnalyzedTable(
            table=table,
            usage_info=UsageInfo(job_count=0, unique_user=0),
        )
        assert analyzed.is_unused() is True
