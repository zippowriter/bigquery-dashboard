"""ExportLeafTablesUseCaseのユニットテスト."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from application.usecases.export_leaf_tables_usecase import (
    ExportLeafTablesRequest,
    ExportLeafTablesUseCase,
)
from domain.entities.lineage import LeafTable
from domain.entities.table import Table
from domain.value_objects.table_id import TableId


class TestExportLeafTablesRequest:
    """ExportLeafTablesRequestのテストクラス."""

    def test_valid_with_project_ids(self) -> None:
        """project_idsのみ指定で正常に作成できることを確認."""
        request = ExportLeafTablesRequest(project_ids=["project-a"])
        assert request.project_ids == ["project-a"]
        assert request.root_tables is None

    def test_valid_with_root_tables(self) -> None:
        """root_tablesのみ指定で正常に作成できることを確認."""
        root_tables = [
            TableId(project_id="project-a", dataset_id="raw", table_id="events")
        ]
        request = ExportLeafTablesRequest(root_tables=root_tables)
        assert request.project_ids is None
        assert request.root_tables == root_tables

    def test_invalid_both_none(self) -> None:
        """両方Noneの場合にエラーになることを確認."""
        with pytest.raises(ValueError, match="どちらかを指定"):
            ExportLeafTablesRequest()

    def test_invalid_both_specified(self) -> None:
        """両方指定した場合にエラーになることを確認."""
        with pytest.raises(ValueError, match="同時に指定できません"):
            ExportLeafTablesRequest(
                project_ids=["project-a"],
                root_tables=[
                    TableId(project_id="project-a", dataset_id="raw", table_id="events")
                ],
            )


class TestExportLeafTablesUseCase:
    """ExportLeafTablesUseCaseのテストクラス."""

    @pytest.fixture
    def mock_table_repository(self) -> Mock:
        """モックTableRepositoryのフィクスチャ."""
        mock = Mock()
        mock.list_tables.return_value = [
            Table(
                table_id=TableId(
                    project_id="project-a",
                    dataset_id="dataset1",
                    table_id="table1",
                ),
                table_type="BASE TABLE",
            ),
            Table(
                table_id=TableId(
                    project_id="project-a",
                    dataset_id="dataset1",
                    table_id="table2",
                ),
                table_type="BASE TABLE",
            ),
        ]
        return mock

    @pytest.fixture
    def mock_lineage_repository(self) -> Mock:
        """モックLineageRepositoryのフィクスチャ."""
        mock = Mock()
        mock.get_leaf_tables.return_value = [
            LeafTable(
                table_id=TableId(
                    project_id="project-a",
                    dataset_id="dataset1",
                    table_id="table2",
                ),
                upstream_count=1,
            ),
        ]
        mock.find_leaf_tables_from_roots.return_value = [
            LeafTable(
                table_id=TableId(
                    project_id="project-a",
                    dataset_id="reports",
                    table_id="final_report",
                ),
                upstream_count=3,
            ),
        ]
        return mock

    @pytest.fixture
    def mock_file_writer(self) -> Mock:
        """モックFileWriterのフィクスチャ."""
        return Mock()

    def test_execute_with_project_ids(
        self,
        mock_table_repository: Mock,
        mock_lineage_repository: Mock,
        mock_file_writer: Mock,
        tmp_path: Path,
    ) -> None:
        """project_ids指定で正常にエクスポートできることを確認."""
        usecase = ExportLeafTablesUseCase(
            table_repository=mock_table_repository,
            lineage_repository=mock_lineage_repository,
            file_writer=mock_file_writer,
        )

        output_path = tmp_path / "leaf_tables.csv"
        request = ExportLeafTablesRequest(
            project_ids=["project-a"],
            output_path=output_path,
            output_format="csv",
        )

        result = usecase.execute(request)

        assert result.total_tables_count == 2
        assert result.leaf_tables_count == 1
        assert result.output_path == output_path

        mock_table_repository.list_tables.assert_called_once_with(["project-a"])
        mock_lineage_repository.get_leaf_tables.assert_called_once()
        mock_file_writer.write_leaf_tables.assert_called_once()

    def test_execute_with_root_tables(
        self,
        mock_table_repository: Mock,
        mock_lineage_repository: Mock,
        mock_file_writer: Mock,
        tmp_path: Path,
    ) -> None:
        """root_tables指定で正常にエクスポートできることを確認."""
        usecase = ExportLeafTablesUseCase(
            table_repository=mock_table_repository,
            lineage_repository=mock_lineage_repository,
            file_writer=mock_file_writer,
        )

        root_tables = [
            TableId(project_id="project-a", dataset_id="raw", table_id="events"),
            TableId(project_id="project-a", dataset_id="raw", table_id="users"),
        ]
        output_path = tmp_path / "leaf_tables.csv"
        request = ExportLeafTablesRequest(
            root_tables=root_tables,
            output_path=output_path,
            output_format="csv",
        )

        result = usecase.execute(request)

        assert result.total_tables_count == 2  # ルートテーブル数
        assert result.leaf_tables_count == 1
        assert result.output_path == output_path

        # project_idsモードのメソッドは呼ばれない
        mock_table_repository.list_tables.assert_not_called()
        mock_lineage_repository.get_leaf_tables.assert_not_called()

        # root_tablesモードのメソッドが呼ばれる
        mock_lineage_repository.find_leaf_tables_from_roots.assert_called_once_with(
            root_tables,
            allowed_project_ids=None,
        )
        mock_file_writer.write_leaf_tables.assert_called_once()

    def test_execute_with_json_format(
        self,
        mock_table_repository: Mock,
        mock_lineage_repository: Mock,
        mock_file_writer: Mock,
        tmp_path: Path,
    ) -> None:
        """JSON形式でエクスポートできることを確認."""
        usecase = ExportLeafTablesUseCase(
            table_repository=mock_table_repository,
            lineage_repository=mock_lineage_repository,
            file_writer=mock_file_writer,
        )

        output_path = tmp_path / "leaf_tables.json"
        request = ExportLeafTablesRequest(
            project_ids=["project-a"],
            output_path=output_path,
            output_format="json",
        )

        usecase.execute(request)

        call_args = mock_file_writer.write_leaf_tables.call_args
        assert call_args[0][2] == "json"

    def test_execute_empty_root_tables(
        self,
        mock_table_repository: Mock,
        mock_file_writer: Mock,
        tmp_path: Path,
    ) -> None:
        """空のroot_tablesリストでも正常に動作することを確認."""
        mock_lineage_repo = Mock()
        mock_lineage_repo.find_leaf_tables_from_roots.return_value = []

        usecase = ExportLeafTablesUseCase(
            table_repository=mock_table_repository,
            lineage_repository=mock_lineage_repo,
            file_writer=mock_file_writer,
        )

        request = ExportLeafTablesRequest(
            root_tables=[],
            output_path=tmp_path / "leaf_tables.csv",
        )

        result = usecase.execute(request)

        assert result.total_tables_count == 0
        assert result.leaf_tables_count == 0
