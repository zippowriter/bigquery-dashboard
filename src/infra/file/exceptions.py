"""ファイル出力インフラストラクチャ層の例外定義."""


class FileWriterError(Exception):
    """ファイル出力に失敗した場合の例外."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        """初期化.

        Args:
            message: エラーメッセージ
            cause: 原因となった例外
        """
        super().__init__(message)
        self.cause = cause
