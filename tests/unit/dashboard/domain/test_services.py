"""TableUsageServiceのテスト。"""

from src.shared.domain.models import TableInfo, TableUsage
from src.shared.domain.services import TableUsageService


class TestMergeUsageData:
    """merge_usage_dataメソッドのテスト。"""

    def test_left_join_preserves_all_tables(self) -> None:
        """テーブル一覧の全行がLEFT JOIN相当で保持されることを検証する。"""
        # 3つのテーブルが存在
        tables = [
            TableInfo(dataset_id="ds1", table_id="t1"),
            TableInfo(dataset_id="ds1", table_id="t2"),
            TableInfo(dataset_id="ds2", table_id="t3"),
        ]

        # 1つのテーブルにのみ利用実績あり
        usage_stats = [
            TableUsage(dataset_id="ds1", table_id="t1", reference_count=10, unique_users=3),
        ]

        result = TableUsageService.merge_usage_data(tables, usage_stats)

        # 全3行が保持される
        assert len(result) == 3

    def test_zero_fill_for_missing_usage(self) -> None:
        """利用実績がないテーブルはreference_count=0、unique_users=0で補完されることを検証する。"""
        tables = [
            TableInfo(dataset_id="ds1", table_id="t1"),
            TableInfo(dataset_id="ds2", table_id="t2"),
        ]

        # ds1.t1のみ利用実績あり
        usage_stats = [
            TableUsage(dataset_id="ds1", table_id="t1", reference_count=5, unique_users=2),
        ]

        result = TableUsageService.merge_usage_data(tables, usage_stats)

        # ds2.t2の行を確認
        ds2_t2 = [u for u in result if u.dataset_id == "ds2" and u.table_id == "t2"][0]
        assert ds2_t2.reference_count == 0
        assert ds2_t2.unique_users == 0

    def test_merge_with_empty_usage(self) -> None:
        """利用統計が空の場合、全テーブルが参照回数0で保持されることを検証する。"""
        tables = [
            TableInfo(dataset_id="ds1", table_id="t1"),
            TableInfo(dataset_id="ds2", table_id="t2"),
        ]

        # 利用統計なし
        usage_stats: list[TableUsage] = []

        result = TableUsageService.merge_usage_data(tables, usage_stats)

        assert len(result) == 2
        assert all(u.reference_count == 0 for u in result)
        assert all(u.unique_users == 0 for u in result)

    def test_preserves_usage_stats_values(self) -> None:
        """利用実績があるテーブルの値が正しく保持されることを検証する。"""
        tables = [
            TableInfo(dataset_id="ds1", table_id="t1"),
        ]

        usage_stats = [
            TableUsage(dataset_id="ds1", table_id="t1", reference_count=100, unique_users=25),
        ]

        result = TableUsageService.merge_usage_data(tables, usage_stats)

        assert len(result) == 1
        assert result[0].reference_count == 100
        assert result[0].unique_users == 25


class TestMergeWithLeafInfo:
    """merge_with_leaf_infoメソッドのテスト。"""

    def test_sets_is_leaf_true_for_leaf_tables(self) -> None:
        """リーフテーブルにis_leaf=Trueが設定されることを検証する。"""
        usages = [
            TableUsage(dataset_id="ds1", table_id="t1", reference_count=10, unique_users=3),
            TableUsage(dataset_id="ds1", table_id="t2", reference_count=5, unique_users=2),
        ]
        leaf_fqns = {"bigquery:proj.ds1.t1"}

        result = TableUsageService.merge_with_leaf_info(usages, leaf_fqns, "proj")

        t1 = [u for u in result if u.table_id == "t1"][0]
        t2 = [u for u in result if u.table_id == "t2"][0]
        assert t1.is_leaf is True
        assert t2.is_leaf is False

    def test_preserves_all_other_fields(self) -> None:
        """他のフィールドが正しく保持されることを検証する。"""
        usages = [
            TableUsage(dataset_id="ds1", table_id="t1", reference_count=10, unique_users=3),
        ]
        leaf_fqns = {"bigquery:proj.ds1.t1"}

        result = TableUsageService.merge_with_leaf_info(usages, leaf_fqns, "proj")

        assert result[0].dataset_id == "ds1"
        assert result[0].table_id == "t1"
        assert result[0].reference_count == 10
        assert result[0].unique_users == 3

    def test_handles_empty_leaf_set(self) -> None:
        """リーフセットが空の場合、全テーブルがis_leaf=Falseになることを検証する。"""
        usages = [
            TableUsage(dataset_id="ds1", table_id="t1", reference_count=10, unique_users=3),
        ]
        leaf_fqns: set[str] = set()

        result = TableUsageService.merge_with_leaf_info(usages, leaf_fqns, "proj")

        assert all(u.is_leaf is False for u in result)
