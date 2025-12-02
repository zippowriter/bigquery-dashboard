"""BigQueryリポジトリ実装。

BigQuery APIを使用してテーブル情報と利用統計を取得する。
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from google.cloud import bigquery

from src.dashboard.domain.logging import Logger
from src.dashboard.domain.models import TableInfo, TableUsage
from src.dashboard.logging_config import get_logger


class BigQueryTableRepository:
    """BigQuery実装のテーブルリポジトリ。

    BigQuery APIを使用してテーブル情報と利用統計を取得する。
    クライアントはシングルトンとして再利用される。
    """

    _client: bigquery.Client | None = None
    _project_id: str | None = None

    def __init__(self, logger: Logger | None = None) -> None:
        """リポジトリを初期化する。

        Args:
            logger: ロガーインスタンス（省略時はデフォルトロガーを使用）
        """
        self._logger = logger or get_logger()

    def _get_client(self, project_id: str) -> bigquery.Client:
        """BigQueryクライアントを取得する。

        同じプロジェクトIDの場合はキャッシュされたクライアントを再利用する。

        Args:
            project_id: GCPプロジェクトID

        Returns:
            BigQueryクライアント
        """
        if self._client is None or self._project_id != project_id:
            BigQueryTableRepository._client = bigquery.Client(project=project_id)
            BigQueryTableRepository._project_id = project_id
        return self._client  # pyright: ignore[reportReturnType]

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

        self._logger.info("テーブル一覧取得開始", project_id=project_id)
        client = self._get_client(project_id)

        # 全データセットを取得
        # google-cloud-bigqueryライブラリの型定義が不完全なためpyright ignoreを使用
        datasets = list(client.list_datasets())  # pyright: ignore[reportUnknownVariableType]
        self._logger.debug("データセット取得完了", dataset_count=len(datasets))

        if not datasets:
            self._logger.info("テーブル一覧取得完了", count=0)
            return []

        tables: list[TableInfo] = []

        def fetch_tables_for_dataset(dataset_id: str) -> list[TableInfo]:
            """1データセットのテーブル一覧を取得する。"""
            result: list[TableInfo] = []
            for table in client.list_tables(dataset_id):  # pyright: ignore[reportUnknownVariableType]
                result.append(
                    TableInfo(
                        dataset_id=str(table.dataset_id),
                        table_id=str(table.table_id),
                    )
                )
            return result

        # データセット数に応じてワーカー数を調整（最大10）
        max_workers = min(len(datasets), 10)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_dataset = {  # pyright: ignore[reportUnknownVariableType]
                executor.submit(fetch_tables_for_dataset, ds.dataset_id): ds.dataset_id  # pyright: ignore[reportUnknownMemberType]
                for ds in datasets  # pyright: ignore[reportUnknownVariableType]
            }

            for future in as_completed(future_to_dataset):
                tables.extend(future.result())

        self._logger.info("テーブル一覧取得完了", count=len(tables))
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

        self._logger.info("利用統計取得開始", project_id=project_id, region=region)
        client = self._get_client(project_id)

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

        self._logger.debug("BigQueryクエリ実行中")
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

        self._logger.info("利用統計取得完了", count=len(usage_stats))
        return usage_stats

    def fetch_all(
        self, project_id: str, region: str
    ) -> tuple[list[TableInfo], list[TableUsage]]:
        """テーブル一覧と利用統計を並列で一括取得する。

        Args:
            project_id: GCPプロジェクトID
            region: BigQueryリージョン

        Returns:
            (テーブル一覧, 利用統計) のタプル
        """
        self._logger.info("一括取得開始", project_id=project_id, region=region)
        with ThreadPoolExecutor(max_workers=2) as executor:
            tables_future = executor.submit(self.fetch_tables, project_id)
            usage_future = executor.submit(self.fetch_usage_stats, project_id, region)

            tables = tables_future.result()
            usage_stats = usage_future.result()

        self._logger.info("一括取得完了", tables_count=len(tables), usage_count=len(usage_stats))
        return tables, usage_stats
