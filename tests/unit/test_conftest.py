"""conftest.py のフィクスチャが正しく動作することを検証するテスト。"""

from datetime import datetime, timezone
from unittest.mock import MagicMock


class TestMockAdapterFixture:
    """mock_adapter フィクスチャのテスト。"""

    def test_mock_adapter_is_magic_mock(self, mock_adapter: MagicMock) -> None:
        """mock_adapter が MagicMock インスタンスであること。"""
        assert isinstance(mock_adapter, MagicMock)

    def test_mock_adapter_supports_context_manager(
        self, mock_adapter: MagicMock
    ) -> None:
        """mock_adapter がコンテキストマネージャーとして使用可能であること。"""
        with mock_adapter as adapter:
            assert adapter is mock_adapter


class TestSampleDatasetInfoDataFixture:
    """sample_dataset_info_data フィクスチャのテスト。"""

    def test_contains_required_fields(self, sample_dataset_info_data: dict) -> None:
        """DatasetInfo に必要な全フィールドが含まれていること。"""
        required_fields = {
            "dataset_id",
            "project",
            "full_path",
            "created",
            "modified",
            "location",
        }
        assert required_fields <= set(sample_dataset_info_data.keys())

    def test_full_path_format(self, sample_dataset_info_data: dict) -> None:
        """full_path が project.dataset 形式であること。"""
        full_path = sample_dataset_info_data["full_path"]
        project = sample_dataset_info_data["project"]
        dataset_id = sample_dataset_info_data["dataset_id"]
        assert full_path == f"{project}.{dataset_id}"

    def test_datetime_fields_are_timezone_aware(
        self, sample_dataset_info_data: dict
    ) -> None:
        """created と modified がタイムゾーン情報を持つ datetime であること。"""
        assert isinstance(sample_dataset_info_data["created"], datetime)
        assert isinstance(sample_dataset_info_data["modified"], datetime)
        assert sample_dataset_info_data["created"].tzinfo is not None
        assert sample_dataset_info_data["modified"].tzinfo is not None


class TestSampleTableInfoDataFixture:
    """sample_table_info_data フィクスチャのテスト。"""

    def test_contains_required_fields(self, sample_table_info_data: dict) -> None:
        """TableInfo に必要な全フィールドが含まれていること。"""
        required_fields = {
            "table_id",
            "dataset_id",
            "project",
            "full_path",
            "table_type",
        }
        assert required_fields <= set(sample_table_info_data.keys())

    def test_full_path_format(self, sample_table_info_data: dict) -> None:
        """full_path が project.dataset.table 形式であること。"""
        full_path = sample_table_info_data["full_path"]
        project = sample_table_info_data["project"]
        dataset_id = sample_table_info_data["dataset_id"]
        table_id = sample_table_info_data["table_id"]
        assert full_path == f"{project}.{dataset_id}.{table_id}"

    def test_table_type_is_valid(self, sample_table_info_data: dict) -> None:
        """table_type が有効な値であること。"""
        valid_types = {"TABLE", "VIEW", "MATERIALIZED_VIEW", "EXTERNAL"}
        assert sample_table_info_data["table_type"] in valid_types


class TestSampleLoadResultDataFixture:
    """sample_load_result_data フィクスチャのテスト。"""

    def test_contains_required_fields(self, sample_load_result_data: dict) -> None:
        """LoadResult に必要な全フィールドが含まれていること。"""
        required_fields = {
            "datasets_success",
            "datasets_failed",
            "tables_total",
            "errors",
        }
        assert required_fields <= set(sample_load_result_data.keys())

    def test_counts_are_non_negative(self, sample_load_result_data: dict) -> None:
        """カウント値が非負整数であること。"""
        assert sample_load_result_data["datasets_success"] >= 0
        assert sample_load_result_data["datasets_failed"] >= 0
        assert sample_load_result_data["tables_total"] >= 0

    def test_errors_is_dict(self, sample_load_result_data: dict) -> None:
        """errors が辞書であること。"""
        assert isinstance(sample_load_result_data["errors"], dict)
