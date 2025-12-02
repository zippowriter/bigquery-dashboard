"""Tests for TableAccessCounter application service.

This module tests the table access counting use case implementation,
including merge logic, filtering, and error handling.
"""

from bq_table_reference.domain.models import (
    DataSource,
    FilterConfig,
    TableAccessCount,
    TableAccessResult,
)


class TestMergeResults:
    """Tests for merge_results function."""

    def test_merge_two_lists_of_table_access_counts(self) -> None:
        """Should merge two lists of TableAccessCount into one."""
        from bq_table_reference.application.table_access_counter import merge_results

        info_schema_results = [
            TableAccessCount(
                project_id="proj",
                dataset_id="ds",
                table_id="tbl1",
                access_count=10,
                source=DataSource.INFORMATION_SCHEMA,
            ),
        ]
        audit_log_results = [
            TableAccessCount(
                project_id="proj",
                dataset_id="ds",
                table_id="tbl2",
                access_count=5,
                source=DataSource.AUDIT_LOG,
            ),
        ]

        merged = merge_results(info_schema_results, audit_log_results)

        assert len(merged) == 2

    def test_identify_same_table_by_project_dataset_table(self) -> None:
        """Should identify same table by matching project, dataset, and table."""
        from bq_table_reference.application.table_access_counter import merge_results

        # Same table from different sources
        info_schema_results = [
            TableAccessCount(
                project_id="proj",
                dataset_id="ds",
                table_id="tbl1",
                access_count=10,
                source=DataSource.INFORMATION_SCHEMA,
            ),
        ]
        audit_log_results = [
            TableAccessCount(
                project_id="proj",
                dataset_id="ds",
                table_id="tbl1",
                access_count=5,
                source=DataSource.AUDIT_LOG,
            ),
        ]

        merged = merge_results(info_schema_results, audit_log_results)

        # Should result in single entry (merged)
        assert len(merged) == 1
        # The merged entry should have access count from one source
        assert merged[0].full_path == "proj.ds.tbl1"

    def test_duplicate_table_takes_max_value(self) -> None:
        """Should take maximum access count when same table appears in both sources."""
        from bq_table_reference.application.table_access_counter import merge_results

        info_schema_results = [
            TableAccessCount(
                project_id="proj",
                dataset_id="ds",
                table_id="tbl1",
                access_count=10,
                source=DataSource.INFORMATION_SCHEMA,
            ),
        ]
        audit_log_results = [
            TableAccessCount(
                project_id="proj",
                dataset_id="ds",
                table_id="tbl1",
                access_count=25,
                source=DataSource.AUDIT_LOG,
            ),
        ]

        merged = merge_results(info_schema_results, audit_log_results)

        assert len(merged) == 1
        assert merged[0].access_count == 25

    def test_results_sorted_by_access_count_descending(self) -> None:
        """Should sort merged results by access count in descending order."""
        from bq_table_reference.application.table_access_counter import merge_results

        info_schema_results = [
            TableAccessCount(
                project_id="proj",
                dataset_id="ds",
                table_id="tbl1",
                access_count=5,
                source=DataSource.INFORMATION_SCHEMA,
            ),
            TableAccessCount(
                project_id="proj",
                dataset_id="ds",
                table_id="tbl2",
                access_count=15,
                source=DataSource.INFORMATION_SCHEMA,
            ),
        ]
        audit_log_results = [
            TableAccessCount(
                project_id="proj",
                dataset_id="ds",
                table_id="tbl3",
                access_count=10,
                source=DataSource.AUDIT_LOG,
            ),
        ]

        merged = merge_results(info_schema_results, audit_log_results)

        assert len(merged) == 3
        assert merged[0].access_count == 15
        assert merged[1].access_count == 10
        assert merged[2].access_count == 5

    def test_merge_empty_lists(self) -> None:
        """Should handle merging empty lists."""
        from bq_table_reference.application.table_access_counter import merge_results

        merged = merge_results([], [])

        assert merged == []

    def test_merge_with_one_empty_list(self) -> None:
        """Should handle merging when one list is empty."""
        from bq_table_reference.application.table_access_counter import merge_results

        info_schema_results = [
            TableAccessCount(
                project_id="proj",
                dataset_id="ds",
                table_id="tbl1",
                access_count=10,
                source=DataSource.INFORMATION_SCHEMA,
            ),
        ]

        merged = merge_results(info_schema_results, [])

        assert len(merged) == 1
        assert merged[0].access_count == 10


