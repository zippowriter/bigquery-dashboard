"""テーブルリポジトリのインターフェース定義."""

from collections.abc import Sequence
from typing import Protocol

from domain.entities.table import CheckedTable, Table


class TableRepository(Protocol):
    """テーブル情報を取得するリポジトリのインターフェース."""

    def list_tables(self, project_ids: Sequence[str]) -> list[Table]:
        """指定されたプロジェクトからテーブル一覧を取得する.

        Args:
            project_ids: 対象プロジェクトIDのリスト

        Returns:
            Table エンティティのリスト

        Raises:
            TableRepositoryError: テーブル取得に失敗した場合
        """
        ...

    def get_table_reference_counts(
        self,
        tables: Sequence[Table],
        days_back: int = 90,
    ) -> list[CheckedTable]:
        """テーブルの参照回数とユニークユーザー数を取得する.

        Args:
            tables: 対象テーブルのリスト
            days_back: 過去何日分のジョブを調査するか（デフォルト: 90日）

        Returns:
            CheckedTable エンティティのリスト

        Raises:
            TableRepositoryError: 参照回数取得に失敗した場合
        """
        ...
