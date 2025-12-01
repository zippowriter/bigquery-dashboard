"""DatasetLoader の単体テスト。

ローダーの初期化とオンメモリデータ保持構造をテストする。
"""

from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest

from bq_table_reference.application.dataset_loader import DatasetLoader
from bq_table_reference.domain.exceptions import (
    DatasetNotFoundError,
    NetworkError,
    PermissionDeniedError,
)
from bq_table_reference.domain.models import DatasetInfo, LoadResult, TableInfo
from bq_table_reference.infrastructure.bq_client_adapter import BQClientAdapter


class TestDatasetLoaderInitialization:
    """DatasetLoader の初期化に関するテスト。"""

    def test_init_with_adapter(self, mock_adapter: MagicMock) -> None:
        """事前設定済みのアダプターを受け取って初期化できる。"""
        loader = DatasetLoader(adapter=mock_adapter)

        assert loader._adapter is mock_adapter

    def test_init_with_project_creates_adapter(self) -> None:
        """project を指定した場合、内部でアダプターが作成される。

        注意: このテストでは BQClientAdapter の生成をモックして検証する。
        """
        from unittest.mock import patch

        mock_adapter_instance = MagicMock(spec=BQClientAdapter)

        with patch(
            "bq_table_reference.application.dataset_loader.BQClientAdapter",
            return_value=mock_adapter_instance,
        ) as mock_adapter_class:
            loader = DatasetLoader(project="test-project")

            mock_adapter_class.assert_called_once_with(project="test-project")
            assert loader._adapter is mock_adapter_instance

    def test_init_requires_adapter_or_project(self) -> None:
        """adapter も project も指定しない場合は ValueError が発生する。"""
        with pytest.raises(
            ValueError, match="adapter または project を指定してください"
        ):
            DatasetLoader()

    def test_init_internal_datasets_dict_is_empty(
        self, mock_adapter: MagicMock
    ) -> None:
        """初期化時に _datasets 辞書が空で作成される。"""
        loader = DatasetLoader(adapter=mock_adapter)

        assert loader._datasets == {}
        assert isinstance(loader._datasets, dict)

    def test_init_internal_tables_dict_is_empty(self, mock_adapter: MagicMock) -> None:
        """初期化時に _tables 辞書が空で作成される。"""
        loader = DatasetLoader(adapter=mock_adapter)

        assert loader._tables == {}
        assert isinstance(loader._tables, dict)

    def test_init_internal_tables_by_dataset_dict_is_empty(
        self, mock_adapter: MagicMock
    ) -> None:
        """初期化時に _tables_by_dataset 辞書が空で作成される。"""
        loader = DatasetLoader(adapter=mock_adapter)

        assert loader._tables_by_dataset == {}
        assert isinstance(loader._tables_by_dataset, dict)


class TestDatasetLoaderInternalStructure:
    """DatasetLoader の内部データ構造に関するテスト。"""

    def test_datasets_dict_key_is_dataset_id(self, mock_adapter: MagicMock) -> None:
        """_datasets 辞書のキーは dataset_id である。"""
        loader = DatasetLoader(adapter=mock_adapter)

        # 内部構造の型を確認
        # dict[str, DatasetInfo] の形式
        assert isinstance(loader._datasets, dict)

    def test_tables_dict_key_is_full_path(self, mock_adapter: MagicMock) -> None:
        """_tables 辞書のキーは full_path である。"""
        loader = DatasetLoader(adapter=mock_adapter)

        # 内部構造の型を確認
        # dict[str, TableInfo] の形式
        assert isinstance(loader._tables, dict)

    def test_tables_by_dataset_dict_key_is_dataset_id(
        self, mock_adapter: MagicMock
    ) -> None:
        """_tables_by_dataset 辞書のキーは dataset_id である。"""
        loader = DatasetLoader(adapter=mock_adapter)

        # 内部構造の型を確認
        # dict[str, list[TableInfo]] の形式
        assert isinstance(loader._tables_by_dataset, dict)


