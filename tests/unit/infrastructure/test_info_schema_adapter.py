"""InfoSchemaAdapterのユニットテスト。

INFORMATION_SCHEMA.JOBS_BY_PROJECTからテーブル参照回数を取得する
アダプターのテストケースを定義する。
"""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock

import pytest
from google.api_core import exceptions as api_exceptions

from bq_table_reference.domain.exceptions import (
    PermissionDeniedError,
    QueryTimeoutError,
)
from bq_table_reference.domain.models import (
    DataSource,
    FilterConfig,
    TableAccessCount,
)
from bq_table_reference.domain.protocols import TableAccessDataSourceProtocol
from bq_table_reference.infrastructure.info_schema_adapter import (
    InfoSchemaAdapter,
    build_query,
    parse_query_results,
)


class TestBuildQuery:
    """build_query関数のテスト。"""

    def test_basic_query_contains_jobs_by_project(self) -> None:
        """基本クエリがJOBS_BY_PROJECTを含むことを検証する。"""
        filter_config = FilterConfig()
        query = build_query(
            project_id="my-project",
            filter_config=filter_config,
            region="us",
        )
        assert "INFORMATION_SCHEMA.JOBS_BY_PROJECT" in query
        assert "region-us" in query

    def test_basic_query_contains_unnest_referenced_tables(self) -> None:
        """基本クエリがUNNEST(referenced_tables)を含むことを検証する。"""
        filter_config = FilterConfig()
        query = build_query(
            project_id="my-project",
            filter_config=filter_config,
            region="us",
        )
        assert "UNNEST(referenced_tables)" in query

    def test_period_filter_in_where_clause(self) -> None:
        """期間フィルタがWHERE句に反映されることを検証する。"""
        filter_config = FilterConfig(days=30)
        query = build_query(
            project_id="my-project",
            filter_config=filter_config,
            region="us",
        )
        assert "creation_time" in query
        assert "TIMESTAMP_SUB" in query or "INTERVAL" in query

    def test_dataset_filter_in_where_clause(self) -> None:
        """データセットフィルタがWHERE句に反映されることを検証する。"""
        filter_config = FilterConfig(dataset_filter="my_dataset")
        query = build_query(
            project_id="my-project",
            filter_config=filter_config,
            region="us",
        )
        assert "my_dataset" in query

    def test_table_pattern_with_regexp_contains(self) -> None:
        """テーブルパターンがREGEXP_CONTAINS句に反映されることを検証する。"""
        filter_config = FilterConfig(table_pattern=".*_events$")
        query = build_query(
            project_id="my-project",
            filter_config=filter_config,
            region="us",
        )
        assert "REGEXP_CONTAINS" in query
        assert ".*_events$" in query

    def test_explicit_date_range(self) -> None:
        """明示的な日付範囲が正しく反映されることを検証する。"""
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        filter_config = FilterConfig(start_date=start, end_date=end)
        query = build_query(
            project_id="my-project",
            filter_config=filter_config,
            region="us",
        )
        assert "2024-01-01" in query
        assert "2024-01-31" in query

    def test_region_parameter(self) -> None:
        """リージョンパラメータが正しく反映されることを検証する。"""
        filter_config = FilterConfig()
        query_us = build_query(
            project_id="my-project",
            filter_config=filter_config,
            region="us",
        )
        query_asia = build_query(
            project_id="my-project",
            filter_config=filter_config,
            region="asia-northeast1",
        )
        assert "region-us" in query_us
        assert "region-asia-northeast1" in query_asia


class TestParseQueryResults:
    """parse_query_results関数のテスト。"""

    def test_parse_single_row(self) -> None:
        """単一行のパース結果を検証する。"""
        mock_rows: list[dict[str, Any]] = [
            {
                "project_id": "my-project",
                "dataset_id": "my_dataset",
                "table_id": "my_table",
                "access_count": 100,
            }
        ]
        results = parse_query_results(mock_rows)
        assert len(results) == 1
        assert isinstance(results[0], TableAccessCount)
        assert results[0].project_id == "my-project"
        assert results[0].dataset_id == "my_dataset"
        assert results[0].table_id == "my_table"
        assert results[0].access_count == 100
        assert results[0].source == DataSource.INFORMATION_SCHEMA

    def test_parse_multiple_rows(self) -> None:
        """複数行のパース結果を検証する。"""
        mock_rows: list[dict[str, Any]] = [
            {
                "project_id": "project1",
                "dataset_id": "dataset1",
                "table_id": "table1",
                "access_count": 50,
            },
            {
                "project_id": "project2",
                "dataset_id": "dataset2",
                "table_id": "table2",
                "access_count": 75,
            },
        ]
        results = parse_query_results(mock_rows)
        assert len(results) == 2
        assert results[0].access_count == 50
        assert results[1].access_count == 75

    def test_parse_empty_results(self) -> None:
        """空の結果のパースを検証する。"""
        results = parse_query_results([])
        assert results == []

    def test_progress_callback_called(self) -> None:
        """進捗コールバックが呼び出されることを検証する。"""
        mock_rows: list[dict[str, Any]] = [
            {
                "project_id": "my-project",
                "dataset_id": "my_dataset",
                "table_id": "my_table",
                "access_count": 100,
            }
        ]
        callback = MagicMock()
        parse_query_results(mock_rows, progress_callback=callback)
        callback.assert_called()


