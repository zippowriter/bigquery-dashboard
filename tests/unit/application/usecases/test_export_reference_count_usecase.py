"""ExportReferenceCountUseCaseのユニットテスト."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from application.usecases.export_reference_count_usecase import (
    ExportReferenceCountRequest,
    ExportReferenceCountUseCase,
)
from domain.entities.analyzed_table import AnalyzedTable
from domain.entities.table import Table
from domain.value_objects.table_id import TableId
from domain.value_objects.usage_info import UsageInfo


@pytest.fixture
def mock_table_repository() -> Mock:
    """モックTableRepositoryのフィクスチャ."""
    mock = Mock()

    table = Table(
        table_id=TableId(
            project_id="project-a",
            dataset_id="dataset1",
            table_id="table1",
        ),
        table_type="BASE TABLE",
    )

    # list_tablesの戻り値を設定
    mock.list_tables.return_value = [table]

    # get_table_reference_countsの戻り値を設定
    mock.get_table_reference_counts.return_value = [
        AnalyzedTable(
            table=table,
            usage_info=UsageInfo(job_count=100, unique_user=5),
        ),
    ]

    return mock


@pytest.fixture
def mock_file_writer() -> Mock:
    """モックFileWriterのフィクスチャ."""
    return Mock()


class TestExportReferenceCountUseCase:
    """ExportReferenceCountUseCaseのテストクラス."""

    def test_execute_success(
        self,
        mock_table_repository: Mock,
        mock_file_writer: Mock,
        tmp_path: Path,
    ) -> None:
        """正常にエクスポートできることを確認."""
        usecase = ExportReferenceCountUseCase(
            table_repository=mock_table_repository,
            file_writer=mock_file_writer,
        )

        output_path = tmp_path / "output.csv"
        request = ExportReferenceCountRequest(
            project_ids=["project-a"],
            days_back=90,
            output_path=output_path,
            output_format="csv",
        )

        result = usecase.execute(request)

        assert result.tables_count == 1
        assert result.output_path == output_path

        # リポジトリが正しく呼び出されたことを確認
        mock_table_repository.list_tables.assert_called_once_with(["project-a"])
        mock_table_repository.get_table_reference_counts.assert_called_once()

        # ファイル出力が呼び出されたことを確認
        mock_file_writer.write_analyzed_tables.assert_called_once()

    def test_execute_with_json_format(
        self,
        mock_table_repository: Mock,
        mock_file_writer: Mock,
        tmp_path: Path,
    ) -> None:
        """JSON形式でエクスポートできることを確認."""
        usecase = ExportReferenceCountUseCase(
            table_repository=mock_table_repository,
            file_writer=mock_file_writer,
        )

        output_path = tmp_path / "output.json"
        request = ExportReferenceCountRequest(
            project_ids=["project-a"],
            days_back=30,
            output_path=output_path,
            output_format="json",
        )

        usecase.execute(request)

        # ファイル出力がJSON形式で呼び出されたことを確認
        call_args = mock_file_writer.write_analyzed_tables.call_args
        assert call_args[0][2] == "json"  # output_format

    def test_execute_with_multiple_projects(
        self,
        mock_table_repository: Mock,
        mock_file_writer: Mock,
        tmp_path: Path,
    ) -> None:
        """複数プロジェクトでエクスポートできることを確認."""
        usecase = ExportReferenceCountUseCase(
            table_repository=mock_table_repository,
            file_writer=mock_file_writer,
        )

        request = ExportReferenceCountRequest(
            project_ids=["project-a", "project-b"],
            output_path=tmp_path / "output.csv",
        )

        usecase.execute(request)

        mock_table_repository.list_tables.assert_called_once_with(
            ["project-a", "project-b"]
        )

    def test_execute_empty_tables(
        self,
        mock_file_writer: Mock,
        tmp_path: Path,
    ) -> None:
        """テーブルが0件の場合も正常に動作することを確認."""
        mock_repo = Mock()
        mock_repo.list_tables.return_value = []
        mock_repo.get_table_reference_counts.return_value = []

        usecase = ExportReferenceCountUseCase(
            table_repository=mock_repo,
            file_writer=mock_file_writer,
        )

        request = ExportReferenceCountRequest(
            project_ids=["project-a"],
            output_path=tmp_path / "output.csv",
        )

        result = usecase.execute(request)

        assert result.tables_count == 0
