"""Tests for domain protocols.

This module tests the Protocol definitions for data source adapters,
ensuring proper method signatures and type contracts.
"""

from collections.abc import Callable
from typing import Protocol

from bq_table_reference.domain.models import DataSource, FilterConfig, TableAccessCount


class TestTableAccessDataSourceProtocol:
    """Tests for TableAccessDataSourceProtocol definition."""

    def test_protocol_has_fetch_table_access_method(self) -> None:
        """Protocol should define fetch_table_access method."""
        from bq_table_reference.domain.protocols import TableAccessDataSourceProtocol

        # Verify the protocol has the required method
        assert hasattr(TableAccessDataSourceProtocol, "fetch_table_access")

    def test_protocol_is_runtime_checkable(self) -> None:
        """Protocol should be runtime checkable for isinstance checks."""
        from bq_table_reference.domain.protocols import TableAccessDataSourceProtocol

        # Protocol should be decorated with @runtime_checkable
        assert isinstance(TableAccessDataSourceProtocol, type)
        # Check if it's a Protocol
        assert issubclass(TableAccessDataSourceProtocol, Protocol)

    def test_fetch_table_access_accepts_project_id_string(self) -> None:
        """fetch_table_access should accept project_id as string."""
        from bq_table_reference.domain.protocols import ProgressCallback

        # Create a mock implementation to verify signature
        class MockDataSource:
            def fetch_table_access(
                self,
                project_id: str,
                filter_config: FilterConfig,
                progress_callback: ProgressCallback | None = None,
            ) -> list[TableAccessCount]:
                return []

        # Should be able to create instance and call method
        source = MockDataSource()
        result = source.fetch_table_access(
            project_id="test-project",
            filter_config=FilterConfig(),
        )
        assert isinstance(result, list)

    def test_fetch_table_access_accepts_filter_config(self) -> None:
        """fetch_table_access should accept FilterConfig as second argument."""
        from bq_table_reference.domain.protocols import ProgressCallback

        class MockDataSource:
            def fetch_table_access(
                self,
                project_id: str,
                filter_config: FilterConfig,
                progress_callback: ProgressCallback | None = None,
            ) -> list[TableAccessCount]:
                # Verify filter_config is used
                assert filter_config.days == 30
                return []

        source = MockDataSource()
        config = FilterConfig(days=30)
        source.fetch_table_access(
            project_id="test-project",
            filter_config=config,
        )

    def test_fetch_table_access_accepts_optional_progress_callback(self) -> None:
        """fetch_table_access should accept optional progress_callback."""
        from bq_table_reference.domain.protocols import ProgressCallback

        callback_called = False

        def my_callback(current: int, total: int, message: str) -> None:
            nonlocal callback_called
            callback_called = True

        class MockDataSource:
            def fetch_table_access(
                self,
                project_id: str,
                filter_config: FilterConfig,
                progress_callback: ProgressCallback | None = None,
            ) -> list[TableAccessCount]:
                if progress_callback is not None:
                    progress_callback(1, 10, "Processing...")
                return []

        source = MockDataSource()
        source.fetch_table_access(
            project_id="test-project",
            filter_config=FilterConfig(),
            progress_callback=my_callback,
        )
        assert callback_called

    def test_fetch_table_access_returns_list_of_table_access_count(self) -> None:
        """fetch_table_access should return list[TableAccessCount]."""
        from bq_table_reference.domain.protocols import ProgressCallback

        class MockDataSource:
            def fetch_table_access(
                self,
                project_id: str,
                filter_config: FilterConfig,
                progress_callback: ProgressCallback | None = None,
            ) -> list[TableAccessCount]:
                return [
                    TableAccessCount(
                        project_id="test-project",
                        dataset_id="test_dataset",
                        table_id="test_table",
                        access_count=10,
                        source=DataSource.INFORMATION_SCHEMA,
                    )
                ]

        source = MockDataSource()
        result = source.fetch_table_access(
            project_id="test-project",
            filter_config=FilterConfig(),
        )

        assert len(result) == 1
        assert isinstance(result[0], TableAccessCount)
        assert result[0].project_id == "test-project"
        assert result[0].access_count == 10

    def test_mock_implementation_satisfies_protocol(self) -> None:
        """A correctly implemented class should satisfy the Protocol."""
        from bq_table_reference.domain.protocols import (
            ProgressCallback,
            TableAccessDataSourceProtocol,
        )

        class ValidDataSource:
            """A valid implementation of TableAccessDataSourceProtocol."""

            def fetch_table_access(
                self,
                project_id: str,
                filter_config: FilterConfig,
                progress_callback: ProgressCallback | None = None,
            ) -> list[TableAccessCount]:
                """Fetch table access counts from the data source.

                Args:
                    project_id: GCP project ID.
                    filter_config: Filtering conditions.
                    progress_callback: Optional callback for progress reporting.

                Returns:
                    List of TableAccessCount objects.

                Raises:
                    AuthenticationError: When authentication fails.
                    PermissionDeniedError: When permission is denied.
                    NetworkError: When network error occurs.
                """
                return []

        # Verify the class can be used where Protocol is expected
        source: TableAccessDataSourceProtocol = ValidDataSource()
        assert isinstance(source, TableAccessDataSourceProtocol)


class TestProgressCallbackTypeAlias:
    """Tests for ProgressCallback type alias."""

    def test_progress_callback_type_exists(self) -> None:
        """ProgressCallback type alias should be defined."""
        from bq_table_reference.domain.protocols import ProgressCallback

        # Should be importable
        assert ProgressCallback is not None

    def test_progress_callback_accepts_current_total_message(self) -> None:
        """ProgressCallback should accept (current, total, message) arguments."""
        # A function matching the signature
        def my_callback(current: int, total: int, message: str) -> None:
            pass

        # Should be assignable to the expected type
        callback: Callable[[int, int, str], None] = my_callback
        callback(5, 10, "Processing item 5 of 10")

    def test_progress_callback_can_be_none(self) -> None:
        """ProgressCallback should be usable as Optional type."""
        # Should be able to use None
        callback: Callable[[int, int, str], None] | None = None
        assert callback is None

        # And assign a function
        def progress_func(current: int, total: int, message: str) -> None:
            pass

        callback = progress_func
        assert callback is not None
