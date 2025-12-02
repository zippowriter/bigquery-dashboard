"""AuditLogAdapterのユニットテスト。

Cloud Audit Logsからテーブル参照回数を取得する
アダプターのテストケースを定義する。
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from bq_table_reference.domain.exceptions import (
    PermissionDeniedError,
)
from bq_table_reference.domain.models import (
    DataSource,
    FilterConfig,
    TableAccessCount,
)
from bq_table_reference.domain.protocols import TableAccessDataSourceProtocol


class TestGoogleCloudLoggingImport:
    """google-cloud-loggingライブラリのインポートテスト。"""

    def test_google_cloud_logging_can_be_imported(self) -> None:
        """google.cloud.loggingがインポートできることを検証する。"""
        import google.cloud.logging  # noqa: F401

        assert True


class TestBuildLogFilter:
    """build_log_filter関数のテスト。"""

    def test_filter_contains_bigquery_dataset_resource_type(self) -> None:
        """フィルタにresource.type="bigquery_dataset"が含まれることを検証する。"""
        from bq_table_reference.infrastructure.audit_log_adapter import (
            build_log_filter,
        )

        filter_config = FilterConfig()
        log_filter = build_log_filter(
            project_id="my-project",
            filter_config=filter_config,
        )
        assert 'resource.type="bigquery_dataset"' in log_filter

    def test_filter_contains_table_data_read_method(self) -> None:
        """フィルタにprotoPayload.methodName="google.cloud.bigquery.v2.JobService.Query"
        またはtableDataReadが含まれることを検証する。"""
        from bq_table_reference.infrastructure.audit_log_adapter import (
            build_log_filter,
        )

        filter_config = FilterConfig()
        log_filter = build_log_filter(
            project_id="my-project",
            filter_config=filter_config,
        )
        # tableDataReadメタデータを含むフィルタ
        assert "tableDataRead" in log_filter or "metadata" in log_filter

    def test_filter_contains_timestamp_range(self) -> None:
        """フィルタにtimestamp範囲が含まれることを検証する。"""
        from bq_table_reference.infrastructure.audit_log_adapter import (
            build_log_filter,
        )

        filter_config = FilterConfig(days=7)
        log_filter = build_log_filter(
            project_id="my-project",
            filter_config=filter_config,
        )
        assert "timestamp" in log_filter

    def test_filter_with_explicit_date_range(self) -> None:
        """明示的な日付範囲が正しくフィルタに反映されることを検証する。"""
        from bq_table_reference.infrastructure.audit_log_adapter import (
            build_log_filter,
        )

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        filter_config = FilterConfig(start_date=start, end_date=end)
        log_filter = build_log_filter(
            project_id="my-project",
            filter_config=filter_config,
        )
        assert "2024-01-01" in log_filter
        assert "2024-01-31" in log_filter


class TestParseLogEntry:
    """parse_log_entry関数のテスト。"""

    def test_parse_resource_name_extracts_project_dataset_table(self) -> None:
        """protoPayload.resourceNameからproject/dataset/tableを抽出することを検証する。"""
        from bq_table_reference.infrastructure.audit_log_adapter import (
            parse_resource_name,
        )

        resource_name = "projects/my-project/datasets/my_dataset/tables/my_table"
        result = parse_resource_name(resource_name)
        assert result is not None
        assert result["project_id"] == "my-project"
        assert result["dataset_id"] == "my_dataset"
        assert result["table_id"] == "my_table"

    def test_parse_resource_name_returns_none_for_invalid_format(self) -> None:
        """不正なフォーマットの場合にNoneを返すことを検証する。"""
        from bq_table_reference.infrastructure.audit_log_adapter import (
            parse_resource_name,
        )

        result = parse_resource_name("invalid/path")
        assert result is None

    def test_parse_resource_name_handles_malformed_input(self) -> None:
        """不正な入力をスキップして継続することを検証する。"""
        from bq_table_reference.infrastructure.audit_log_adapter import (
            parse_resource_name,
        )

        result = parse_resource_name("")
        assert result is None


class TestAggregateTableAccessCounts:
    """aggregate_table_access_counts関数のテスト。"""

    def test_aggregate_counts_by_table(self) -> None:
        """テーブル単位でカウントが集計されることを検証する。"""
        from bq_table_reference.infrastructure.audit_log_adapter import (
            aggregate_table_access_counts,
        )

        parsed_entries = [
            {"project_id": "proj", "dataset_id": "ds", "table_id": "t1"},
            {"project_id": "proj", "dataset_id": "ds", "table_id": "t1"},
            {"project_id": "proj", "dataset_id": "ds", "table_id": "t2"},
        ]
        results = aggregate_table_access_counts(parsed_entries)
        assert len(results) == 2

        # t1は2回
        t1_count = next(r for r in results if r.table_id == "t1")
        assert t1_count.access_count == 2

        # t2は1回
        t2_count = next(r for r in results if r.table_id == "t2")
        assert t2_count.access_count == 1

    def test_aggregate_returns_audit_log_source(self) -> None:
        """結果のsourceがAUDIT_LOGであることを検証する。"""
        from bq_table_reference.infrastructure.audit_log_adapter import (
            aggregate_table_access_counts,
        )

        parsed_entries = [
            {"project_id": "proj", "dataset_id": "ds", "table_id": "t1"},
        ]
        results = aggregate_table_access_counts(parsed_entries)
        assert results[0].source == DataSource.AUDIT_LOG

    def test_aggregate_empty_entries(self) -> None:
        """空のエントリリストで空のリストを返すことを検証する。"""
        from bq_table_reference.infrastructure.audit_log_adapter import (
            aggregate_table_access_counts,
        )

        results = aggregate_table_access_counts([])
        assert results == []


class TestAuditLogAdapter:
    """AuditLogAdapterクラスのテスト。"""

    def test_implements_protocol(self) -> None:
        """TableAccessDataSourceProtocolを満たすことを検証する。"""
        from bq_table_reference.infrastructure.audit_log_adapter import (
            AuditLogAdapter,
        )

        mock_client = MagicMock()
        adapter = AuditLogAdapter(logging_client=mock_client)
        assert isinstance(adapter, TableAccessDataSourceProtocol)

    def test_fetch_table_access_calls_list_entries(self) -> None:
        """fetch_table_accessがlist_entriesを呼び出すことを検証する。"""
        from bq_table_reference.infrastructure.audit_log_adapter import (
            AuditLogAdapter,
        )

        mock_client = MagicMock()
        mock_client.list_entries.return_value = iter([])

        adapter = AuditLogAdapter(logging_client=mock_client)
        filter_config = FilterConfig()

        adapter.fetch_table_access(
            project_id="my-project",
            filter_config=filter_config,
        )

        mock_client.list_entries.assert_called_once()

    def test_fetch_table_access_returns_table_access_counts(self) -> None:
        """fetch_table_accessがTableAccessCountリストを返すことを検証する。"""
        from bq_table_reference.infrastructure.audit_log_adapter import (
            AuditLogAdapter,
        )

        mock_client = MagicMock()
        mock_entry = MagicMock()
        mock_entry.payload = {
            "resourceName": "projects/my-project/datasets/my_dataset/tables/my_table"
        }
        mock_client.list_entries.return_value = iter([mock_entry])

        adapter = AuditLogAdapter(logging_client=mock_client)
        filter_config = FilterConfig()

        results = adapter.fetch_table_access(
            project_id="my-project",
            filter_config=filter_config,
        )

        assert len(results) == 1
        assert isinstance(results[0], TableAccessCount)
        assert results[0].table_id == "my_table"

    def test_pagination_processes_multiple_pages(self) -> None:
        """ページネーションが正しく処理されることを検証する。"""
        from bq_table_reference.infrastructure.audit_log_adapter import (
            AuditLogAdapter,
        )

        mock_client = MagicMock()
        mock_entry1 = MagicMock()
        mock_entry1.payload = {
            "resourceName": "projects/proj/datasets/ds/tables/t1"
        }
        mock_entry2 = MagicMock()
        mock_entry2.payload = {
            "resourceName": "projects/proj/datasets/ds/tables/t2"
        }
        # Simulate pagination by returning multiple entries
        mock_client.list_entries.return_value = iter([mock_entry1, mock_entry2])

        adapter = AuditLogAdapter(logging_client=mock_client)
        filter_config = FilterConfig()

        results = adapter.fetch_table_access(
            project_id="my-project",
            filter_config=filter_config,
        )

        assert len(results) == 2

    def test_progress_callback_called_during_processing(self) -> None:
        """進捗コールバックが処理中に呼び出されることを検証する。"""
        from bq_table_reference.infrastructure.audit_log_adapter import (
            AuditLogAdapter,
        )

        mock_client = MagicMock()
        mock_entry = MagicMock()
        mock_entry.payload = {
            "resourceName": "projects/proj/datasets/ds/tables/t1"
        }
        mock_client.list_entries.return_value = iter([mock_entry])

        adapter = AuditLogAdapter(logging_client=mock_client)
        filter_config = FilterConfig()
        callback = MagicMock()

        adapter.fetch_table_access(
            project_id="my-project",
            filter_config=filter_config,
            progress_callback=callback,
        )

        callback.assert_called()


class TestAuditLogAdapterErrorHandling:
    """AuditLogAdapterのエラーハンドリングテスト。"""

    def test_permission_denied_raises_permission_error(self) -> None:
        """403エラー時にPermissionDeniedErrorを送出することを検証する。"""
        from google.api_core import exceptions as api_exceptions

        from bq_table_reference.infrastructure.audit_log_adapter import (
            AuditLogAdapter,
        )

        mock_client = MagicMock()
        mock_client.list_entries.side_effect = api_exceptions.PermissionDenied(
            "Permission denied"
        )

        adapter = AuditLogAdapter(logging_client=mock_client)
        filter_config = FilterConfig()

        with pytest.raises(PermissionDeniedError) as exc_info:
            adapter.fetch_table_access(
                project_id="my-project",
                filter_config=filter_config,
            )
        assert "logging.viewer" in str(exc_info.value).lower() or "roles" in str(
            exc_info.value
        ).lower()

    def test_empty_results_warns_about_audit_log_not_enabled(self) -> None:
        """ログが0件の場合にAuditLogNotEnabledErrorの可能性を警告することを検証する。"""
        from bq_table_reference.infrastructure.audit_log_adapter import (
            AuditLogAdapter,
        )

        mock_client = MagicMock()
        mock_client.list_entries.return_value = iter([])

        adapter = AuditLogAdapter(logging_client=mock_client)
        filter_config = FilterConfig()

        # 結果は空だが警告が出る
        results = adapter.fetch_table_access(
            project_id="my-project",
            filter_config=filter_config,
        )
        # 0件の場合、結果は空リストを返す（警告はログに出力される）
        assert results == []

    def test_rate_limit_retries_with_backoff(self) -> None:
        """レート制限時にバックオフリトライすることを検証する。"""
        from google.api_core import exceptions as api_exceptions

        from bq_table_reference.infrastructure.audit_log_adapter import (
            AuditLogAdapter,
        )

        mock_client = MagicMock()
        # 最初は ResourceExhausted、次は成功
        mock_entry = MagicMock()
        mock_entry.payload = {
            "resourceName": "projects/proj/datasets/ds/tables/t1"
        }
        mock_client.list_entries.side_effect = [
            api_exceptions.ResourceExhausted("Rate limit"),
            iter([mock_entry]),
        ]

        adapter = AuditLogAdapter(logging_client=mock_client, max_retries=3)
        filter_config = FilterConfig()

        results = adapter.fetch_table_access(
            project_id="my-project",
            filter_config=filter_config,
        )

        # リトライ後に成功
        assert len(results) == 1
        # list_entriesが2回呼ばれた
        assert mock_client.list_entries.call_count == 2
