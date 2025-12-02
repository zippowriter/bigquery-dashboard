"""テーブルアクセス回数関連モデルのテスト。

DataSource, TableAccessCount, FilterConfig, TableAccessResult の
生成、属性アクセス、バリデーションを検証する。
"""

import pytest

from bq_table_reference.domain.models import DataSource


class TestDataSource:
    """DataSource 列挙型のテスト。"""

    def test_data_source_has_information_schema_value(self) -> None:
        """DataSource に INFORMATION_SCHEMA 値が存在することを検証する。"""
        assert hasattr(DataSource, "INFORMATION_SCHEMA")
        assert DataSource.INFORMATION_SCHEMA.value == "information_schema"

    def test_data_source_has_audit_log_value(self) -> None:
        """DataSource に AUDIT_LOG 値が存在することを検証する。"""
        assert hasattr(DataSource, "AUDIT_LOG")
        assert DataSource.AUDIT_LOG.value == "audit_log"

    def test_data_source_is_str_enum(self) -> None:
        """DataSource が StrEnum であることを検証する。"""
        # StrEnum なので文字列として使用可能
        assert str(DataSource.INFORMATION_SCHEMA) == "information_schema"
        assert str(DataSource.AUDIT_LOG) == "audit_log"

    def test_data_source_equality_with_string(self) -> None:
        """DataSource が文字列と比較可能であることを検証する。"""
        assert DataSource.INFORMATION_SCHEMA == "information_schema"
        assert DataSource.AUDIT_LOG == "audit_log"


class TestTableAccessCount:
    """TableAccessCount モデルのテスト。"""

    def test_create_table_access_count(self) -> None:
        """TableAccessCount インスタンスを正常に生成できることを検証する。"""
        from bq_table_reference.domain.models import TableAccessCount

        count = TableAccessCount(
            project_id="my-project",
            dataset_id="my_dataset",
            table_id="my_table",
            access_count=42,
            source=DataSource.INFORMATION_SCHEMA,
        )

        assert count.project_id == "my-project"
        assert count.dataset_id == "my_dataset"
        assert count.table_id == "my_table"
        assert count.access_count == 42
        assert count.source == DataSource.INFORMATION_SCHEMA

    def test_full_path_property(self) -> None:
        """full_path プロパティが project.dataset.table 形式を返すことを検証する。"""
        from bq_table_reference.domain.models import TableAccessCount

        count = TableAccessCount(
            project_id="proj",
            dataset_id="ds",
            table_id="tbl",
            access_count=10,
            source=DataSource.AUDIT_LOG,
        )

        assert count.full_path == "proj.ds.tbl"

    def test_table_access_count_is_immutable(self) -> None:
        """TableAccessCount がイミュータブルであることを検証する。"""
        from pydantic import ValidationError

        from bq_table_reference.domain.models import TableAccessCount

        count = TableAccessCount(
            project_id="my-project",
            dataset_id="my_dataset",
            table_id="my_table",
            access_count=42,
            source=DataSource.INFORMATION_SCHEMA,
        )

        with pytest.raises(ValidationError):
            count.access_count = 100  # type: ignore[misc]

    def test_access_count_must_be_non_negative(self) -> None:
        """access_count は0以上であることを検証する。"""
        from pydantic import ValidationError

        from bq_table_reference.domain.models import TableAccessCount

        with pytest.raises(ValidationError):
            TableAccessCount(
                project_id="my-project",
                dataset_id="my_dataset",
                table_id="my_table",
                access_count=-1,
                source=DataSource.INFORMATION_SCHEMA,
            )


class TestFilterConfig:
    """FilterConfig モデルのテスト。"""

    def test_default_values(self) -> None:
        """デフォルト値が正しく設定されることを検証する。"""
        from bq_table_reference.domain.models import FilterConfig

        config = FilterConfig()

        assert config.days == 30
        assert config.start_date is None
        assert config.end_date is None
        assert config.dataset_filter is None
        assert config.table_pattern is None
        assert config.min_access_count == 0

    def test_custom_days(self) -> None:
        """days を指定した場合に反映されることを検証する。"""
        from bq_table_reference.domain.models import FilterConfig

        config = FilterConfig(days=60)

        assert config.days == 60

    def test_explicit_date_range(self) -> None:
        """start_date と end_date を明示指定できることを検証する。"""
        from datetime import datetime, timezone

        from bq_table_reference.domain.models import FilterConfig

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        config = FilterConfig(start_date=start, end_date=end)

        assert config.start_date == start
        assert config.end_date == end

    def test_filter_options(self) -> None:
        """dataset_filter, table_pattern, min_access_count を設定できることを検証する。"""
        from bq_table_reference.domain.models import FilterConfig

        config = FilterConfig(
            dataset_filter="my_dataset",
            table_pattern="temp_.*",
            min_access_count=5,
        )

        assert config.dataset_filter == "my_dataset"
        assert config.table_pattern == "temp_.*"
        assert config.min_access_count == 5

    def test_days_must_be_positive(self) -> None:
        """days は1以上であることを検証する。"""
        from pydantic import ValidationError

        from bq_table_reference.domain.models import FilterConfig

        with pytest.raises(ValidationError):
            FilterConfig(days=0)

    def test_min_access_count_must_be_non_negative(self) -> None:
        """min_access_count は0以上であることを検証する。"""
        from pydantic import ValidationError

        from bq_table_reference.domain.models import FilterConfig

        with pytest.raises(ValidationError):
            FilterConfig(min_access_count=-1)

    def test_filter_config_is_immutable(self) -> None:
        """FilterConfig がイミュータブルであることを検証する。"""
        from pydantic import ValidationError

        from bq_table_reference.domain.models import FilterConfig

        config = FilterConfig()

        with pytest.raises(ValidationError):
            config.days = 60  # type: ignore[misc]


