"""Lineage APIクライアント管理."""

from collections.abc import Generator
from contextlib import contextmanager

from google.api_core.exceptions import GoogleAPIError
from google.cloud.datacatalog_lineage_v1 import LineageClient

from infra.lineage.exceptions import LineageConnectionError


class LineageClientFactory:
    """Lineage APIクライアントのファクトリクラス."""

    def __init__(self, location: str = "us") -> None:
        """初期化.

        Args:
            location: Lineage APIのロケーション（デフォルト: us）
        """
        self._location = location

    @property
    def location(self) -> str:
        """ロケーションを取得する."""
        return self._location

    @contextmanager
    def get_client(self) -> Generator[LineageClient, None, None]:
        """Lineage APIクライアントをコンテキストマネージャとして取得する.

        ADC (Application Default Credentials) を使用して認証する。

        Yields:
            LineageClient インスタンス

        Raises:
            LineageConnectionError: クライアント作成に失敗した場合
        """
        client: LineageClient | None = None
        try:
            client = LineageClient()
            yield client
        except GoogleAPIError as e:
            raise LineageConnectionError(
                f"Lineage APIクライアントの作成に失敗しました: {e}",
                cause=e,
            ) from e
        finally:
            if client is not None:
                client.transport.close()
