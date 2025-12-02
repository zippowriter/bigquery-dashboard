"""ドメインモデルのテスト。"""

from src.dashboard.domain.models import TableUsage


class TestTableUsage:
    """TableUsageモデルのテスト。"""

    def test_is_unused_returns_true_when_reference_count_is_zero(self) -> None:
        """参照回数が0の場合、is_unusedがTrueを返却することを検証する。"""
        usage = TableUsage(
            dataset_id="ds1",
            table_id="t1",
            reference_count=0,
            unique_users=0,
        )

        assert usage.is_unused is True

    def test_is_unused_returns_false_when_reference_count_is_positive(self) -> None:
        """参照回数が正の場合、is_unusedがFalseを返却することを検証する。"""
        usage = TableUsage(
            dataset_id="ds1",
            table_id="t1",
            reference_count=10,
            unique_users=3,
        )

        assert usage.is_unused is False
