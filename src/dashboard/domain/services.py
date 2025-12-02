"""ビジネスロジックサービス。

テーブル利用統計に関するビジネスロジックを提供する。
"""

from src.dashboard.domain.models import TableInfo, TableUsage


class TableUsageService:
    """テーブル利用統計のビジネスロジック。

    テーブル一覧と利用統計の結合処理を提供する。
    """

    @staticmethod
    def merge_usage_data(
        tables: list[TableInfo],
        usage_stats: list[TableUsage],
    ) -> list[TableUsage]:
        """テーブル一覧と利用統計を結合する。

        テーブル一覧を基準としてLEFT JOIN相当の結合を行い、
        利用実績がないテーブルはreference_count=0、unique_users=0で補完する。

        Args:
            tables: テーブル情報のリスト
            usage_stats: 利用統計のリスト

        Returns:
            結合済みのテーブル利用統計リスト。
            利用実績がないテーブルはreference_count=0、unique_users=0
        """
        # 利用統計をキー（dataset_id, table_id）でマップ化
        usage_map: dict[tuple[str, str], TableUsage] = {
            (u.dataset_id, u.table_id): u for u in usage_stats
        }

        result: list[TableUsage] = []
        for table in tables:
            key = (table.dataset_id, table.table_id)
            if key in usage_map:
                result.append(usage_map[key])
            else:
                # 利用実績なしの場合は0で補完
                result.append(
                    TableUsage(
                        dataset_id=table.dataset_id,
                        table_id=table.table_id,
                        reference_count=0,
                        unique_users=0,
                    )
                )
        return result
