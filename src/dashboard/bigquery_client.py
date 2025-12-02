"""BigQueryクライアントモジュール。

対象プロジェクトのBigQueryテーブル一覧を取得する機能を提供する。
"""

from typing import Any

from google.cloud import bigquery
from pandas import DataFrame


def fetch_table_list(project_id: str) -> DataFrame:
    """対象プロジェクトの全テーブル一覧を取得する。

    Args:
        project_id: GCPプロジェクトID

    Returns:
        データセット名とテーブル名を含むDataFrame。
        カラム: dataset_id (str), table_id (str)

    Raises:
        ValueError: project_idが空文字の場合
        google.api_core.exceptions.GoogleAPIError: BigQuery API呼び出しに失敗した場合
    """
    if not project_id:
        raise ValueError("project_idは空文字にできません")

    client = bigquery.Client(project=project_id)

    table_list: list[dict[str, str]] = []

    # 全データセットを取得し、各データセット内のテーブルを収集
    # google-cloud-bigqueryライブラリの型定義が不完全なためAnyを使用
    dataset: Any
    for dataset in client.list_datasets():  # pyright: ignore[reportUnknownVariableType]
        table: Any
        for table in client.list_tables(dataset.dataset_id):  # pyright: ignore[reportUnknownVariableType]
            table_list.append(
                {
                    "dataset_id": str(table.dataset_id),
                    "table_id": str(table.table_id),
                }
            )

    if not table_list:
        # 空のDataFrameの場合もカラムを保持するため明示的に設定
        return DataFrame({"dataset_id": [], "table_id": []})
    return DataFrame(table_list)


def fetch_table_usage_stats(project_id: str, region: str = "region-us") -> DataFrame:
    """対象プロジェクトのテーブル利用統計を取得する。

    INFORMATION_SCHEMA.JOBS_BY_PROJECTからreferenced_tablesをUNNESTして集計し、
    各テーブルごとの参照回数とユニーク参照ユーザー数を算出する。

    Args:
        project_id: GCPプロジェクトID
        region: BigQueryリージョン（デフォルト: region-us）

    Returns:
        利用統計を含むDataFrame。
        カラム: dataset_id (str), table_id (str),
               reference_count (int), unique_users (int)

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
        WHERE t.project_id = @project_id
        GROUP BY t.dataset_id, t.table_id
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("project_id", "STRING", project_id),
        ]
    )

    query_job = client.query(query, job_config=job_config)
    results = query_job.result()

    usage_list: list[dict[str, Any]] = []
    row: Any
    for row in results:  # pyright: ignore[reportUnknownVariableType]
        usage_list.append(
            {
                "dataset_id": row.dataset_id,
                "table_id": row.table_id,
                "reference_count": row.reference_count,
                "unique_users": row.unique_users,
            }
        )

    if not usage_list:
        # 空のDataFrameの場合もカラムを保持するため明示的に設定
        return DataFrame(
            {
                "dataset_id": [],
                "table_id": [],
                "reference_count": [],
                "unique_users": [],
            }
        )
    return DataFrame(usage_list)
