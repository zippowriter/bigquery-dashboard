"""BigQuery クライアントアダプター。

BigQuery Python SDK をラップし、ドメインオブジェクトへの変換と
エラーハンドリングを提供する。
"""

from collections.abc import Iterable, Iterator
from types import TracebackType
from typing import cast

from google.api_core import exceptions as api_exceptions
from google.auth import exceptions as auth_exceptions
from google.cloud import bigquery
from google.cloud.bigquery.dataset import DatasetListItem
from google.cloud.bigquery.table import TableListItem
from requests.exceptions import ConnectionError as RequestsConnectionError

from bq_table_reference.domain.exceptions import (
    AuthenticationError,
    DatasetNotFoundError,
    NetworkError,
    PermissionDeniedError,
)
from bq_table_reference.domain.models import DatasetInfo, TableInfo


class BQClientAdapter:
    """BigQuery API との通信を抽象化するアダプタークラス。

    BigQuery Client のライフサイクル管理、SDK オブジェクトから
    ドメインオブジェクトへの変換、エラーハンドリングを担当する。

    Examples:
        >>> with BQClientAdapter(project="my-project") as adapter:
        ...     for dataset in adapter.list_datasets("my-project"):
        ...         print(dataset.full_path)
    """

    def __init__(self, project: str | None = None) -> None:
        """BigQuery クライアントでアダプターを初期化する。

        Args:
            project: GCP プロジェクト ID。None の場合は認証情報のデフォルトを使用。

        Raises:
            AuthenticationError: 有効な認証情報が見つからない場合。
        """
        try:
            self._client = bigquery.Client(project=project)
        except auth_exceptions.DefaultCredentialsError as e:
            raise AuthenticationError(
                "認証に失敗しました。'gcloud auth application-default login' を実行して "
                "認証情報を設定してください。"
            ) from e
        except auth_exceptions.RefreshError as e:
            raise AuthenticationError(
                "認証に失敗しました。認証情報のリフレッシュに失敗しました。"
                "'gcloud auth application-default login' を再実行してください。"
            ) from e

    def close(self) -> None:
        """BigQuery クライアントをクローズする。"""
        self._client.close()

    def __enter__(self) -> "BQClientAdapter":
        """コンテキストマネージャーのエントリー。

        Returns:
            自身のインスタンス。
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """コンテキストマネージャーのイグジット。

        Args:
            exc_type: 例外の型（発生した場合）。
            exc_val: 例外の値（発生した場合）。
            exc_tb: トレースバック（発生した場合）。
        """
        self.close()

    def list_datasets(self, project: str) -> Iterator[DatasetInfo]:
        """指定プロジェクト内の全データセットを一覧取得する。

        Args:
            project: GCP プロジェクト ID。

        Yields:
            DatasetInfo: データセットのメタデータ。

        Raises:
            PermissionDeniedError: bigquery.datasets.list 権限がない場合。
            NetworkError: ネットワーク問題が発生した場合。
        """
        try:
            dataset_list = cast(
                Iterable[DatasetListItem],
                self._client.list_datasets(project=project),
            )
            for dataset_list_item in dataset_list:
                # 詳細情報を取得するために get_dataset を呼び出す
                dataset: bigquery.Dataset = self._client.get_dataset(
                    dataset_list_item.reference
                )
                yield DatasetInfo(
                    dataset_id=dataset.dataset_id,
                    project=dataset.project,
                    full_path=f"{dataset.project}.{dataset.dataset_id}",
                    created=dataset.created,
                    modified=dataset.modified,
                    location=dataset.location,
                )
        except api_exceptions.Forbidden as e:
            raise PermissionDeniedError() from e
        except api_exceptions.ServiceUnavailable as e:
            raise NetworkError() from e
        except RequestsConnectionError as e:
            raise NetworkError() from e

    def list_tables(self, dataset_id: str, project: str) -> Iterator[TableInfo]:
        """指定データセット内の全テーブルを一覧取得する。

        Args:
            dataset_id: BigQuery データセット ID。
            project: GCP プロジェクト ID。

        Yields:
            TableInfo: テーブルのメタデータ。

        Raises:
            DatasetNotFoundError: データセットが存在しない場合。
            PermissionDeniedError: bigquery.tables.list 権限がない場合。
            NetworkError: ネットワーク問題が発生した場合。
        """
        try:
            dataset_ref = bigquery.DatasetReference(
                project=project, dataset_id=dataset_id
            )
            table_list = cast(
                Iterable[TableListItem],
                self._client.list_tables(dataset_ref),
            )
            for table_list_item in table_list:
                yield TableInfo(
                    table_id=table_list_item.table_id,
                    dataset_id=table_list_item.dataset_id,
                    project=table_list_item.project,
                    full_path=f"{table_list_item.project}.{table_list_item.dataset_id}.{table_list_item.table_id}",
                    table_type=table_list_item.table_type,
                )
        except api_exceptions.NotFound as e:
            raise DatasetNotFoundError(
                f"データセット '{dataset_id}' が見つかりません。"
            ) from e
        except api_exceptions.Forbidden as e:
            raise PermissionDeniedError() from e
        except api_exceptions.ServiceUnavailable as e:
            raise NetworkError() from e
        except RequestsConnectionError as e:
            raise NetworkError() from e
