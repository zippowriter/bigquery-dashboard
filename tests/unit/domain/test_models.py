"""DatasetInfo, TableInfo, LoadResult dataclass のテスト。

ドメインモデルの生成、属性アクセス、イミュータブル性を検証する。
"""

from datetime import datetime, timezone

import pytest

from pydantic import ValidationError

from tests.conftest import DatasetInfoData, TableInfoData


class TestDatasetInfo:
    """DatasetInfo dataclass のテスト。"""

    def test_create_dataset_info_with_all_fields(
        self, sample_dataset_info_data: DatasetInfoData
    ) -> None:
        """全フィールドを指定して DatasetInfo を生成できることを検証する。"""
        from bq_table_reference.domain.models import DatasetInfo

        dataset_info = DatasetInfo(**sample_dataset_info_data)

        assert dataset_info.dataset_id == "test_dataset"
        assert dataset_info.project == "test-project"
        assert dataset_info.full_path == "test-project.test_dataset"
        assert dataset_info.created == datetime(
            2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc
        )
        assert dataset_info.modified == datetime(
            2024, 6, 1, 0, 0, 0, tzinfo=timezone.utc
        )
        assert dataset_info.location == "US"

    def test_create_dataset_info_with_optional_fields_as_none(self) -> None:
        """オプショナルフィールドを None で生成できることを検証する。"""
        from bq_table_reference.domain.models import DatasetInfo

        dataset_info = DatasetInfo(
            dataset_id="minimal_dataset",
            project="my-project",
            full_path="my-project.minimal_dataset",
            created=None,
            modified=None,
            location=None,
        )

        assert dataset_info.dataset_id == "minimal_dataset"
        assert dataset_info.project == "my-project"
        assert dataset_info.full_path == "my-project.minimal_dataset"
        assert dataset_info.created is None
        assert dataset_info.modified is None
        assert dataset_info.location is None

    def test_dataset_info_is_immutable(
        self, sample_dataset_info_data: DatasetInfoData
    ) -> None:
        """DatasetInfo がイミュータブル（frozen）であることを検証する。"""
        from bq_table_reference.domain.models import DatasetInfo

        dataset_info = DatasetInfo(**sample_dataset_info_data)

        with pytest.raises(ValidationError):
            dataset_info.dataset_id = "new_id"

    def test_dataset_info_equality(
        self, sample_dataset_info_data: DatasetInfoData
    ) -> None:
        """同じフィールド値を持つ DatasetInfo が等しいことを検証する。"""
        from bq_table_reference.domain.models import DatasetInfo

        dataset_info1 = DatasetInfo(**sample_dataset_info_data)
        dataset_info2 = DatasetInfo(**sample_dataset_info_data)

        assert dataset_info1 == dataset_info2

    def test_dataset_info_hashable(
        self, sample_dataset_info_data: DatasetInfoData
    ) -> None:
        """DatasetInfo がハッシュ可能（辞書のキーやセットで使用可能）であることを検証する。"""
        from bq_table_reference.domain.models import DatasetInfo

        dataset_info = DatasetInfo(**sample_dataset_info_data)

        # set に追加できることを確認
        # Pydantic frozen model はハッシュ可能だが pyright が認識しないため無視
        dataset_set: set[DatasetInfo] = set()
        dataset_set.add(dataset_info)
        assert dataset_info in dataset_set

        # dict のキーとして使用できることを確認
        dataset_dict: dict[DatasetInfo, str] = {}
        dataset_dict[dataset_info] = "value"
        assert dataset_dict[dataset_info] == "value"

    def test_dataset_info_repr(self, sample_dataset_info_data: DatasetInfoData) -> None:
        """DatasetInfo の repr がクラス名とフィールドを含むことを検証する。"""
        from bq_table_reference.domain.models import DatasetInfo

        dataset_info = DatasetInfo(**sample_dataset_info_data)

        repr_str = repr(dataset_info)
        assert "DatasetInfo" in repr_str
        assert "test_dataset" in repr_str
        assert "test-project" in repr_str


