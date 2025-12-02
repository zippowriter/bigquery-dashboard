"""Tests for BigQuery client module."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from google.api_core.exceptions import GoogleAPIError


class TestFetchTableList:
    """Tests for fetch_table_list function."""

    def test_returns_dataframe_with_correct_columns(self) -> None:
        """fetch_table_listがdataset_idとtable_idカラムを持つDataFrameを返却することを検証する。"""
        from src.dashboard.bigquery_client import fetch_table_list

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
            "src.dashboard.bigquery_client.bigquery.Client", return_value=mock_client
        ):
            df = fetch_table_list("test-project")

        # DataFrameの検証
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["dataset_id", "table_id"]
        assert len(df) == 3
        assert df.iloc[0]["dataset_id"] == "dataset1"
        assert df.iloc[0]["table_id"] == "table1"

    def test_returns_empty_dataframe_when_no_datasets(self) -> None:
        """データセットが存在しない場合、空のDataFrameを返却することを検証する。"""
        from src.dashboard.bigquery_client import fetch_table_list

        mock_client = MagicMock()
        mock_client.list_datasets.return_value = []

        with patch(
            "src.dashboard.bigquery_client.bigquery.Client", return_value=mock_client
        ):
            df = fetch_table_list("test-project")

        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["dataset_id", "table_id"]
        assert len(df) == 0

    def test_raises_error_when_api_fails(self) -> None:
        """BigQuery API呼び出しが失敗した場合、例外がスローされることを検証する。"""
        from src.dashboard.bigquery_client import fetch_table_list

        mock_client = MagicMock()
        mock_client.list_datasets.side_effect = GoogleAPIError("API Error")

        with patch(
            "src.dashboard.bigquery_client.bigquery.Client", return_value=mock_client
        ):
            with pytest.raises(GoogleAPIError):
                fetch_table_list("test-project")

    def test_raises_value_error_for_empty_project_id(self) -> None:
        """空のproject_idを渡した場合、ValueErrorがスローされることを検証する。"""
        from src.dashboard.bigquery_client import fetch_table_list

        with pytest.raises(ValueError, match="project_id"):
            fetch_table_list("")


class TestFetchTableUsageStats:
    """fetch_table_usage_stats関数のテスト。"""

    def test_returns_dataframe_with_correct_columns(self) -> None:
        """利用統計DataFrameが4カラム（dataset_id, table_id, reference_count, unique_users）を持つことを検証する。"""
        from src.dashboard.bigquery_client import fetch_table_usage_stats

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
            "src.dashboard.bigquery_client.bigquery.Client", return_value=mock_client
        ):
            df = fetch_table_usage_stats("test-project")

        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == [
            "dataset_id",
            "table_id",
            "reference_count",
            "unique_users",
        ]
        assert len(df) == 2
        assert df.iloc[0]["dataset_id"] == "dataset1"
        assert df.iloc[0]["reference_count"] == 10
        assert df.iloc[1]["unique_users"] == 2

    def test_returns_empty_dataframe_with_correct_schema(self) -> None:
        """空結果時も4カラム構成のDataFrameを返却することを検証する。"""
        from src.dashboard.bigquery_client import fetch_table_usage_stats

        mock_client = MagicMock()
        mock_query_job = MagicMock()
        mock_query_job.result.return_value = []
        mock_client.query.return_value = mock_query_job

        with patch(
            "src.dashboard.bigquery_client.bigquery.Client", return_value=mock_client
        ):
            df = fetch_table_usage_stats("test-project")

        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == [
            "dataset_id",
            "table_id",
            "reference_count",
            "unique_users",
        ]
        assert len(df) == 0

    def test_raises_value_error_for_empty_project_id(self) -> None:
        """空のproject_idを渡した場合、ValueErrorがスローされることを検証する。"""
        from src.dashboard.bigquery_client import fetch_table_usage_stats

        with pytest.raises(ValueError, match="project_id"):
            fetch_table_usage_stats("")

    def test_uses_region_parameter_in_query(self) -> None:
        """リージョンパラメータがクエリに使用されることを検証する。"""
        from src.dashboard.bigquery_client import fetch_table_usage_stats

        mock_client = MagicMock()
        mock_query_job = MagicMock()
        mock_query_job.result.return_value = []
        mock_client.query.return_value = mock_query_job

        with patch(
            "src.dashboard.bigquery_client.bigquery.Client", return_value=mock_client
        ):
            fetch_table_usage_stats("test-project", region="region-asia-northeast1")

        # queryが呼ばれ、regionが含まれていることを確認
        mock_client.query.assert_called_once()
        query_arg = mock_client.query.call_args[0][0]
        assert "region-asia-northeast1" in query_arg
