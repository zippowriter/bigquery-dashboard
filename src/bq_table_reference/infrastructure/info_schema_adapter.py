"""INFORMATION_SCHEMAからテーブル参照情報を取得するアダプター。

BigQueryのINFORMATION_SCHEMA.JOBS_BY_PROJECTビューを使用して、
テーブルの参照回数を取得する。
"""

from collections.abc import Callable, Iterable, Mapping
from typing import Any

from google.api_core import exceptions as api_exceptions
from google.cloud import bigquery

from bq_table_reference.domain.exceptions import (
    NetworkError,
    PermissionDeniedError,
    QueryTimeoutError,
)
from bq_table_reference.domain.models import (
    DataSource,
    FilterConfig,
    TableAccessCount,
)


# SQLクエリテンプレート
_BASE_QUERY_TEMPLATE = """
SELECT
    ref.project_id,
    ref.dataset_id,
    ref.table_id,
    COUNT(*) AS access_count
FROM
    `{project_id}.region-{region}.INFORMATION_SCHEMA.JOBS_BY_PROJECT`,
    UNNEST(referenced_tables) AS ref
WHERE
    job_type = 'QUERY'
    AND state = 'DONE'
    {time_filter}
    {dataset_filter}
    {table_pattern_filter}
GROUP BY
    ref.project_id,
    ref.dataset_id,
    ref.table_id
ORDER BY
    access_count DESC
"""


def build_query(
    project_id: str,
    filter_config: FilterConfig,
    region: str,
) -> str:
    """INFORMATION_SCHEMAへのクエリを生成する。

    Args:
        project_id: GCPプロジェクトID
        filter_config: フィルタリング条件
        region: BigQueryリージョン

    Returns:
        生成されたSQLクエリ文字列
    """
    # 期間フィルタの生成
    if filter_config.start_date is not None and filter_config.end_date is not None:
        start_str = filter_config.start_date.strftime("%Y-%m-%d %H:%M:%S")
        end_str = filter_config.end_date.strftime("%Y-%m-%d %H:%M:%S")
        time_filter = (
            f"AND creation_time >= TIMESTAMP('{start_str}') "
            f"AND creation_time < TIMESTAMP('{end_str}')"
        )
    else:
        time_filter = (
            f"AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), "
            f"INTERVAL {filter_config.days} DAY)"
        )

    # データセットフィルタの生成
    if filter_config.dataset_filter is not None:
        dataset_filter = f"AND ref.dataset_id = '{filter_config.dataset_filter}'"
    else:
        dataset_filter = ""

    # テーブルパターンフィルタの生成
    if filter_config.table_pattern is not None:
        table_pattern_filter = (
            f"AND REGEXP_CONTAINS(ref.table_id, r'{filter_config.table_pattern}')"
        )
    else:
        table_pattern_filter = ""

    query = _BASE_QUERY_TEMPLATE.format(
        project_id=project_id,
        region=region,
        time_filter=time_filter,
        dataset_filter=dataset_filter,
        table_pattern_filter=table_pattern_filter,
    )

    return query


def parse_query_results(
    rows: Iterable[dict[str, Any]],
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> list[TableAccessCount]:
    """クエリ結果をTableAccessCountリストにパースする。

    Args:
        rows: BigQueryクエリ結果の行イテラブル
        progress_callback: 進捗コールバック関数

    Returns:
        TableAccessCountのリスト
    """
    results: list[TableAccessCount] = []
    row_list = list(rows)
    total = len(row_list)

    for i, row in enumerate(row_list):
        table_access = TableAccessCount(
            project_id=row["project_id"],
            dataset_id=row["dataset_id"],
            table_id=row["table_id"],
            access_count=row["access_count"],
            source=DataSource.INFORMATION_SCHEMA,
        )
        results.append(table_access)

        if progress_callback is not None:
            progress_callback(i + 1, total, f"Processing row {i + 1}/{total}")

    return results


class InfoSchemaAdapter:
    """INFORMATION_SCHEMAからテーブル参照情報を取得するアダプター。

    BigQueryのINFORMATION_SCHEMA.JOBS_BY_PROJECTビューにクエリを実行し、
    テーブルの参照回数を取得する。

    Example:
        >>> from google.cloud import bigquery
        >>> client = bigquery.Client()
        >>> adapter = InfoSchemaAdapter(bq_client=client, region="us")
        >>> results = adapter.fetch_table_access("my-project", FilterConfig())
    """

    def __init__(
        self,
        bq_client: bigquery.Client,
        region: str = "us",
    ) -> None:
        """初期化。

        Args:
            bq_client: BigQueryクライアント
            region: BigQueryリージョン（デフォルト: us）
        """
        self._client = bq_client
        self._region = region

    def fetch_table_access(
        self,
        project_id: str,
        filter_config: FilterConfig,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> list[TableAccessCount]:
        """INFORMATION_SCHEMAからテーブル参照回数を取得する。

        Args:
            project_id: GCPプロジェクトID
            filter_config: フィルタリング条件
            progress_callback: 進捗コールバック関数

        Returns:
            TableAccessCountのリスト

        Raises:
            PermissionDeniedError: bigquery.jobs.listAll権限がない場合
            QueryTimeoutError: クエリがタイムアウトした場合
            NetworkError: ネットワークエラーが発生した場合
        """
        query = build_query(
            project_id=project_id,
            filter_config=filter_config,
            region=self._region,
        )

        try:
            query_job = self._client.query(query)
            rows = query_job.result()
        except api_exceptions.Forbidden as e:
            raise PermissionDeniedError(
                "INFORMATION_SCHEMAへのアクセス権限がありません。"
                "'roles/bigquery.resourceViewer' ロールまたは "
                "'bigquery.jobs.listAll' 権限が必要です。"
            ) from e
        except api_exceptions.DeadlineExceeded as e:
            raise QueryTimeoutError() from e
        except api_exceptions.ServiceUnavailable as e:
            raise NetworkError() from e

        # BigQuery RowIterator をdict形式に変換
        row_dicts = self._convert_rows_to_dicts(rows)

        return parse_query_results(row_dicts, progress_callback)

    def _convert_rows_to_dicts(
        self,
        rows: Iterable[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        """BigQueryの行データを辞書形式に変換する。

        Args:
            rows: BigQueryクエリ結果の行イテラブル

        Returns:
            辞書形式の行データリスト
        """
        result: list[dict[str, Any]] = []
        for row in rows:
            row_dict: dict[str, Any] = {
                "project_id": str(row["project_id"]),
                "dataset_id": str(row["dataset_id"]),
                "table_id": str(row["table_id"]),
                "access_count": int(row["access_count"]),
            }
            result.append(row_dict)
        return result
