"""Protocol definitions for domain interfaces.

This module defines Protocol classes that establish contracts
for data source adapters and other interfaces used in the application.
"""

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from bq_table_reference.domain.models import FilterConfig, TableAccessCount


# Type alias for progress callback function.
# Callbacks receive (current, total, message) for progress reporting.
ProgressCallback = Callable[[int, int, str], None]


@runtime_checkable
class TableAccessDataSourceProtocol(Protocol):
    """Protocol for table access data source adapters.

    This protocol defines the contract that data source adapters
    (InfoSchemaAdapter, AuditLogAdapter) must implement to provide
    table access count data.

    Implementations should handle:
    - Connection to the underlying data source
    - Query execution and result parsing
    - Error handling and appropriate exception raising

    Example:
        >>> class MyAdapter:
        ...     def fetch_table_access(
        ...         self,
        ...         project_id: str,
        ...         filter_config: FilterConfig,
        ...         progress_callback: ProgressCallback | None = None,
        ...     ) -> list[TableAccessCount]:
        ...         # Implementation here
        ...         return []
    """

    def fetch_table_access(
        self,
        project_id: str,
        filter_config: FilterConfig,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> list[TableAccessCount]:
        """Fetch table access counts from the data source.

        Args:
            project_id: GCP project ID to query.
            filter_config: Filtering conditions for the query.
            progress_callback: Optional callback function for progress reporting.
                Called with (current, total, message) during long-running operations.

        Returns:
            List of TableAccessCount objects representing table access statistics.

        Raises:
            AuthenticationError: When authentication to the data source fails.
                User should run 'gcloud auth application-default login'.
            PermissionDeniedError: When the user lacks required permissions.
                For INFORMATION_SCHEMA: requires 'roles/bigquery.resourceViewer'.
                For Audit Logs: requires 'roles/logging.viewer'.
            NetworkError: When network connectivity issues occur.
                User should check connection and retry.
        """
        ...
