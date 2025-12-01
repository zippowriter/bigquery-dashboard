"""BQClientAdapter の単体テスト。

BigQuery クライアントアダプターの初期化、認証処理、
コンテキストマネージャー対応をテストする。
"""

from unittest.mock import MagicMock, patch

import pytest

from google.auth import exceptions as auth_exceptions

from bq_table_reference.domain.exceptions import AuthenticationError
from bq_table_reference.infrastructure.bq_client_adapter import BQClientAdapter


class TestBQClientAdapterInit:
    """BQClientAdapter の初期化に関するテスト。"""

    def test_init_with_default_credentials_success(self) -> None:
        """ADC が利用可能な場合、正常に初期化できることを検証する。"""
        mock_client = MagicMock()

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter()

            assert adapter._client is mock_client

    def test_init_with_project_id(self) -> None:
        """プロジェクト ID を指定して初期化できることを検証する。"""
        mock_client = MagicMock()

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ) as mock_client_class:
            adapter = BQClientAdapter(project="my-project")

            mock_client_class.assert_called_once_with(project="my-project")
            assert adapter._client is mock_client

    def test_init_without_project_uses_default(self) -> None:
        """プロジェクト ID 未指定の場合、認証情報のデフォルトを使用することを検証する。"""
        mock_client = MagicMock()

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ) as mock_client_class:
            adapter = BQClientAdapter()

            mock_client_class.assert_called_once_with(project=None)
            assert adapter._client is mock_client


class TestBQClientAdapterAuthenticationError:
    """BQClientAdapter の認証エラー処理に関するテスト。"""

    def test_init_raises_authentication_error_on_default_credentials_error(
        self,
    ) -> None:
        """ADC が見つからない場合、AuthenticationError を発生させることを検証する。"""
        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            side_effect=auth_exceptions.DefaultCredentialsError(
                "Could not automatically determine credentials."
            ),
        ):
            with pytest.raises(AuthenticationError) as exc_info:
                BQClientAdapter()

            assert "認証に失敗しました" in str(exc_info.value)
            assert "gcloud auth application-default login" in str(exc_info.value)

    def test_init_raises_authentication_error_on_refresh_error(self) -> None:
        """認証情報のリフレッシュに失敗した場合、AuthenticationError を発生させることを検証する。"""
        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            side_effect=auth_exceptions.RefreshError("Unable to refresh access token."),
        ):
            with pytest.raises(AuthenticationError) as exc_info:
                BQClientAdapter()

            assert "認証に失敗しました" in str(exc_info.value)


class TestBQClientAdapterContextManager:
    """BQClientAdapter のコンテキストマネージャーに関するテスト。"""

    def test_context_manager_enter_returns_self(self) -> None:
        """__enter__ が self を返すことを検証する。"""
        mock_client = MagicMock()

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter()
            result = adapter.__enter__()

            assert result is adapter

    def test_context_manager_exit_closes_client(self) -> None:
        """__exit__ でクライアントがクローズされることを検証する。"""
        mock_client = MagicMock()

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter()
            adapter.__exit__(None, None, None)

            mock_client.close.assert_called_once()

    def test_with_statement_usage(self) -> None:
        """with 文で正常に使用できることを検証する。"""
        mock_client = MagicMock()

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            with BQClientAdapter() as adapter:
                assert adapter._client is mock_client

            mock_client.close.assert_called_once()


class TestBQClientAdapterClose:
    """BQClientAdapter の close メソッドに関するテスト。"""

    def test_close_closes_client(self) -> None:
        """close() でクライアントがクローズされることを検証する。"""
        mock_client = MagicMock()

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter()
            adapter.close()

            mock_client.close.assert_called_once()

    def test_close_can_be_called_multiple_times(self) -> None:
        """close() を複数回呼び出しても問題ないことを検証する。"""
        mock_client = MagicMock()

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter()
            adapter.close()
            adapter.close()

            # 2回呼ばれることを許容（idempotent）
            assert mock_client.close.call_count == 2


