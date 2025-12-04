"""テーブル関連のSQLクエリビルダー."""

from collections.abc import Sequence


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
        cte = f"""{cte_name} AS (
    SELECT
        table_catalog AS project_id,
        table_schema AS dataset_id,
        table_name AS table_id,
        table_type
    FROM `{project_id}.region-us`.INFORMATION_SCHEMA.TABLES
    WHERE
        table_schema NOT IN ({excluded_list})
        AND table_schema NOT LIKE r'test_%'
)"""
        cte_parts.append(cte)

    with_clause = "WITH " + ",\n\n".join(cte_parts)

    if len(project_ids) == 1:
        select_clause = """

SELECT project_id, dataset_id, table_id, table_type
FROM tables_0"""
    else:
        select_clause = """

SELECT project_id, dataset_id, table_id, table_type
FROM tables_0"""
        for i in range(1, len(project_ids)):
            select_clause += f"""
FULL OUTER JOIN tables_{i} USING (project_id, dataset_id, table_id, table_type)"""

    return with_clause + select_clause


def build_reference_count_query(
    project_ids: Sequence[str],
    days_back: int = 90,
) -> str:
    """INFORMATION_SCHEMA.JOBS_BY_PROJECTからテーブル参照回数を取得するクエリを生成する.

    Args:
        project_ids: 対象プロジェクトIDのリスト
        days_back: 過去何日分を対象とするか

    Returns:
        SQL クエリ文字列
    """
    if not project_ids:
        return ""

    project_list = ", ".join(f"'{pid}'" for pid in project_ids)

    return f"""WITH job_references AS (
    SELECT
        user_email,
        ref.project_id AS referenced_project,
        ref.dataset_id AS referenced_dataset,
        ref.table_id AS referenced_table
    FROM
        `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT,
        UNNEST(referenced_tables) AS ref
    WHERE
        creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days_back} DAY)
        AND job_type = 'QUERY'
        AND state = 'DONE'
        AND error_result IS NULL
        AND ref.project_id IN ({project_list})
)
SELECT
    referenced_project AS project_id,
    referenced_dataset AS dataset_id,
    referenced_table AS table_id,
    COUNT(*) AS job_count,
    COUNT(DISTINCT user_email) AS unique_user
FROM job_references
GROUP BY
    referenced_project,
    referenced_dataset,
    referenced_table
ORDER BY
    job_count DESC"""
