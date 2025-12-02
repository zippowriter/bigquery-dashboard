"""ドメインモデル定義。

テーブル情報と利用統計のドメインモデルを提供する。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TableInfo:
    """テーブル情報のドメインモデル。

    Attributes:
        dataset_id: データセットID
        table_id: テーブルID
    """

    dataset_id: str
    table_id: str


@dataclass(frozen=True)
class TableUsage:
    """テーブル利用統計のドメインモデル。

    Attributes:
        dataset_id: データセットID
        table_id: テーブルID
        reference_count: 参照回数
        unique_users: ユニーク参照ユーザー数
    """

    dataset_id: str
    table_id: str
    reference_count: int
    unique_users: int

    @property
    def is_unused(self) -> bool:
        """未使用テーブルかどうかを判定する。

        Returns:
            参照回数が0の場合True
        """
        return self.reference_count == 0