class TestTableAccessCounter:
    """Tests for TableAccessCounter class."""

    def test_info_schema_only_calls_info_schema_adapter(self) -> None:
        """When INFO_SCHEMA option is selected, only info_schema adapter should be called."""
        from bq_table_reference.application.table_access_counter import (
            DataSourceOption,
            TableAccessCounter,
        )
        from bq_table_reference.domain.protocols import ProgressCallback

        info_schema_called = False
        audit_log_called = False

        class MockInfoSchemaAdapter:
            def fetch_table_access(
                self,
                project_id: str,
                filter_config: FilterConfig,
                progress_callback: ProgressCallback | None = None,
            ) -> list[TableAccessCount]:
                nonlocal info_schema_called
                info_schema_called = True
                return [
                    TableAccessCount(
                        project_id=project_id,
                        dataset_id="ds",
                        table_id="tbl",
                        access_count=10,
                        source=DataSource.INFORMATION_SCHEMA,
                    )
                ]

        class MockAuditLogAdapter:
            def fetch_table_access(
                self,
                project_id: str,
                filter_config: FilterConfig,
                progress_callback: ProgressCallback | None = None,
            ) -> list[TableAccessCount]:
                nonlocal audit_log_called
                audit_log_called = True
                return []

        counter = TableAccessCounter(
            info_schema_adapter=MockInfoSchemaAdapter(),
            audit_log_adapter=MockAuditLogAdapter(),
        )

        counter.count_access(
            project_id="test-project",
            filter_config=FilterConfig(),
            source=DataSourceOption.INFO_SCHEMA,
        )

        assert info_schema_called is True
        assert audit_log_called is False

    def test_audit_log_only_calls_audit_log_adapter(self) -> None:
        """When AUDIT_LOG option is selected, only audit_log adapter should be called."""
        from bq_table_reference.application.table_access_counter import (
            DataSourceOption,
            TableAccessCounter,
        )
        from bq_table_reference.domain.protocols import ProgressCallback

        info_schema_called = False
        audit_log_called = False

        class MockInfoSchemaAdapter:
            def fetch_table_access(
                self,
                project_id: str,
                filter_config: FilterConfig,
                progress_callback: ProgressCallback | None = None,
            ) -> list[TableAccessCount]:
                nonlocal info_schema_called
                info_schema_called = True
                return []

        class MockAuditLogAdapter:
            def fetch_table_access(
                self,
                project_id: str,
                filter_config: FilterConfig,
                progress_callback: ProgressCallback | None = None,
            ) -> list[TableAccessCount]:
                nonlocal audit_log_called
                audit_log_called = True
                return [
                    TableAccessCount(
                        project_id=project_id,
                        dataset_id="ds",
                        table_id="tbl",
                        access_count=5,
                        source=DataSource.AUDIT_LOG,
                    )
                ]

        counter = TableAccessCounter(
            info_schema_adapter=MockInfoSchemaAdapter(),
            audit_log_adapter=MockAuditLogAdapter(),
        )

        counter.count_access(
            project_id="test-project",
            filter_config=FilterConfig(),
            source=DataSourceOption.AUDIT_LOG,
        )

        assert info_schema_called is False
        assert audit_log_called is True

    def test_both_option_calls_both_adapters(self) -> None:
        """When BOTH option is selected, both adapters should be called."""
        from bq_table_reference.application.table_access_counter import (
            DataSourceOption,
            TableAccessCounter,
        )
        from bq_table_reference.domain.protocols import ProgressCallback

        info_schema_called = False
        audit_log_called = False

        class MockInfoSchemaAdapter:
            def fetch_table_access(
                self,
                project_id: str,
                filter_config: FilterConfig,
                progress_callback: ProgressCallback | None = None,
            ) -> list[TableAccessCount]:
                nonlocal info_schema_called
                info_schema_called = True
                return [
                    TableAccessCount(
                        project_id=project_id,
                        dataset_id="ds",
                        table_id="tbl",
                        access_count=10,
                        source=DataSource.INFORMATION_SCHEMA,
                    )
                ]

        class MockAuditLogAdapter:
            def fetch_table_access(
                self,
                project_id: str,
                filter_config: FilterConfig,
                progress_callback: ProgressCallback | None = None,
            ) -> list[TableAccessCount]:
                nonlocal audit_log_called
                audit_log_called = True
                return [
                    TableAccessCount(
                        project_id=project_id,
                        dataset_id="ds",
                        table_id="tbl",
                        access_count=5,
                        source=DataSource.AUDIT_LOG,
                    )
                ]

        counter = TableAccessCounter(
            info_schema_adapter=MockInfoSchemaAdapter(),
            audit_log_adapter=MockAuditLogAdapter(),
        )

        counter.count_access(
            project_id="test-project",
            filter_config=FilterConfig(),
            source=DataSourceOption.BOTH,
        )

        assert info_schema_called is True
        assert audit_log_called is True

    def test_partial_success_when_one_source_fails(self) -> None:
        """Should return results from successful source when other fails."""
        from bq_table_reference.application.table_access_counter import (
            DataSourceOption,
            TableAccessCounter,
        )
        from bq_table_reference.domain.exceptions import PermissionDeniedError
        from bq_table_reference.domain.protocols import ProgressCallback

        class MockInfoSchemaAdapter:
            def fetch_table_access(
                self,
                project_id: str,
                filter_config: FilterConfig,
                progress_callback: ProgressCallback | None = None,
            ) -> list[TableAccessCount]:
                return [
                    TableAccessCount(
                        project_id=project_id,
                        dataset_id="ds",
                        table_id="tbl",
                        access_count=10,
                        source=DataSource.INFORMATION_SCHEMA,
                    )
                ]

        class FailingAuditLogAdapter:
            def fetch_table_access(
                self,
                project_id: str,
                filter_config: FilterConfig,
                progress_callback: ProgressCallback | None = None,
            ) -> list[TableAccessCount]:
                raise PermissionDeniedError("No access to audit logs")

        counter = TableAccessCounter(
            info_schema_adapter=MockInfoSchemaAdapter(),
            audit_log_adapter=FailingAuditLogAdapter(),
        )

        result = counter.count_access(
            project_id="test-project",
            filter_config=FilterConfig(),
            source=DataSourceOption.BOTH,
        )

        # Should have results from info_schema
        assert len(result.info_schema_results) == 1
        # Audit log results should be empty
        assert len(result.audit_log_results) == 0
        # Should have a warning about the failure
        assert len(result.warnings) > 0

    def test_returns_table_access_result(self) -> None:
        """count_access should return a TableAccessResult."""
        from bq_table_reference.application.table_access_counter import (
            DataSourceOption,
            TableAccessCounter,
        )
        from bq_table_reference.domain.protocols import ProgressCallback

        class MockInfoSchemaAdapter:
            def fetch_table_access(
                self,
                project_id: str,
                filter_config: FilterConfig,
                progress_callback: ProgressCallback | None = None,
            ) -> list[TableAccessCount]:
                return []

        class MockAuditLogAdapter:
            def fetch_table_access(
                self,
                project_id: str,
                filter_config: FilterConfig,
                progress_callback: ProgressCallback | None = None,
            ) -> list[TableAccessCount]:
                return []

        counter = TableAccessCounter(
            info_schema_adapter=MockInfoSchemaAdapter(),
            audit_log_adapter=MockAuditLogAdapter(),
        )

        result = counter.count_access(
            project_id="test-project",
            filter_config=FilterConfig(),
            source=DataSourceOption.BOTH,
        )

        assert isinstance(result, TableAccessResult)
        assert result.project_id == "test-project"