class TestTableAccessResult:
    """TableAccessResult モデルのテスト。"""

    def test_create_table_access_result(self) -> None:
        """TableAccessResult インスタンスを正常に生成できることを検証する。"""
        from datetime import datetime, timezone

        from bq_table_reference.domain.models import TableAccessResult

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)

        result = TableAccessResult(
            start_date=start,
            end_date=end,
            project_id="my-project",
            info_schema_results=[],
            audit_log_results=[],
            merged_results=[],
            warnings=[],
        )

        assert result.start_date == start
        assert result.end_date == end
        assert result.project_id == "my-project"

    def test_separate_result_lists(self) -> None:
        """info_schema_results, audit_log_results, merged_results を個別に保持できることを検証する。"""
        from datetime import datetime, timezone

        from bq_table_reference.domain.models import (
            TableAccessCount,
            TableAccessResult,
        )

        info_count = TableAccessCount(
            project_id="proj",
            dataset_id="ds",
            table_id="tbl1",
            access_count=10,
            source=DataSource.INFORMATION_SCHEMA,
        )
        audit_count = TableAccessCount(
            project_id="proj",
            dataset_id="ds",
            table_id="tbl2",
            access_count=5,
            source=DataSource.AUDIT_LOG,
        )
        merged_count = TableAccessCount(
            project_id="proj",
            dataset_id="ds",
            table_id="tbl1",
            access_count=10,
            source=DataSource.INFORMATION_SCHEMA,
        )

        result = TableAccessResult(
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            project_id="proj",
            info_schema_results=[info_count],
            audit_log_results=[audit_count],
            merged_results=[merged_count],
            warnings=[],
        )

        assert len(result.info_schema_results) == 1
        assert len(result.audit_log_results) == 1
        assert len(result.merged_results) == 1
        assert result.info_schema_results[0].table_id == "tbl1"
        assert result.audit_log_results[0].table_id == "tbl2"

    def test_warnings_list(self) -> None:
        """warnings リストを保持できることを検証する。"""
        from datetime import datetime, timezone

        from bq_table_reference.domain.models import TableAccessResult

        result = TableAccessResult(
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            project_id="proj",
            info_schema_results=[],
            audit_log_results=[],
            merged_results=[],
            warnings=["Warning 1", "Warning 2"],
        )

        assert len(result.warnings) == 2
        assert "Warning 1" in result.warnings
        assert "Warning 2" in result.warnings

    def test_empty_result_lists_default(self) -> None:
        """結果リストのデフォルト値が空リストであることを検証する。"""
        from datetime import datetime, timezone

        from bq_table_reference.domain.models import TableAccessResult

        result = TableAccessResult(
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            project_id="proj",
        )

        assert result.info_schema_results == []
        assert result.audit_log_results == []
        assert result.merged_results == []
        assert result.warnings == []


class TestExceptions:
    """例外クラスのテスト。"""

    def test_audit_log_not_enabled_error_default_message(self) -> None:
        """AuditLogNotEnabledError のデフォルトメッセージが有効化手順を含むことを検証する。"""
        from bq_table_reference.domain.exceptions import AuditLogNotEnabledError

        error = AuditLogNotEnabledError()
        message = str(error)

        assert "Data Access" in message or "BigQuery" in message
        assert "有効化" in message or "enable" in message.lower()

    def test_audit_log_not_enabled_error_custom_message(self) -> None:
        """AuditLogNotEnabledError にカスタムメッセージを渡せることを検証する。"""
        from bq_table_reference.domain.exceptions import AuditLogNotEnabledError

        custom_msg = "Custom error message"
        error = AuditLogNotEnabledError(custom_msg)

        assert str(error) == custom_msg

    def test_audit_log_not_enabled_error_inherits_from_base(self) -> None:
        """AuditLogNotEnabledError が DatasetLoaderError を継承していることを検証する。"""
        from bq_table_reference.domain.exceptions import (
            AuditLogNotEnabledError,
            DatasetLoaderError,
        )

        error = AuditLogNotEnabledError()

        assert isinstance(error, DatasetLoaderError)

    def test_query_timeout_error_default_message(self) -> None:
        """QueryTimeoutError のデフォルトメッセージがタイムアウト調整方法を含むことを検証する。"""
        from bq_table_reference.domain.exceptions import QueryTimeoutError

        error = QueryTimeoutError()
        message = str(error)

        assert "タイムアウト" in message or "timeout" in message.lower()

    def test_query_timeout_error_custom_message(self) -> None:
        """QueryTimeoutError にカスタムメッセージを渡せることを検証する。"""
        from bq_table_reference.domain.exceptions import QueryTimeoutError

        custom_msg = "Query took too long"
        error = QueryTimeoutError(custom_msg)

        assert str(error) == custom_msg

    def test_query_timeout_error_inherits_from_base(self) -> None:
        """QueryTimeoutError が DatasetLoaderError を継承していることを検証する。"""
        from bq_table_reference.domain.exceptions import (
            DatasetLoaderError,
            QueryTimeoutError,
        )

        error = QueryTimeoutError()

        assert isinstance(error, DatasetLoaderError)

    def test_permission_denied_error_with_required_permission(self) -> None:
        """PermissionDeniedError が必要な権限情報を含むことを検証する。"""
        from bq_table_reference.domain.exceptions import PermissionDeniedError

        error = PermissionDeniedError()
        message = str(error)

        # デフォルトメッセージにロール情報が含まれている
        assert "roles/" in message or "権限" in message
