"""BigQueryTableRepositoryのテスト。"""

from unittest.mock import MagicMock, patch

import pytest
from google.api_core.exceptions import GoogleAPIError

from src.shared.domain.models import TableInfo, TableUsage
from src.shared.infra.bigquery import BigQueryTableRepository


@pytest.fixture(autouse=True)
def reset_bigquery_client():  # type: ignore[misc]
    """各テスト前後でBigQueryクライアントをリセットする。"""
    BigQueryTableRepository._client = None
    BigQueryTableRepository._project_id = None
    yield
    BigQueryTableRepository._client = None
    BigQueryTableRepository._project_id = None


class TestFetchTables:
    """fetch_tablesメソッドのテスト。"""

    def test_returns_list_of_table_info(self) -> None:
        """テーブル情報のリストを返却することを検証する。"""
        repository = BigQueryTableRepository()

        # BigQueryクライアントをモック
        mock_client = MagicMock()

        # データセットのモック
        mock_dataset1 = MagicMock()
        mock_dataset1.dataset_id = "dataset1"

        mock_dataset2 = MagicMock()
        mock_dataset2.dataset_id = "dataset2"

        # テーブルのモック
        mock_table1 = MagicMock()
        mock_table1.dataset_id = "dataset1"
        mock_table1.table_id = "table1"

        mock_table2 = MagicMock()
        mock_table2.dataset_id = "dataset1"
        mock_table2.table_id = "table2"

        mock_table3 = MagicMock()
        mock_table3.dataset_id = "dataset2"
        mock_table3.table_id = "table3"

        # list_datasetsのモック
        mock_client.list_datasets.return_value = [mock_dataset1, mock_dataset2]

        # list_tablesのモック（データセットごとに異なるテーブルを返す）
        def mock_list_tables(dataset_id: str) -> list[MagicMock]:
            if dataset_id == "dataset1":
                return [mock_table1, mock_table2]
            elif dataset_id == "dataset2":
                return [mock_table3]
            return []

        mock_client.list_tables.side_effect = mock_list_tables

        with patch(
            "src.shared.infra.bigquery.bigquery.Client", return_value=mock_client
        ):
            tables = repository.fetch_tables("test-project")

        assert len(tables) == 3
        assert all(isinstance(t, TableInfo) for t in tables)
        assert tables[0].dataset_id == "dataset1"
        assert tables[0].table_id == "table1"

    def test_returns_empty_list_when_no_datasets(self) -> None:
        """データセットが存在しない場合、空リストを返却することを検証する。"""
        repository = BigQueryTableRepository()

        mock_client = MagicMock()
        mock_client.list_datasets.return_value = []

        with patch(
            "src.shared.infra.bigquery.bigquery.Client", return_value=mock_client
        ):
            tables = repository.fetch_tables("test-project")

        assert tables == []

    def test_raises_error_when_api_fails(self) -> None:
        """BigQuery API呼び出しが失敗した場合、例外がスローされることを検証する。"""
        repository = BigQueryTableRepository()

        mock_client = MagicMock()
        mock_client.list_datasets.side_effect = GoogleAPIError("API Error")

        with patch(
            "src.shared.infra.bigquery.bigquery.Client", return_value=mock_client
        ):
            with pytest.raises(GoogleAPIError):
                repository.fetch_tables("test-project")

    def test_raises_value_error_for_empty_project_id(self) -> None:
        """空のproject_idを渡した場合、ValueErrorがスローされることを検証する。"""
        repository = BigQueryTableRepository()

        with pytest.raises(ValueError, match="project_id"):
            repository.fetch_tables("")