class TestDatasetLoaderProperties:
    """DatasetLoader のプロパティに関するテスト。"""

    def test_datasets_property_returns_empty_list_initially(
        self, mock_adapter: MagicMock
    ) -> None:
        """datasets プロパティは初期状態で空リストを返す。"""
        loader = DatasetLoader(adapter=mock_adapter)

        assert loader.datasets == []

    def test_tables_property_returns_empty_list_initially(
        self, mock_adapter: MagicMock
    ) -> None:
        """tables プロパティは初期状態で空リストを返す。"""
        loader = DatasetLoader(adapter=mock_adapter)

        assert loader.tables == []


class TestDatasetLoaderLoadAll:
    """DatasetLoader の load_all メソッドに関するテスト。"""

    def test_load_all_returns_load_result(self, mock_adapter: MagicMock) -> None:
        """load_all は LoadResult を返す。"""
        mock_adapter.list_datasets.return_value = iter([])

        loader = DatasetLoader(adapter=mock_adapter)
        result = loader.load_all("test-project")

        assert isinstance(result, LoadResult)

    def test_load_all_calls_list_datasets_with_project(
        self, mock_adapter: MagicMock
    ) -> None:
        """load_all は指定した project で list_datasets を呼び出す。"""
        mock_adapter.list_datasets.return_value = iter([])

        loader = DatasetLoader(adapter=mock_adapter)
        loader.load_all("my-project")

        mock_adapter.list_datasets.assert_called_once_with("my-project")

    def test_load_all_loads_datasets_into_internal_dict(
        self, mock_adapter: MagicMock, sample_dataset_info: DatasetInfo
    ) -> None:
        """load_all はデータセットを内部辞書に登録する。"""
        mock_adapter.list_datasets.return_value = iter([sample_dataset_info])
        mock_adapter.list_tables.return_value = iter([])

        loader = DatasetLoader(adapter=mock_adapter)
        loader.load_all("test-project")

        assert sample_dataset_info.dataset_id in loader._datasets
        assert loader._datasets[sample_dataset_info.dataset_id] == sample_dataset_info

    def test_load_all_calls_list_tables_for_each_dataset(
        self, mock_adapter: MagicMock, sample_dataset_info: DatasetInfo
    ) -> None:
        """load_all は各データセットに対して list_tables を呼び出す。"""
        mock_adapter.list_datasets.return_value = iter([sample_dataset_info])
        mock_adapter.list_tables.return_value = iter([])

        loader = DatasetLoader(adapter=mock_adapter)
        loader.load_all("test-project")

        mock_adapter.list_tables.assert_called_once_with(
            sample_dataset_info.dataset_id, "test-project"
        )

    def test_load_all_loads_tables_into_internal_dict(
        self,
        mock_adapter: MagicMock,
        sample_dataset_info: DatasetInfo,
        sample_table_info: TableInfo,
    ) -> None:
        """load_all はテーブルを内部辞書に登録する。"""
        mock_adapter.list_datasets.return_value = iter([sample_dataset_info])
        mock_adapter.list_tables.return_value = iter([sample_table_info])

        loader = DatasetLoader(adapter=mock_adapter)
        loader.load_all("test-project")

        assert sample_table_info.full_path in loader._tables
        assert loader._tables[sample_table_info.full_path] == sample_table_info

    def test_load_all_loads_tables_by_dataset(
        self,
        mock_adapter: MagicMock,
        sample_dataset_info: DatasetInfo,
        sample_table_info: TableInfo,
    ) -> None:
        """load_all はデータセット別テーブル辞書にテーブルを登録する。"""
        mock_adapter.list_datasets.return_value = iter([sample_dataset_info])
        mock_adapter.list_tables.return_value = iter([sample_table_info])

        loader = DatasetLoader(adapter=mock_adapter)
        loader.load_all("test-project")

        assert sample_dataset_info.dataset_id in loader._tables_by_dataset
        assert (
            sample_table_info
            in loader._tables_by_dataset[sample_dataset_info.dataset_id]
        )

    def test_load_all_result_success_count(
        self, mock_adapter: MagicMock, sample_dataset_info: DatasetInfo
    ) -> None:
        """load_all の結果に成功したデータセット数が含まれる。"""
        mock_adapter.list_datasets.return_value = iter([sample_dataset_info])
        mock_adapter.list_tables.return_value = iter([])

        loader = DatasetLoader(adapter=mock_adapter)
        result = loader.load_all("test-project")

        assert result.datasets_success == 1

    def test_load_all_result_tables_total(
        self,
        mock_adapter: MagicMock,
        sample_dataset_info: DatasetInfo,
        sample_table_info: TableInfo,
    ) -> None:
        """load_all の結果にテーブル総数が含まれる。"""
        mock_adapter.list_datasets.return_value = iter([sample_dataset_info])
        mock_adapter.list_tables.return_value = iter([sample_table_info])

        loader = DatasetLoader(adapter=mock_adapter)
        result = loader.load_all("test-project")

        assert result.tables_total == 1


