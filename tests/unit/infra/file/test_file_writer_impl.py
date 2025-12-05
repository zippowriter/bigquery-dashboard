"""PandasFileWriterのユニットテスト."""

import json
from pathlib import Path

import pytest

from domain.entities.analyzed_table import AnalyzedTable
from domain.entities.table import Table
from domain.value_objects.table_id import TableId
from domain.value_objects.usage_info import UsageInfo
from infra.file.exceptions import FileWriterError
from infra.file.file_writer_impl import PandasFileWriter


@pytest.fixture
def file_writer() -> PandasFileWriter:
    """PandasFileWriterのフィクスチャ."""
    return PandasFileWriter()


@pytest.fixture
def sample_analyzed_tables() -> list[AnalyzedTable]:
    """テスト用のAnalyzedTableリスト."""
    table1 = Table(
        table_id=TableId(
            project_id="project-a",
            dataset_id="dataset1",
            table_id="table1",
        ),
        table_type="BASE TABLE",
    )
    table2 = Table(
        table_id=TableId(
            project_id="project-a",
            dataset_id="dataset1",
            table_id="table2",
        ),
        table_type="VIEW",
    )
    return [
        AnalyzedTable(
            table=table1,
            usage_info=UsageInfo(job_count=100, unique_user=5),
        ),
        AnalyzedTable(
            table=table2,
            usage_info=UsageInfo(job_count=50, unique_user=3),
        ),
    ]


class TestPandasFileWriter:
    """PandasFileWriterのテストクラス."""

    def test_write_analyzed_tables_csv(
        self,
        file_writer: PandasFileWriter,
        sample_analyzed_tables: list[AnalyzedTable],
        tmp_path: Path,
    ) -> None:
        """CSV形式で出力できることを確認."""
        output_path = tmp_path / "output.csv"

        file_writer.write_analyzed_tables(
            sample_analyzed_tables,
            output_path,
            output_format="csv",
        )

        assert output_path.exists()
        content = output_path.read_text()
        lines = content.strip().split("\n")

        assert len(lines) == 3  # ヘッダー + 2行
        assert "project_id" in lines[0]
        assert "project-a" in lines[1]

    def test_write_analyzed_tables_json(
        self,
        file_writer: PandasFileWriter,
        sample_analyzed_tables: list[AnalyzedTable],
        tmp_path: Path,
    ) -> None:
        """JSON形式で出力できることを確認."""
        output_path = tmp_path / "output.json"

        file_writer.write_analyzed_tables(
            sample_analyzed_tables,
            output_path,
            output_format="json",
        )

        assert output_path.exists()
        data = json.loads(output_path.read_text())

        assert len(data) == 2
        assert data[0]["project_id"] == "project-a"
        assert data[0]["job_count"] == 100

    def test_write_analyzed_tables_creates_parent_directory(
        self,
        file_writer: PandasFileWriter,
        sample_analyzed_tables: list[AnalyzedTable],
        tmp_path: Path,
    ) -> None:
        """親ディレクトリが存在しない場合に作成されることを確認."""
        output_path = tmp_path / "nested" / "dir" / "output.csv"

        file_writer.write_analyzed_tables(
            sample_analyzed_tables,
            output_path,
            output_format="csv",
        )

        assert output_path.exists()

    def test_write_analyzed_tables_empty_list(
        self,
        file_writer: PandasFileWriter,
        tmp_path: Path,
    ) -> None:
        """空のリストでもファイルが作成されることを確認."""
        output_path = tmp_path / "empty.csv"

        file_writer.write_analyzed_tables(
            [],
            output_path,
            output_format="csv",
        )

        assert output_path.exists()

    def test_write_analyzed_tables_unsupported_format(
        self,
        file_writer: PandasFileWriter,
        sample_analyzed_tables: list[AnalyzedTable],
        tmp_path: Path,
    ) -> None:
        """サポートされていない形式の場合にエラーが発生することを確認."""
        output_path = tmp_path / "output.xml"

        with pytest.raises(FileWriterError) as exc_info:
            file_writer.write_analyzed_tables(
                sample_analyzed_tables,
                output_path,
                output_format="xml",  # type: ignore[arg-type]
            )

        assert "Unsupported format" in str(exc_info.value)