class TestFetchUsageStats:
    """fetch_usage_statsメソッドのテスト。"""

    def test_returns_list_of_table_usage(self) -> None:
        """利用統計のリストを返却することを検証する。"""
        repository = BigQueryTableRepository()

        mock_client = MagicMock()

        # クエリ結果のモック
        mock_row1 = MagicMock()
        mock_row1.dataset_id = "dataset1"
        mock_row1.table_id = "table1"
        mock_row1.reference_count = 10
        mock_row1.unique_users = 3

        mock_row2 = MagicMock()
        mock_row2.dataset_id = "dataset2"
        mock_row2.table_id = "table2"
        mock_row2.reference_count = 5
        mock_row2.unique_users = 2

        mock_query_job = MagicMock()
        mock_query_job.result.return_value = [mock_row1, mock_row2]
        mock_client.query.return_value = mock_query_job

        with patch(
            "src.shared.infra.bigquery.bigquery.Client", return_value=mock_client
        ):
            usage_stats = repository.fetch_usage_stats("test-project", "region-us")

        assert len(usage_stats) == 2
        assert all(isinstance(u, TableUsage) for u in usage_stats)
        assert usage_stats[0].dataset_id == "dataset1"
        assert usage_stats[0].reference_count == 10
        assert usage_stats[1].unique_users == 2

    def test_returns_empty_list_when_no_results(self) -> None:
        """クエリ結果が空の場合、空リストを返却することを検証する。"""
        repository = BigQueryTableRepository()

        mock_client = MagicMock()
        mock_query_job = MagicMock()
        mock_query_job.result.return_value = []
        mock_client.query.return_value = mock_query_job

        with patch(
            "src.shared.infra.bigquery.bigquery.Client", return_value=mock_client
        ):
            usage_stats = repository.fetch_usage_stats("test-project", "region-us")

        assert usage_stats == []

    def test_raises_value_error_for_empty_project_id(self) -> None:
        """空のproject_idを渡した場合、ValueErrorがスローされることを検証する。"""
        repository = BigQueryTableRepository()

        with pytest.raises(ValueError, match="project_id"):
            repository.fetch_usage_stats("", "region-us")

    def test_uses_region_parameter_in_query(self) -> None:
        """リージョンパラメータがクエリに使用されることを検証する。"""
        repository = BigQueryTableRepository()

        mock_client = MagicMock()
        mock_query_job = MagicMock()
        mock_query_job.result.return_value = []
        mock_client.query.return_value = mock_query_job

        with patch(
            "src.shared.infra.bigquery.bigquery.Client", return_value=mock_client
        ):
            repository.fetch_usage_stats("test-project", region="region-asia-northeast1")

        # queryが呼ばれ、regionが含まれていることを確認
        mock_client.query.assert_called_once()
        query_arg = mock_client.query.call_args[0][0]
        assert "region-asia-northeast1" in query_arg


class TestFetchAll:
    """fetch_allメソッドのテスト。"""

    def test_returns_tuple_of_tables_and_usage(self) -> None:
        """テーブル一覧と利用統計のタプルを返却することを検証する。"""
        repository = BigQueryTableRepository()

        mock_client = MagicMock()

        # データセットとテーブルのモック
        mock_dataset = MagicMock()
        mock_dataset.dataset_id = "dataset1"
        mock_table = MagicMock()
        mock_table.dataset_id = "dataset1"
        mock_table.table_id = "table1"

        mock_client.list_datasets.return_value = [mock_dataset]
        mock_client.list_tables.return_value = [mock_table]

        # クエリ結果のモック
        mock_row = MagicMock()
        mock_row.dataset_id = "dataset1"
        mock_row.table_id = "table1"
        mock_row.reference_count = 10
        mock_row.unique_users = 3

        mock_query_job = MagicMock()
        mock_query_job.result.return_value = [mock_row]
        mock_client.query.return_value = mock_query_job

        with patch(
            "src.shared.infra.bigquery.bigquery.Client", return_value=mock_client
        ):
            tables, usage_stats = repository.fetch_all("test-project", "region-us")

        assert len(tables) == 1
        assert isinstance(tables[0], TableInfo)
        assert tables[0].dataset_id == "dataset1"

        assert len(usage_stats) == 1
        assert isinstance(usage_stats[0], TableUsage)
        assert usage_stats[0].reference_count == 10


class TestClientSingleton:
    """クライアントシングルトンのテスト。"""

    def test_reuses_client_for_same_project(self) -> None:
        """同じプロジェクトIDでクライアントが再利用されることを検証する。"""
        repository = BigQueryTableRepository()

        mock_client = MagicMock()
        mock_client.list_datasets.return_value = []

        with patch(
            "src.shared.infra.bigquery.bigquery.Client", return_value=mock_client
        ) as mock_constructor:
            repository.fetch_tables("test-project")
            repository.fetch_tables("test-project")

            # クライアントは1回だけ作成される
            assert mock_constructor.call_count == 1
