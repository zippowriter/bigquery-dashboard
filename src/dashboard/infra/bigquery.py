"""BigQueryリポジトリ実装。

BigQuery APIを使用してテーブル情報と利用統計を取得する。
"""

from typing import Any

from google.cloud import bigquery

from src.dashboard.domain.models import TableInfo, TableUsage


class BigQueryTableRepository:
    """BigQuery実装のテーブルリポジトリ。

    BigQuery APIを使用してテーブル情報と利用統計を取得する。
    """

    def fetch_tables(self, project_id: str) -> list[TableInfo]:
        """プロジェクト内の全テーブル一覧を取得する。

        Args:
            project_id: GCPプロジェクトID

        Returns:
            テーブル情報のリスト

        Raises:
            ValueError: project_idが空文字の場合
            google.api_core.exceptions.GoogleAPIError: BigQuery API呼び出しに失敗した場合
        """
        if not project_id:
            raise ValueError("project_idは空文字にできません")

        client = bigquery.Client(project=project_id)

        tables: list[TableInfo] = []

        # 全データセットを取得し、各データセット内のテーブルを収集
        # google-cloud-bigqueryライブラリの型定義が不完全なためpyright ignoreを使用
        for dataset in client.list_datasets():  # pyright: ignore[reportUnknownVariableType]
            for table in client.list_tables(dataset.dataset_id):  # pyright: ignore[reportUnknownVariableType]
                tables.append(
                    TableInfo(
                        dataset_id=str(table.dataset_id),
                        table_id=str(table.table_id),
                    )
                )

        return tables

    def fetch_usage_stats(self, project_id: str, region: str) -> list[TableUsage]:
        """テーブル利用統計を取得する。

        INFORMATION_SCHEMA.JOBS_BY_PROJECTからreferenced_tablesをUNNESTして集計し、
        各テーブルごとの参照回数とユニーク参照ユーザー数を算出する。

        Args:
            project_id: GCPプロジェクトID
            region: BigQueryリージョン（例: region-us）

        Returns:
            テーブル利用統計のリスト

        Raises:
            ValueError: project_idが空文字の場合
            google.api_core.exceptions.GoogleAPIError: BigQuery API呼び出しに失敗した場合
        """
        if not project_id:
            raise ValueError("project_idは空文字にできません")

        client = bigquery.Client(project=project_id)

        query = f"""
            SELECT
                t.dataset_id,
                t.table_id,
                COUNT(*) AS reference_count,
                COUNT(DISTINCT user_email) AS unique_users
            FROM `{region}`.INFORMATION_SCHEMA.JOBS_BY_PROJECT,
                UNNEST(referenced_tables) AS t
            WHERE
                t.project_id = @project_id
                AND NOT STARTS_WITH(t.dataset_id, '_')
                AND NOT STARTS_WITH(t.dataset_id, 'auditlog')
                AND NOT STARTS_WITH(t.table_id, 'INFORMATION_SCHEMA')
                AND DATE(creation_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
            GROUP BY t.dataset_id, t.table_id
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("project_id", "STRING", project_id),
            ]
        )

        query_job = client.query(query, job_config=job_config)
        results = query_job.result()

        usage_stats: list[TableUsage] = []
        row: Any
        for row in results:  # pyright: ignore[reportUnknownVariableType]
            usage_stats.append(
                TableUsage(
                    dataset_id=row.dataset_id,
                    table_id=row.table_id,
                    reference_count=row.reference_count,
                    unique_users=row.unique_users,
                )
            )

        return usage_stats
