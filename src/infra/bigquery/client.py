"""BigQueryクライアント管理."""

from collections.abc import Generator
from contextlib import contextmanager

from google.api_core.exceptions import GoogleAPIError
from google.cloud import bigquery
from google.cloud.bigquery import Client

from infra.bigquery.exceptions import BigQueryConnectionError


class BigQueryClientFactory:
    """BigQueryクライアントのファクトリクラス."""

    def __init__(self, project_id: str | None = None) -> None:
        """初期化.

        Args:
            project_id: デフォルトのプロジェクトID（Noneの場合はADCから推論）
        """
        self._project_id = project_id

    @contextmanager
    def get_client(self) -> Generator[Client, None, None]:
        """BigQueryクライアントをコンテキストマネージャとして取得する.

        ADC (Application Default Credentials) を使用して認証する。

        Yields:
            BigQuery Client インスタンス

        Raises:
            BigQueryConnectionError: クライアント作成に失敗した場合
        """
        client: Client | None = None
        try:
            client = bigquery.Client(project=self._project_id)
            yield client
        except GoogleAPIError as e:
            raise BigQueryConnectionError(
                f"Failed to create BigQuery client: {e}",
                cause=e,
            ) from e
        finally:
            if client is not None:
                client.close()