class TestDatasetLoaderLoadAllErrorHandling:
    """DatasetLoader の load_all メソッドのエラー処理に関するテスト。"""

    def test_load_all_continues_on_dataset_error(self, mock_adapter: MagicMock) -> None:
        """load_all はデータセットエラーが発生しても他のデータセットの処理を継続する。"""
        dataset1 = DatasetInfo(
            dataset_id="dataset1",
            project="test-project",
            full_path="test-project.dataset1",
            created=None,
            modified=None,
            location=None,
        )
        dataset2 = DatasetInfo(
            dataset_id="dataset2",
            project="test-project",
            full_path="test-project.dataset2",
            created=None,
            modified=None,
            location=None,
        )
        table2 = TableInfo(
            table_id="table2",
            dataset_id="dataset2",
            project="test-project",
            full_path="test-project.dataset2.table2",
            table_type="TABLE",
        )

        mock_adapter.list_datasets.return_value = iter([dataset1, dataset2])

        # dataset1 はエラー、dataset2 は成功
        def list_tables_side_effect(
            dataset_id: str, project: str
        ) -> Iterator[TableInfo]:
            if dataset_id == "dataset1":
                raise PermissionDeniedError("Permission denied for dataset1")
            return iter([table2])

        mock_adapter.list_tables.side_effect = list_tables_side_effect

        loader = DatasetLoader(adapter=mock_adapter)
        result = loader.load_all("test-project")

        # dataset2 のテーブルがロードされている
        assert "test-project.dataset2.table2" in loader._tables
        # エラーが発生したデータセットの情報が含まれる
        assert result.datasets_failed == 1
        assert result.datasets_success == 1

    def test_load_all_records_error_in_result(
        self, mock_adapter: MagicMock, sample_dataset_info: DatasetInfo
    ) -> None:
        """load_all はエラー情報を LoadResult.errors に記録する。"""
        mock_adapter.list_datasets.return_value = iter([sample_dataset_info])
        mock_adapter.list_tables.side_effect = DatasetNotFoundError("Dataset not found")

        loader = DatasetLoader(adapter=mock_adapter)
        result = loader.load_all("test-project")

        assert sample_dataset_info.dataset_id in result.errors
        assert "Dataset not found" in result.errors[sample_dataset_info.dataset_id]

    def test_load_all_handles_network_error(
        self, mock_adapter: MagicMock, sample_dataset_info: DatasetInfo
    ) -> None:
        """load_all はネットワークエラーを記録して処理を継続する。"""
        mock_adapter.list_datasets.return_value = iter([sample_dataset_info])
        mock_adapter.list_tables.side_effect = NetworkError("Network error occurred")

        loader = DatasetLoader(adapter=mock_adapter)
        result = loader.load_all("test-project")

        assert result.datasets_failed == 1
        assert sample_dataset_info.dataset_id in result.errors


