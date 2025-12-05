from pydantic import BaseModel


class UsageInfo(BaseModel, frozen=True):
    """テーブルの利用状況を表す値オブジェクト.

    不変であり、同じ値を持つインスタンスは等価として扱われる。
    """

    job_count: int
    unique_user: int

    def is_unused(self, threshold: int = 0) -> bool:
        """未使用テーブルかどうか."""
        return self.job_count <= threshold
