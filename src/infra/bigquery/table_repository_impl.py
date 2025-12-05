"""BigQueryを使用したTableRepositoryの実装."""

from collections.abc import Sequence
from typing import Any

from google.api_core.exceptions import GoogleAPIError
from google.cloud.bigquery import Client

from domain.entities.analyzed_table import AnalyzedTable
from domain.entities.table import Table
from domain.value_objects.table_id import TableId
from domain.value_objects.usage_info import UsageInfo
from infra.bigquery.client import BigQueryClientFactory
from infra.bigquery.exceptions import BigQueryQueryError, TableRepositoryError
from infra.bigquery.queries.table_queries import (
    build_list_tables_query,
    build_reference_count_query,
)


class BigQueryTableRepository:
    """BigQueryを使用したTableRepositoryの実装."""

    def __init__(self, client_factory: BigQueryClientFactory) -> None:
        """初期化.

        Args:
            client_factory: BigQueryクライアントファクトリ
        """
        self._client_factory = client_factory

    def list_tables(self, project_ids: Sequence[str]) -> list[Table]:
        """指定されたプロジェクトからテーブル一覧を取得する.

        Args:
            project_ids: 対象プロジェクトIDのリスト

        Returns:
            Table エンティティのリスト

        Raises:
            TableRepositoryError: テーブル取得に失敗した場合
        """
        if not project_ids:
            return []

        query = build_list_tables_query(project_ids)

        try:
            with self._client_factory.get_client() as client:
                results = self._execute_query(client, query)

                tables: list[Table] = []
                for row in results:
                    table = Table(
                        table_id=TableId(
                            project_id=row["project_id"],
                            dataset_id=row["dataset_id"],
                            table_id=row["table_id"],
                        ),
                        table_type=row["table_type"],
                    )
                    tables.append(table)

                return tables

        except BigQueryQueryError as e:
            raise TableRepositoryError(
                f"Failed to list tables: {e}",
                cause=e,
            ) from e

    def get_table_reference_counts(
        self,
        tables: Sequence[Table],
        days_back: int = 90,
    ) -> list[AnalyzedTable]:
        """テーブルの参照回数とユニークユーザー数を取得する.

        Args:
            tables: 対象テーブルのリスト
            days_back: 過去何日分のジョブを調査するか

        Returns:
            AnalyzedTable エンティティのリスト（usage_info設定済み）

        Raises:
            TableRepositoryError: 参照回数取得に失敗した場合
        """
        if not tables:
            return []

        query = build_reference_count_query(days_back)

        try:
            with self._client_factory.get_client() as client:
                results = self._execute_query(client, query)

                reference_map: dict[tuple[str, str, str], tuple[int, int]] = {}
                for row in results:
                    key = (
                        row["project_id"],
                        row["dataset_id"],
                        row["table_id"],
                    )
                    reference_map[key] = (row["job_count"], row["unique_user"])

                analyzed_tables: list[AnalyzedTable] = []
                for table in tables:
                    key = (
                        table.table_id.project_id,
                        table.table_id.dataset_id,
                        table.table_id.table_id,
                    )
                    job_count, unique_user = reference_map.get(key, (0, 0))

                    analyzed_table = AnalyzedTable(
                        table=table,
                        usage_info=UsageInfo(
                            job_count=job_count,
                            unique_user=unique_user,
                        ),
                    )
                    analyzed_tables.append(analyzed_table)

                return analyzed_tables

        except BigQueryQueryError as e:
            raise TableRepositoryError(
                f"Failed to get table reference counts: {e}",
                cause=e,
            ) from e

    def _execute_query(self, client: Client, query: str) -> list[dict[str, Any]]:
        """クエリを実行し結果を辞書のリストとして返す.

        Args:
            client: BigQueryクライアント
            query: 実行するSQLクエリ

        Returns:
            結果の辞書リスト

        Raises:
            BigQueryQueryError: クエリ実行に失敗した場合
        """
        try:
            query_job = client.query(query)
            results = query_job.result()
            return [dict(row.items()) for row in results]  # pyright: ignore[reportUnknownVariableType]
        except GoogleAPIError as e:
            raise BigQueryQueryError(
                f"Query execution failed: {e}",
                query=query,
                cause=e,
            ) from e