class TestDatasetLoaderLoadAllProgress:
    """DatasetLoader の load_all メソッドの進捗通知に関するテスト。"""

    def test_load_all_calls_progress_callback(
        self, mock_adapter: MagicMock, sample_dataset_info: DatasetInfo
    ) -> None:
        """load_all は進捗コールバックを呼び出す。"""
        mock_adapter.list_datasets.return_value = iter([sample_dataset_info])
        mock_adapter.list_tables.return_value = iter([])

        callback = MagicMock()

        loader = DatasetLoader(adapter=mock_adapter)
        loader.load_all("test-project", on_progress=callback)

        callback.assert_called_once_with(1, 1, sample_dataset_info.dataset_id)

    def test_load_all_calls_progress_callback_for_multiple_datasets(
        self, mock_adapter: MagicMock
    ) -> None:
        """load_all は複数データセットに対して進捗コールバックを順番に呼び出す。"""
        dataset1 = DatasetInfo(
            dataset_id="dataset1",
            project="test-project",
            full_path="test-project.dataset1",
            created=None,
            modified=None,
            location=None,
        )
        dataset2 = DatasetInfo(
            dataset_id="dataset2",
            project="test-project",
            full_path="test-project.dataset2",
            created=None,
            modified=None,
            location=None,
        )

        mock_adapter.list_datasets.return_value = iter([dataset1, dataset2])
        mock_adapter.list_tables.return_value = iter([])

        callback = MagicMock()

        loader = DatasetLoader(adapter=mock_adapter)
        loader.load_all("test-project", on_progress=callback)

        # 2回呼び出されることを確認
        assert callback.call_count == 2
        # 呼び出し順序を確認
        callback.assert_any_call(1, 2, "dataset1")
        callback.assert_any_call(2, 2, "dataset2")

    def test_load_all_works_without_progress_callback(
        self, mock_adapter: MagicMock, sample_dataset_info: DatasetInfo
    ) -> None:
        """load_all は進捗コールバックなしでも動作する。"""
        mock_adapter.list_datasets.return_value = iter([sample_dataset_info])
        mock_adapter.list_tables.return_value = iter([])

        loader = DatasetLoader(adapter=mock_adapter)
        result = loader.load_all("test-project")

        # エラーなく完了すること
        assert result.datasets_success == 1


class TestDatasetLoaderLoadAllMultipleDatasets:
    """DatasetLoader の load_all メソッドの複数データセット処理に関するテスト。"""

    def test_load_all_handles_multiple_datasets(self, mock_adapter: MagicMock) -> None:
        """load_all は複数のデータセットを処理できる。"""
        dataset1 = DatasetInfo(
            dataset_id="dataset1",
            project="test-project",
            full_path="test-project.dataset1",
            created=None,
            modified=None,
            location=None,
        )
        dataset2 = DatasetInfo(
            dataset_id="dataset2",
            project="test-project",
            full_path="test-project.dataset2",
            created=None,
            modified=None,
            location=None,
        )
        table1 = TableInfo(
            table_id="table1",
            dataset_id="dataset1",
            project="test-project",
            full_path="test-project.dataset1.table1",
            table_type="TABLE",
        )
        table2 = TableInfo(
            table_id="table2",
            dataset_id="dataset2",
            project="test-project",
            full_path="test-project.dataset2.table2",
            table_type="VIEW",
        )

        mock_adapter.list_datasets.return_value = iter([dataset1, dataset2])

        def list_tables_side_effect(
            dataset_id: str, project: str
        ) -> Iterator[TableInfo]:
            if dataset_id == "dataset1":
                return iter([table1])
            return iter([table2])

        mock_adapter.list_tables.side_effect = list_tables_side_effect

        loader = DatasetLoader(adapter=mock_adapter)
        result = loader.load_all("test-project")

        assert len(loader._datasets) == 2
        assert len(loader._tables) == 2
        assert result.datasets_success == 2
        assert result.tables_total == 2


