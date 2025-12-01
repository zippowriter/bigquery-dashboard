"""DatasetInfo, TableInfo, LoadResult dataclass のテスト。

ドメインモデルの生成、属性アクセス、イミュータブル性を検証する。
"""

from datetime import datetime, timezone

import pytest

from pydantic import ValidationError

from tests.conftest import DatasetInfoData


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
