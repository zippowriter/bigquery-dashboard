"""PandasFileWriterのユニットテスト."""

import json
from pathlib import Path

import pytest

from domain.entities.table import CheckedTable
from domain.value_objects.table_id import TableId
from infra.file.exceptions import FileWriterError
from infra.file.file_writer_impl import PandasFileWriter


@pytest.fixture
def file_writer() -> PandasFileWriter:
    """PandasFileWriterのフィクスチャ."""
    return PandasFileWriter()


@pytest.fixture
def sample_checked_tables() -> list[CheckedTable]:
    """テスト用のCheckedTableリスト."""
    return [
        CheckedTable(
            table_id=TableId(
                project_id="project-a",
                dataset_id="dataset1",
                table_id="table1",
            ),
            table_type="BASE TABLE",
            job_count=100,
            unique_user=5,
        ),
        CheckedTable(
            table_id=TableId(
                project_id="project-a",
                dataset_id="dataset1",
                table_id="table2",
            ),
            table_type="VIEW",
            job_count=50,
            unique_user=3,
        ),
    ]


class TestPandasFileWriter:
    """PandasFileWriterのテストクラス."""

    def test_write_checked_tables_csv(
        self,
        file_writer: PandasFileWriter,
        sample_checked_tables: list[CheckedTable],
        tmp_path: Path,
    ) -> None:
        """CSV形式で出力できることを確認."""
        output_path = tmp_path / "output.csv"

        file_writer.write_checked_tables(
            sample_checked_tables,
            output_path,
            output_format="csv",
        )

        assert output_path.exists()
        content = output_path.read_text()
        lines = content.strip().split("\n")

        assert len(lines) == 3  # ヘッダー + 2行
        assert "project_id" in lines[0]
        assert "project-a" in lines[1]

    def test_write_checked_tables_json(
        self,
        file_writer: PandasFileWriter,
        sample_checked_tables: list[CheckedTable],
        tmp_path: Path,
    ) -> None:
        """JSON形式で出力できることを確認."""
        output_path = tmp_path / "output.json"

        file_writer.write_checked_tables(
            sample_checked_tables,
            output_path,
            output_format="json",
        )

        assert output_path.exists()
        data = json.loads(output_path.read_text())

        assert len(data) == 2
        assert data[0]["project_id"] == "project-a"
        assert data[0]["job_count"] == 100

    def test_write_checked_tables_creates_parent_directory(
        self,
        file_writer: PandasFileWriter,
        sample_checked_tables: list[CheckedTable],
        tmp_path: Path,
    ) -> None:
        """親ディレクトリが存在しない場合に作成されることを確認."""
        output_path = tmp_path / "nested" / "dir" / "output.csv"

        file_writer.write_checked_tables(
            sample_checked_tables,
            output_path,
            output_format="csv",
        )

        assert output_path.exists()

    def test_write_checked_tables_empty_list(
        self,
        file_writer: PandasFileWriter,
        tmp_path: Path,
    ) -> None:
        """空のリストでもファイルが作成されることを確認."""
        output_path = tmp_path / "empty.csv"

        file_writer.write_checked_tables(
            [],
            output_path,
            output_format="csv",
        )

        assert output_path.exists()

    def test_write_checked_tables_unsupported_format(
        self,
        file_writer: PandasFileWriter,
        sample_checked_tables: list[CheckedTable],
        tmp_path: Path,
    ) -> None:
        """サポートされていない形式の場合にエラーが発生することを確認."""
        output_path = tmp_path / "output.xml"

        with pytest.raises(FileWriterError) as exc_info:
            file_writer.write_checked_tables(
                sample_checked_tables,
                output_path,
                output_format="xml",  # type: ignore[arg-type]
            )

        assert "Unsupported format" in str(exc_info.value)
