"""pytest 共通フィクスチャ。

テスト全体で使用するフィクスチャを定義する。
"""

from datetime import datetime, timezone
from typing import Literal, TypedDict
from unittest.mock import MagicMock

import pytest

# TableType 型定義（models.py と同等）
TableType = Literal["TABLE", "VIEW", "MATERIALIZED_VIEW", "EXTERNAL"]


class DatasetInfoData(TypedDict):
    """DatasetInfo 生成用データの型定義。"""

    dataset_id: str
    project: str
    full_path: str
    created: datetime | None
    modified: datetime | None
    location: str | None


class TableInfoData(TypedDict):
    """TableInfo 生成用データの型定義。"""

    table_id: str
    dataset_id: str
    project: str
    full_path: str
    table_type: TableType


class LoadResultData(TypedDict):
    """LoadResult 生成用データの型定義。"""

    datasets_success: int
    datasets_failed: int
    tables_total: int
    errors: dict[str, str]


@pytest.fixture
def mock_adapter() -> MagicMock:
    """モック化された BQClientAdapter を提供する。

    Returns:
        BQClientAdapter のモックオブジェクト。
    """
    adapter = MagicMock()
    adapter.__enter__ = MagicMock(return_value=adapter)
    adapter.__exit__ = MagicMock(return_value=None)
    return adapter


@pytest.fixture
def sample_dataset_info_data() -> DatasetInfoData:
    """テスト用 DatasetInfo 生成データを提供する。

    Returns:
        DatasetInfo 生成に必要なフィールドの辞書。
    """
    return DatasetInfoData(
        dataset_id="test_dataset",
        project="test-project",
        full_path="test-project.test_dataset",
        created=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        modified=datetime(2024, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        location="US",
    )


@pytest.fixture
def sample_table_info_data() -> TableInfoData:
    """テスト用 TableInfo 生成データを提供する。

    Returns:
        TableInfo 生成に必要なフィールドの辞書。
    """
    return TableInfoData(
        table_id="test_table",
        dataset_id="test_dataset",
        project="test-project",
        full_path="test-project.test_dataset.test_table",
        table_type="TABLE",
    )


@pytest.fixture
def sample_load_result_data() -> LoadResultData:
    """テスト用 LoadResult 生成データを提供する。

    Returns:
        LoadResult 生成に必要なフィールドの辞書。
    """
    return LoadResultData(
        datasets_success=5,
        datasets_failed=1,
        tables_total=25,
        errors={"failed_dataset": "Permission denied"},
    )


@pytest.fixture
def sample_dataset_info(sample_dataset_info_data: DatasetInfoData) -> "DatasetInfo":
    """テスト用 DatasetInfo インスタンスを提供する。

    Returns:
        DatasetInfo インスタンス。
    """
    from bq_table_reference.domain.models import DatasetInfo

    return DatasetInfo(**sample_dataset_info_data)


@pytest.fixture
def sample_table_info(sample_table_info_data: TableInfoData) -> "TableInfo":
    """テスト用 TableInfo インスタンスを提供する。

    Returns:
        TableInfo インスタンス。
    """
    from bq_table_reference.domain.models import TableInfo

    return TableInfo(**sample_table_info_data)