class TestInfoSchemaAdapter:
    """InfoSchemaAdapterクラスのテスト。"""

    def test_implements_protocol(self) -> None:
        """TableAccessDataSourceProtocolを満たすことを検証する。"""
        mock_client = MagicMock()
        adapter = InfoSchemaAdapter(bq_client=mock_client, region="us")
        assert isinstance(adapter, TableAccessDataSourceProtocol)

    def test_fetch_table_access_executes_query(self) -> None:
        """fetch_table_accessがクエリを実行することを検証する。"""
        mock_client = MagicMock()
        mock_job = MagicMock()
        mock_job.result.return_value = []
        mock_client.query.return_value = mock_job

        adapter = InfoSchemaAdapter(bq_client=mock_client, region="us")
        filter_config = FilterConfig()

        adapter.fetch_table_access(
            project_id="my-project",
            filter_config=filter_config,
        )

        mock_client.query.assert_called_once()
        # クエリ文字列にJOBS_BY_PROJECTが含まれることを確認
        call_args = mock_client.query.call_args
        query_str = call_args[0][0]
        assert "INFORMATION_SCHEMA.JOBS_BY_PROJECT" in query_str

    def test_fetch_table_access_returns_table_access_counts(self) -> None:
        """fetch_table_accessがTableAccessCountリストを返すことを検証する。"""
        mock_client = MagicMock()
        mock_job = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: {
            "project_id": "my-project",
            "dataset_id": "my_dataset",
            "table_id": "my_table",
            "access_count": 42,
        }[key]
        mock_job.result.return_value = [mock_row]
        mock_client.query.return_value = mock_job

        adapter = InfoSchemaAdapter(bq_client=mock_client, region="us")
        filter_config = FilterConfig()

        results = adapter.fetch_table_access(
            project_id="my-project",
            filter_config=filter_config,
        )

        assert len(results) == 1
        assert isinstance(results[0], TableAccessCount)
        assert results[0].access_count == 42


class TestInfoSchemaAdapterErrorHandling:
    """InfoSchemaAdapterのエラーハンドリングテスト。"""

    def test_permission_denied_raises_permission_error(self) -> None:
        """403エラー時にPermissionDeniedErrorを送出することを検証する。"""
        mock_client = MagicMock()
        mock_client.query.side_effect = api_exceptions.Forbidden("Access Denied")

        adapter = InfoSchemaAdapter(bq_client=mock_client, region="us")
        filter_config = FilterConfig()

        with pytest.raises(PermissionDeniedError) as exc_info:
            adapter.fetch_table_access(
                project_id="my-project",
                filter_config=filter_config,
            )
        assert "roles/bigquery.resourceViewer" in str(exc_info.value)

    def test_timeout_raises_query_timeout_error(self) -> None:
        """タイムアウト時にQueryTimeoutErrorを送出することを検証する。"""
        mock_client = MagicMock()
        mock_job = MagicMock()
        mock_job.result.side_effect = api_exceptions.DeadlineExceeded("Timeout")
        mock_client.query.return_value = mock_job

        adapter = InfoSchemaAdapter(bq_client=mock_client, region="us")
        filter_config = FilterConfig()

        with pytest.raises(QueryTimeoutError):
            adapter.fetch_table_access(
                project_id="my-project",
                filter_config=filter_config,
            )

    def test_permission_denied_message_contains_required_role(self) -> None:
        """エラーメッセージにroles/bigquery.resourceViewerが含まれることを検証する。"""
        mock_client = MagicMock()
        mock_client.query.side_effect = api_exceptions.Forbidden("Access Denied")

        adapter = InfoSchemaAdapter(bq_client=mock_client, region="us")
        filter_config = FilterConfig()

        with pytest.raises(PermissionDeniedError) as exc_info:
            adapter.fetch_table_access(
                project_id="my-project",
                filter_config=filter_config,
            )
        error_message = str(exc_info.value)
        assert "bigquery.resourceViewer" in error_message or "bigquery.jobs.listAll" in error_message