class TestApplyFilters:
    """Tests for filter application logic."""

    def test_min_count_filters_results_below_threshold(self) -> None:
        """Should filter out results below min_access_count threshold."""
        from bq_table_reference.application.table_access_counter import apply_filters

        results = [
            TableAccessCount(
                project_id="proj",
                dataset_id="ds",
                table_id="tbl1",
                access_count=3,
                source=DataSource.INFORMATION_SCHEMA,
            ),
            TableAccessCount(
                project_id="proj",
                dataset_id="ds",
                table_id="tbl2",
                access_count=10,
                source=DataSource.INFORMATION_SCHEMA,
            ),
            TableAccessCount(
                project_id="proj",
                dataset_id="ds",
                table_id="tbl3",
                access_count=5,
                source=DataSource.INFORMATION_SCHEMA,
            ),
        ]

        filter_config = FilterConfig(min_access_count=5)
        filtered = apply_filters(results, filter_config)

        assert len(filtered) == 2
        # Only results with access_count >= 5
        assert all(r.access_count >= 5 for r in filtered)

    def test_filter_config_passed_to_adapter(self) -> None:
        """FilterConfig should be passed correctly to adapter."""
        from bq_table_reference.application.table_access_counter import (
            DataSourceOption,
            TableAccessCounter,
        )
        from bq_table_reference.domain.protocols import ProgressCallback

        received_filter_config: FilterConfig | None = None

        class MockInfoSchemaAdapter:
            def fetch_table_access(
                self,
                project_id: str,
                filter_config: FilterConfig,
                progress_callback: ProgressCallback | None = None,
            ) -> list[TableAccessCount]:
                nonlocal received_filter_config
                received_filter_config = filter_config
                return []

        counter = TableAccessCounter(
            info_schema_adapter=MockInfoSchemaAdapter(),
            audit_log_adapter=None,
        )

        original_config = FilterConfig(days=60, dataset_filter="my_dataset")

        counter.count_access(
            project_id="test-project",
            filter_config=original_config,
            source=DataSourceOption.INFO_SCHEMA,
        )

        assert received_filter_config is not None
        assert received_filter_config.days == 60
        assert received_filter_config.dataset_filter == "my_dataset"

    def test_period_exceeds_180_days_adds_warning(self) -> None:
        """Should add warning when period exceeds 180 days."""
        from bq_table_reference.application.table_access_counter import (
            DataSourceOption,
            TableAccessCounter,
        )
        from bq_table_reference.domain.protocols import ProgressCallback

        class MockInfoSchemaAdapter:
            def fetch_table_access(
                self,
                project_id: str,
                filter_config: FilterConfig,
                progress_callback: ProgressCallback | None = None,
            ) -> list[TableAccessCount]:
                return []

        counter = TableAccessCounter(
            info_schema_adapter=MockInfoSchemaAdapter(),
            audit_log_adapter=None,
        )

        # 200 days exceeds 180 day retention period
        filter_config = FilterConfig(days=200)

        result = counter.count_access(
            project_id="test-project",
            filter_config=filter_config,
            source=DataSourceOption.INFO_SCHEMA,
        )

        # Should have a warning about period exceeding retention
        assert len(result.warnings) > 0
        assert any("180" in w for w in result.warnings)

    def test_apply_filters_with_zero_min_count_includes_all(self) -> None:
        """Should include all results when min_access_count is 0."""
        from bq_table_reference.application.table_access_counter import apply_filters

        results = [
            TableAccessCount(
                project_id="proj",
                dataset_id="ds",
                table_id="tbl1",
                access_count=0,
                source=DataSource.INFORMATION_SCHEMA,
            ),
            TableAccessCount(
                project_id="proj",
                dataset_id="ds",
                table_id="tbl2",
                access_count=10,
                source=DataSource.INFORMATION_SCHEMA,
            ),
        ]

        filter_config = FilterConfig(min_access_count=0)
        filtered = apply_filters(results, filter_config)

        assert len(filtered) == 2