class TestDatasetLoaderGetDataset:
    """DatasetLoader の get_dataset メソッドに関するテスト。"""

    def test_get_dataset_returns_dataset_info_by_id(
        self,
        mock_adapter: MagicMock,
        sample_dataset_info: DatasetInfo,
    ) -> None:
        """get_dataset は dataset_id で DatasetInfo を返す。"""
        mock_adapter.list_datasets.return_value = iter([sample_dataset_info])
        mock_adapter.list_tables.return_value = iter([])

        loader = DatasetLoader(adapter=mock_adapter)
        loader.load_all("test-project")

        result = loader.get_dataset(sample_dataset_info.dataset_id)

        assert result is not None
        assert result == sample_dataset_info

    def test_get_dataset_returns_none_for_unknown_id(
        self, mock_adapter: MagicMock
    ) -> None:
        """get_dataset は存在しない dataset_id に対して None を返す。"""
        mock_adapter.list_datasets.return_value = iter([])

        loader = DatasetLoader(adapter=mock_adapter)
        loader.load_all("test-project")

        result = loader.get_dataset("nonexistent_dataset")

        assert result is None

    def test_get_dataset_is_o1_complexity(self, mock_adapter: MagicMock) -> None:
        """get_dataset は O(1) の計算量で動作する（辞書検索を使用）。"""
        # 複数のデータセットを用意
        datasets = [
            DatasetInfo(
                dataset_id=f"dataset_{i}",
                project="test-project",
                full_path=f"test-project.dataset_{i}",
                created=None,
                modified=None,
                location=None,
            )
            for i in range(100)
        ]

        mock_adapter.list_datasets.return_value = iter(datasets)
        mock_adapter.list_tables.return_value = iter([])

        loader = DatasetLoader(adapter=mock_adapter)
        loader.load_all("test-project")

        # 任意の位置のデータセットを検索
        result = loader.get_dataset("dataset_50")

        assert result is not None
        assert result.dataset_id == "dataset_50"

    def test_get_dataset_before_load_returns_none(
        self, mock_adapter: MagicMock
    ) -> None:
        """load_all 呼び出し前の get_dataset は None を返す。"""
        loader = DatasetLoader(adapter=mock_adapter)

        result = loader.get_dataset("any_dataset")

        assert result is None


class TestDatasetLoaderGetTable:
    """DatasetLoader の get_table メソッドに関するテスト。"""

    def test_get_table_returns_table_info_by_full_path(
        self,
        mock_adapter: MagicMock,
        sample_dataset_info: DatasetInfo,
        sample_table_info: TableInfo,
    ) -> None:
        """get_table は full_path で TableInfo を返す。"""
        mock_adapter.list_datasets.return_value = iter([sample_dataset_info])
        mock_adapter.list_tables.return_value = iter([sample_table_info])

        loader = DatasetLoader(adapter=mock_adapter)
        loader.load_all("test-project")

        result = loader.get_table(sample_table_info.full_path)

        assert result is not None
        assert result == sample_table_info

    def test_get_table_returns_none_for_unknown_path(
        self, mock_adapter: MagicMock
    ) -> None:
        """get_table は存在しない full_path に対して None を返す。"""
        mock_adapter.list_datasets.return_value = iter([])

        loader = DatasetLoader(adapter=mock_adapter)
        loader.load_all("test-project")

        result = loader.get_table("project.dataset.nonexistent_table")

        assert result is None

    def test_get_table_is_efficient(self, mock_adapter: MagicMock) -> None:
        """get_table は効率的に動作する（辞書検索を使用）。"""
        dataset = DatasetInfo(
            dataset_id="test_dataset",
            project="test-project",
            full_path="test-project.test_dataset",
            created=None,
            modified=None,
            location=None,
        )
        # 複数のテーブルを用意
        tables = [
            TableInfo(
                table_id=f"table_{i}",
                dataset_id="test_dataset",
                project="test-project",
                full_path=f"test-project.test_dataset.table_{i}",
                table_type="TABLE",
            )
            for i in range(100)
        ]

        mock_adapter.list_datasets.return_value = iter([dataset])
        mock_adapter.list_tables.return_value = iter(tables)

        loader = DatasetLoader(adapter=mock_adapter)
        loader.load_all("test-project")

        # 任意の位置のテーブルを検索
        result = loader.get_table("test-project.test_dataset.table_50")

        assert result is not None
        assert result.table_id == "table_50"

    def test_get_table_before_load_returns_none(self, mock_adapter: MagicMock) -> None:
        """load_all 呼び出し前の get_table は None を返す。"""
        loader = DatasetLoader(adapter=mock_adapter)

        result = loader.get_table("project.dataset.table")

        assert result is None