class TestBQClientAdapterListDatasets:
    """BQClientAdapter の list_datasets メソッドに関するテスト。"""

    def test_list_datasets_returns_dataset_info_iterator(self) -> None:
        """list_datasets が DatasetInfo のイテレータを返すことを検証する。"""
        from datetime import datetime, timezone

        from bq_table_reference.domain.models import DatasetInfo

        mock_client = MagicMock()

        # BigQuery SDK のデータセットリストアイテムをモック
        mock_dataset_list_item = MagicMock()
        mock_dataset_list_item.dataset_id = "test_dataset"
        mock_dataset_list_item.project = "test-project"
        mock_dataset_list_item.full_dataset_id = "test-project:test_dataset"

        # get_dataset で返される詳細情報をモック
        mock_dataset = MagicMock()
        mock_dataset.dataset_id = "test_dataset"
        mock_dataset.project = "test-project"
        mock_dataset.created = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        mock_dataset.modified = datetime(2024, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
        mock_dataset.location = "US"

        mock_client.list_datasets.return_value = iter([mock_dataset_list_item])
        mock_client.get_dataset.return_value = mock_dataset

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter(project="test-project")
            datasets = list(adapter.list_datasets("test-project"))

            assert len(datasets) == 1
            assert isinstance(datasets[0], DatasetInfo)
            assert datasets[0].dataset_id == "test_dataset"
            assert datasets[0].project == "test-project"
            assert datasets[0].full_path == "test-project.test_dataset"
            assert datasets[0].created == datetime(
                2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            )
            assert datasets[0].modified == datetime(
                2024, 6, 1, 0, 0, 0, tzinfo=timezone.utc
            )
            assert datasets[0].location == "US"

    def test_list_datasets_handles_multiple_datasets(self) -> None:
        """複数のデータセットを正しく処理することを検証する。"""
        from datetime import datetime, timezone

        from bq_table_reference.domain.models import DatasetInfo

        mock_client = MagicMock()

        # 複数のデータセットをモック
        mock_items = []
        mock_datasets = []
        for i in range(3):
            mock_item = MagicMock()
            mock_item.dataset_id = f"dataset_{i}"
            mock_item.project = "test-project"
            mock_item.full_dataset_id = f"test-project:dataset_{i}"
            mock_items.append(mock_item)

            mock_ds = MagicMock()
            mock_ds.dataset_id = f"dataset_{i}"
            mock_ds.project = "test-project"
            mock_ds.created = datetime(2024, 1, i + 1, 0, 0, 0, tzinfo=timezone.utc)
            mock_ds.modified = datetime(2024, 6, i + 1, 0, 0, 0, tzinfo=timezone.utc)
            mock_ds.location = "US"
            mock_datasets.append(mock_ds)

        mock_client.list_datasets.return_value = iter(mock_items)
        mock_client.get_dataset.side_effect = mock_datasets

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter(project="test-project")
            datasets = list(adapter.list_datasets("test-project"))

            assert len(datasets) == 3
            for i, ds in enumerate(datasets):
                assert isinstance(ds, DatasetInfo)
                assert ds.dataset_id == f"dataset_{i}"

    def test_list_datasets_returns_empty_iterator_when_no_datasets(self) -> None:
        """データセットがない場合、空のイテレータを返すことを検証する。"""
        mock_client = MagicMock()
        mock_client.list_datasets.return_value = iter([])

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter(project="test-project")
            datasets = list(adapter.list_datasets("test-project"))

            assert datasets == []

    def test_list_datasets_handles_optional_fields_as_none(self) -> None:
        """オプショナルフィールドが None の場合も正しく処理することを検証する。"""
        from bq_table_reference.domain.models import DatasetInfo

        mock_client = MagicMock()

        mock_dataset_list_item = MagicMock()
        mock_dataset_list_item.dataset_id = "test_dataset"
        mock_dataset_list_item.project = "test-project"
        mock_dataset_list_item.full_dataset_id = "test-project:test_dataset"

        mock_dataset = MagicMock()
        mock_dataset.dataset_id = "test_dataset"
        mock_dataset.project = "test-project"
        mock_dataset.created = None
        mock_dataset.modified = None
        mock_dataset.location = None

        mock_client.list_datasets.return_value = iter([mock_dataset_list_item])
        mock_client.get_dataset.return_value = mock_dataset

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter(project="test-project")
            datasets = list(adapter.list_datasets("test-project"))

            assert len(datasets) == 1
            assert isinstance(datasets[0], DatasetInfo)
            assert datasets[0].created is None
            assert datasets[0].modified is None
            assert datasets[0].location is None


class TestBQClientAdapterListDatasetsErrors:
    """BQClientAdapter の list_datasets エラー処理に関するテスト。"""

    def test_list_datasets_raises_permission_denied_error(self) -> None:
        """権限エラー時に PermissionDeniedError を発生させることを検証する。"""
        from google.api_core import exceptions as api_exceptions

        from bq_table_reference.domain.exceptions import PermissionDeniedError

        mock_client = MagicMock()
        mock_client.list_datasets.side_effect = api_exceptions.Forbidden(
            "Access Denied"
        )

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter(project="test-project")

            with pytest.raises(PermissionDeniedError) as exc_info:
                list(adapter.list_datasets("test-project"))

            assert "アクセス権限がありません" in str(exc_info.value)

    def test_list_datasets_raises_network_error_on_service_unavailable(self) -> None:
        """サービス利用不可時に NetworkError を発生させることを検証する。"""
        from google.api_core import exceptions as api_exceptions

        from bq_table_reference.domain.exceptions import NetworkError

        mock_client = MagicMock()
        mock_client.list_datasets.side_effect = api_exceptions.ServiceUnavailable(
            "Service Unavailable"
        )

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter(project="test-project")

            with pytest.raises(NetworkError) as exc_info:
                list(adapter.list_datasets("test-project"))

            assert "ネットワークエラー" in str(exc_info.value)

    def test_list_datasets_raises_network_error_on_connection_error(self) -> None:
        """接続エラー時に NetworkError を発生させることを検証する。"""
        from requests.exceptions import ConnectionError as RequestsConnectionError

        from bq_table_reference.domain.exceptions import NetworkError

        mock_client = MagicMock()
        mock_client.list_datasets.side_effect = RequestsConnectionError(
            "Connection failed"
        )

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter(project="test-project")

            with pytest.raises(NetworkError) as exc_info:
                list(adapter.list_datasets("test-project"))

            assert "ネットワークエラー" in str(exc_info.value)


class TestBQClientAdapterListTables:
    """BQClientAdapter の list_tables メソッドに関するテスト。"""

    def test_list_tables_returns_iterator_of_table_info(self) -> None:
        """list_tables が TableInfo のイテレータを返すことを検証する。"""
        mock_client = MagicMock()
        mock_table_1 = MagicMock()
        mock_table_1.table_id = "table_1"
        mock_table_1.dataset_id = "test_dataset"
        mock_table_1.project = "test-project"
        mock_table_1.table_type = "TABLE"

        mock_table_2 = MagicMock()
        mock_table_2.table_id = "table_2"
        mock_table_2.dataset_id = "test_dataset"
        mock_table_2.project = "test-project"
        mock_table_2.table_type = "VIEW"

        mock_client.list_tables.return_value = iter([mock_table_1, mock_table_2])

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter()
            tables = list(adapter.list_tables("test_dataset", "test-project"))

            assert len(tables) == 2
            from bq_table_reference.domain.models import TableInfo

            assert all(isinstance(t, TableInfo) for t in tables)

    def test_list_tables_converts_sdk_object_to_table_info(self) -> None:
        """SDK オブジェクトから TableInfo への変換が正しく行われることを検証する。"""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_table.table_id = "users"
        mock_table.dataset_id = "analytics"
        mock_table.project = "my-project"
        mock_table.table_type = "TABLE"

        mock_client.list_tables.return_value = iter([mock_table])

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter()
            tables = list(adapter.list_tables("analytics", "my-project"))

            assert len(tables) == 1
            table = tables[0]
            assert table.table_id == "users"
            assert table.dataset_id == "analytics"
            assert table.project == "my-project"
            assert table.full_path == "my-project.analytics.users"
            assert table.table_type == "TABLE"

    def test_list_tables_handles_various_table_types(self) -> None:
        """様々なテーブル種別を正しく変換できることを検証する。"""
        mock_client = MagicMock()

        table_types = ["TABLE", "VIEW", "MATERIALIZED_VIEW", "EXTERNAL"]
        mock_tables = []
        for i, table_type in enumerate(table_types):
            mock_table = MagicMock()
            mock_table.table_id = f"table_{i}"
            mock_table.dataset_id = "test_dataset"
            mock_table.project = "test-project"
            mock_table.table_type = table_type
            mock_tables.append(mock_table)

        mock_client.list_tables.return_value = iter(mock_tables)

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter()
            tables = list(adapter.list_tables("test_dataset", "test-project"))

            assert len(tables) == 4
            for i, table in enumerate(tables):
                assert table.table_type == table_types[i]

    def test_list_tables_handles_pagination(self) -> None:
        """ページネーションが自動的に処理されることを検証する。"""
        mock_client = MagicMock()

        # SDK は内部でページネーションを処理してイテレータを返す
        mock_tables = []
        for i in range(100):
            mock_table = MagicMock()
            mock_table.table_id = f"table_{i}"
            mock_table.dataset_id = "test_dataset"
            mock_table.project = "test-project"
            mock_table.table_type = "TABLE"
            mock_tables.append(mock_table)

        mock_client.list_tables.return_value = iter(mock_tables)

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter()
            tables = list(adapter.list_tables("test_dataset", "test-project"))

            assert len(tables) == 100

    def test_list_tables_calls_sdk_with_correct_dataset_reference(self) -> None:
        """SDK に正しいデータセット参照を渡すことを検証する。"""
        mock_client = MagicMock()
        mock_client.list_tables.return_value = iter([])

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter()
            list(adapter.list_tables("my_dataset", "my-project"))

            mock_client.list_tables.assert_called_once()
            # DatasetReference が正しく生成されていることを確認
            call_args = mock_client.list_tables.call_args
            dataset_ref = call_args[0][0]
            assert dataset_ref.dataset_id == "my_dataset"
            assert dataset_ref.project == "my-project"

    def test_list_tables_returns_empty_iterator_for_empty_dataset(self) -> None:
        """空のデータセットに対して空のイテレータを返すことを検証する。"""
        mock_client = MagicMock()
        mock_client.list_tables.return_value = iter([])

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter()
            tables = list(adapter.list_tables("empty_dataset", "test-project"))

            assert len(tables) == 0


class TestBQClientAdapterListTablesErrors:
    """BQClientAdapter の list_tables エラー処理に関するテスト。"""

    def test_list_tables_raises_dataset_not_found_error(self) -> None:
        """存在しないデータセットを指定した場合、DatasetNotFoundError を発生させることを検証する。"""
        from google.api_core import exceptions as api_exceptions

        from bq_table_reference.domain.exceptions import DatasetNotFoundError

        mock_client = MagicMock()
        mock_client.list_tables.side_effect = api_exceptions.NotFound(
            "Dataset not found: test-project:nonexistent_dataset"
        )

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter()

            with pytest.raises(DatasetNotFoundError) as exc_info:
                list(adapter.list_tables("nonexistent_dataset", "test-project"))

            assert "nonexistent_dataset" in str(exc_info.value)

    def test_list_tables_raises_permission_denied_error(self) -> None:
        """権限がない場合、PermissionDeniedError を発生させることを検証する。"""
        from google.api_core import exceptions as api_exceptions

        from bq_table_reference.domain.exceptions import PermissionDeniedError

        mock_client = MagicMock()
        mock_client.list_tables.side_effect = api_exceptions.Forbidden(
            "Access Denied: Table test-project:test_dataset: User does not have permission"
        )

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter()

            with pytest.raises(PermissionDeniedError) as exc_info:
                list(adapter.list_tables("test_dataset", "test-project"))

            assert "アクセス権限" in str(exc_info.value)

    def test_list_tables_raises_network_error_on_service_unavailable(self) -> None:
        """サービス利用不可の場合、NetworkError を発生させることを検証する。"""
        from google.api_core import exceptions as api_exceptions

        from bq_table_reference.domain.exceptions import NetworkError

        mock_client = MagicMock()
        mock_client.list_tables.side_effect = api_exceptions.ServiceUnavailable(
            "Service is temporarily unavailable"
        )

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter()

            with pytest.raises(NetworkError) as exc_info:
                list(adapter.list_tables("test_dataset", "test-project"))

            assert "ネットワークエラー" in str(exc_info.value)

    def test_list_tables_raises_network_error_on_connection_error(self) -> None:
        """接続エラーの場合、NetworkError を発生させることを検証する。"""
        from requests.exceptions import ConnectionError as RequestsConnectionError

        from bq_table_reference.domain.exceptions import NetworkError

        mock_client = MagicMock()
        mock_client.list_tables.side_effect = RequestsConnectionError(
            "Failed to establish a new connection"
        )

        with patch(
            "bq_table_reference.infrastructure.bq_client_adapter.bigquery.Client",
            return_value=mock_client,
        ):
            adapter = BQClientAdapter()

            with pytest.raises(NetworkError) as exc_info:
                list(adapter.list_tables("test_dataset", "test-project"))

            assert "ネットワークエラー" in str(exc_info.value)