class TestTableInfo:
    """TableInfo dataclass のテスト。"""

    def test_create_table_info_with_all_fields(
        self, sample_table_info_data: TableInfoData
    ) -> None:
        """全フィールドを指定して TableInfo を生成できることを検証する。"""
        from bq_table_reference.domain.models import TableInfo

        table_info = TableInfo(**sample_table_info_data)

        assert table_info.table_id == "test_table"
        assert table_info.dataset_id == "test_dataset"
        assert table_info.project == "test-project"
        assert table_info.full_path == "test-project.test_dataset.test_table"
        assert table_info.table_type == "TABLE"

    def test_create_table_info_with_view_type(self) -> None:
        """テーブル種別 VIEW で TableInfo を生成できることを検証する。"""
        from bq_table_reference.domain.models import TableInfo

        table_info = TableInfo(
            table_id="test_view",
            dataset_id="test_dataset",
            project="test-project",
            full_path="test-project.test_dataset.test_view",
            table_type="VIEW",
        )

        assert table_info.table_type == "VIEW"

    def test_create_table_info_with_materialized_view_type(self) -> None:
        """テーブル種別 MATERIALIZED_VIEW で TableInfo を生成できることを検証する。"""
        from bq_table_reference.domain.models import TableInfo

        table_info = TableInfo(
            table_id="test_mv",
            dataset_id="test_dataset",
            project="test-project",
            full_path="test-project.test_dataset.test_mv",
            table_type="MATERIALIZED_VIEW",
        )

        assert table_info.table_type == "MATERIALIZED_VIEW"

    def test_create_table_info_with_external_type(self) -> None:
        """テーブル種別 EXTERNAL で TableInfo を生成できることを検証する。"""
        from bq_table_reference.domain.models import TableInfo

        table_info = TableInfo(
            table_id="test_external",
            dataset_id="test_dataset",
            project="test-project",
            full_path="test-project.test_dataset.test_external",
            table_type="EXTERNAL",
        )

        assert table_info.table_type == "EXTERNAL"

    def test_table_info_is_immutable(
        self, sample_table_info_data: TableInfoData
    ) -> None:
        """TableInfo がイミュータブル（frozen）であることを検証する。"""
        from bq_table_reference.domain.models import TableInfo

        table_info = TableInfo(**sample_table_info_data)

        with pytest.raises(ValidationError):
            table_info.table_id = "new_id"

    def test_table_info_equality(self, sample_table_info_data: TableInfoData) -> None:
        """同じフィールド値を持つ TableInfo が等しいことを検証する。"""
        from bq_table_reference.domain.models import TableInfo

        table_info1 = TableInfo(**sample_table_info_data)
        table_info2 = TableInfo(**sample_table_info_data)

        assert table_info1 == table_info2

    def test_table_info_hashable(self, sample_table_info_data: TableInfoData) -> None:
        """TableInfo がハッシュ可能（辞書のキーやセットで使用可能）であることを検証する。"""
        from bq_table_reference.domain.models import TableInfo

        table_info = TableInfo(**sample_table_info_data)

        # set に追加できることを確認
        table_set: set[TableInfo] = set()
        table_set.add(table_info)
        assert table_info in table_set

        # dict のキーとして使用できることを確認
        table_dict: dict[TableInfo, str] = {}
        table_dict[table_info] = "value"
        assert table_dict[table_info] == "value"

    def test_table_info_repr(self, sample_table_info_data: TableInfoData) -> None:
        """TableInfo の repr がクラス名とフィールドを含むことを検証する。"""
        from bq_table_reference.domain.models import TableInfo

        table_info = TableInfo(**sample_table_info_data)

        repr_str = repr(table_info)
        assert "TableInfo" in repr_str
        assert "test_table" in repr_str
        assert "test_dataset" in repr_str
        assert "test-project" in repr_str

    def test_table_info_invalid_table_type_raises_error(self) -> None:
        """無効なテーブル種別で TableInfo を生成するとエラーが発生することを検証する。"""
        from bq_table_reference.domain.models import TableInfo

        with pytest.raises(ValidationError):
            TableInfo(
                table_id="test_table",
                dataset_id="test_dataset",
                project="test-project",
                full_path="test-project.test_dataset.test_table",
                table_type="INVALID_TYPE",  # type: ignore[arg-type]
            )
