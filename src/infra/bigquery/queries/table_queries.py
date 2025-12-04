"""テーブル関連のSQLクエリビルダー."""

from collections.abc import Sequence
from textwrap import dedent


# 除外するデータセットのリスト
EXCLUDED_DATASETS = [
    "auditlog_bigquery_v2",
    "abematv_bigquery_log",
    "patriot_abematv_bigquery_log",
    "patriot_117478195",
    "patriot_153256568",
]


def build_list_tables_query(project_ids: Sequence[str]) -> str:
    """INFORMATION_SCHEMA.TABLESからテーブル一覧を取得するクエリを生成する.

    Args:
        project_ids: 対象プロジェクトIDのリスト

    Returns:
        SQL クエリ文字列
    """
    if not project_ids:
        return ""

    cte_parts: list[str] = []
    excluded_list = ", ".join(f"'{ds}'" for ds in EXCLUDED_DATASETS)

    for i, project_id in enumerate(project_ids):
        cte_name = f"tables_{i}"
        cte = dedent(f"""
            {cte_name} AS (
                SELECT
                    table_catalog AS project_id,
                    table_schema AS dataset_id,
                    table_name AS table_id,
                    table_type
                FROM `{project_id}.region-us`.INFORMATION_SCHEMA.TABLES
                WHERE
                    table_schema NOT IN ({excluded_list})
                    AND table_schema NOT LIKE r'test_%'
            )
        """)
        cte_parts.append(cte)

    with_clause = "WITH " + ",\n\n".join(cte_parts)

    if len(project_ids) == 1:
        select_clause = dedent("""
            SELECT project_id, dataset_id, table_id, table_type
            FROM tables_0
        """)
    else:
        select_clause = dedent("""
            SELECT project_id, dataset_id, table_id, table_type
            FROM tables_0
        """)
        for i in range(1, len(project_ids)):
            select_clause += dedent(f"""
                FULL OUTER JOIN tables_{i} USING (project_id, dataset_id, table_id, table_type)
            """)

    return with_clause + select_clause


def build_reference_count_query(
    days_back: int = 180,
) -> str:
    """INFORMATION_SCHEMA.JOBS_BY_PROJECTからテーブル参照回数を取得するクエリを生成する.

    Args:
        days_back: 過去何日分を対象とするか

    Returns:
        SQL クエリ文字列
    """

    return dedent(f"""
        SELECT
            project_id,
            dataset_id,
            table_id,
            SUM(job_count) AS job_count,
            SUM(unique_user) AS unique_user
        FROM `abematv-data.test_kono.table_access_count`
        WHERE
            dt >= DATE_SUB(CURRENT_DATE('Asia/Tokyo'), INTERVAL {days_back} DAY)
        GROUP BY
            1, 2, 3
        """)
