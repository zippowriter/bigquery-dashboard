"""BigQueryインフラストラクチャ層の例外定義."""

from typing import Any


class BigQueryInfraError(Exception):
    """BigQueryインフラストラクチャ層の基底例外."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class BigQueryConnectionError(BigQueryInfraError):
    """BigQueryへの接続に失敗した場合の例外."""

    pass


class BigQueryQueryError(BigQueryInfraError):
    """クエリ実行に失敗した場合の例外."""

    def __init__(
        self,
        message: str,
        query: str | None = None,
        params: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, cause)
        self.query = query
        self.params = params


class TableNotFoundError(BigQueryInfraError):
    """テーブルが見つからない場合の例外."""

    def __init__(self, project_id: str, dataset_id: str, table_id: str) -> None:
        super().__init__(f"Table not found: {project_id}.{dataset_id}.{table_id}")
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id


class TableRepositoryError(BigQueryInfraError):
    """TableRepository操作に失敗した場合の例外."""

    pass
