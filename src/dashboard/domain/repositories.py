"""リポジトリインターフェース定義。

データアクセス層の抽象インターフェースをProtocolで定義する。
"""

from typing import Protocol

from src.dashboard.domain.models import TableInfo, TableUsage


class TableRepository(Protocol):
    """テーブル情報取得のリポジトリインターフェース。

    データソースに依存しない抽象的なインターフェースを定義。
    実装はinfra層で提供される。
    """

    def fetch_tables(self, project_id: str) -> list[TableInfo]:
        """プロジェクト内の全テーブル一覧を取得する。

        Args:
            project_id: GCPプロジェクトID

        Returns:
            テーブル情報のリスト
        """
        ...

    def fetch_usage_stats(self, project_id: str, region: str) -> list[TableUsage]:
        """テーブル利用統計を取得する。

        Args:
            project_id: GCPプロジェクトID
            region: BigQueryリージョン

        Returns:
            テーブル利用統計のリスト
        """
        ...