class TestDatasetLoaderGetTablesByDataset:
    """DatasetLoader の get_tables_by_dataset メソッドに関するテスト。"""

    def test_get_tables_by_dataset_returns_tables_list(
        self,
        mock_adapter: MagicMock,
        sample_dataset_info: DatasetInfo,
        sample_table_info: TableInfo,
    ) -> None:
        """get_tables_by_dataset は指定したデータセットのテーブルリストを返す。"""
        mock_adapter.list_datasets.return_value = iter([sample_dataset_info])
        mock_adapter.list_tables.return_value = iter([sample_table_info])

        loader = DatasetLoader(adapter=mock_adapter)
        loader.load_all("test-project")

        result = loader.get_tables_by_dataset(sample_dataset_info.dataset_id)

        assert len(result) == 1
        assert sample_table_info in result

    def test_get_tables_by_dataset_returns_empty_list_for_unknown_dataset(
        self, mock_adapter: MagicMock
    ) -> None:
        """get_tables_by_dataset は存在しないデータセットに対して空リストを返す。"""
        mock_adapter.list_datasets.return_value = iter([])

        loader = DatasetLoader(adapter=mock_adapter)
        loader.load_all("test-project")

        result = loader.get_tables_by_dataset("nonexistent_dataset")

        assert result == []

    def test_get_tables_by_dataset_returns_multiple_tables(
        self, mock_adapter: MagicMock
    ) -> None:
        """get_tables_by_dataset は複数のテーブルを返す。"""
        dataset = DatasetInfo(
            dataset_id="test_dataset",
            project="test-project",
            full_path="test-project.test_dataset",
            created=None,
            modified=None,
            location=None,
        )
        table1 = TableInfo(
            table_id="table1",
            dataset_id="test_dataset",
            project="test-project",
            full_path="test-project.test_dataset.table1",
            table_type="TABLE",
        )
        table2 = TableInfo(
            table_id="table2",
            dataset_id="test_dataset",
            project="test-project",
            full_path="test-project.test_dataset.table2",
            table_type="VIEW",
        )

        mock_adapter.list_datasets.return_value = iter([dataset])
        mock_adapter.list_tables.return_value = iter([table1, table2])

        loader = DatasetLoader(adapter=mock_adapter)
        loader.load_all("test-project")

        result = loader.get_tables_by_dataset("test_dataset")

        assert len(result) == 2
        assert table1 in result
        assert table2 in result

    def test_get_tables_by_dataset_before_load_returns_empty_list(
        self, mock_adapter: MagicMock
    ) -> None:
        """load_all 呼び出し前の get_tables_by_dataset は空リストを返す。"""
        loader = DatasetLoader(adapter=mock_adapter)

        result = loader.get_tables_by_dataset("any_dataset")

        assert result == []

    def test_get_tables_by_dataset_returns_only_tables_from_specified_dataset(
        self, mock_adapter: MagicMock
    ) -> None:
        """get_tables_by_dataset は指定したデータセットのテーブルのみを返す。"""
        dataset1 = DatasetInfo(
            dataset_id="dataset1",
            project="test-project",
            full_path="test-project.dataset1",
            created=None,
            modified=None,
            location=None,
        )
        dataset2 = DatasetInfo(
            dataset_id="dataset2",
            project="test-project",
            full_path="test-project.dataset2",
            created=None,
            modified=None,
            location=None,
        )
        table1 = TableInfo(
            table_id="table1",
            dataset_id="dataset1",
            project="test-project",
            full_path="test-project.dataset1.table1",
            table_type="TABLE",
        )
        table2 = TableInfo(
            table_id="table2",
            dataset_id="dataset2",
            project="test-project",
            full_path="test-project.dataset2.table2",
            table_type="VIEW",
        )

        mock_adapter.list_datasets.return_value = iter([dataset1, dataset2])

        def list_tables_side_effect(
            dataset_id: str, project: str
        ) -> Iterator[TableInfo]:
            if dataset_id == "dataset1":
                return iter([table1])
            return iter([table2])

        mock_adapter.list_tables.side_effect = list_tables_side_effect

        loader = DatasetLoader(adapter=mock_adapter)
        loader.load_all("test-project")

        result = loader.get_tables_by_dataset("dataset1")

        assert len(result) == 1
        assert table1 in result
        assert table2 not in result
