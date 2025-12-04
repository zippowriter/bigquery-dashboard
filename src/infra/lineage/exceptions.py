"""Lineageインフラストラクチャ層の例外定義."""


class LineageInfraError(Exception):
    """Lineageインフラストラクチャ層の基底例外."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class LineageConnectionError(LineageInfraError):
    """Lineage APIへの接続に失敗した場合の例外."""

    pass


class LineageApiError(LineageInfraError):
    """Lineage API呼び出しに失敗した場合の例外."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, cause)
        self.operation = operation


class LineageRepositoryError(LineageInfraError):
    """LineageRepository操作に失敗した場合の例外."""

    pass
