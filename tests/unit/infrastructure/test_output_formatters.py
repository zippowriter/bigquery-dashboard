"""出力フォーマッターのテスト。

ConsoleFormatter, CsvFormatter, JsonFormatter, OutputFormatterProtocol の
動作を検証する。
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from bq_table_reference.domain.models import (
    DataSource,
    TableAccessCount,
    TableAccessResult,
)


def _create_sample_result() -> TableAccessResult:
    """テスト用の TableAccessResult を生成する。"""
    return TableAccessResult(
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
        project_id="my-project",
        info_schema_results=[
            TableAccessCount(
                project_id="my-project",
                dataset_id="dataset1",
                table_id="table_a",
                access_count=100,
                source=DataSource.INFORMATION_SCHEMA,
            ),
            TableAccessCount(
                project_id="my-project",
                dataset_id="dataset1",
                table_id="table_b",
                access_count=50,
                source=DataSource.INFORMATION_SCHEMA,
            ),
        ],
        audit_log_results=[
            TableAccessCount(
                project_id="my-project",
                dataset_id="dataset2",
                table_id="table_c",
                access_count=30,
                source=DataSource.AUDIT_LOG,
            ),
        ],
        merged_results=[
            TableAccessCount(
                project_id="my-project",
                dataset_id="dataset1",
                table_id="table_a",
                access_count=100,
                source=DataSource.INFORMATION_SCHEMA,
            ),
            TableAccessCount(
                project_id="my-project",
                dataset_id="dataset1",
                table_id="table_b",
                access_count=50,
                source=DataSource.INFORMATION_SCHEMA,
            ),
            TableAccessCount(
                project_id="my-project",
                dataset_id="dataset2",
                table_id="table_c",
                access_count=30,
                source=DataSource.AUDIT_LOG,
            ),
        ],
        warnings=[],
    )


def _create_result_with_warnings() -> TableAccessResult:
    """警告付きの TableAccessResult を生成する。"""
    return TableAccessResult(
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
        project_id="my-project",
        info_schema_results=[],
        audit_log_results=[],
        merged_results=[
            TableAccessCount(
                project_id="my-project",
                dataset_id="dataset1",
                table_id="table_a",
                access_count=10,
                source=DataSource.INFORMATION_SCHEMA,
            ),
        ],
        warnings=["Warning: 期間が180日を超えています", "Warning: Audit Logが無効です"],
    )


class TestConsoleFormatter:
    """ConsoleFormatter のテスト。"""

    def test_format_returns_string(self) -> None:
        """ConsoleFormatter.format() が文字列を返すことを検証する。"""
        from bq_table_reference.infrastructure.output_formatters import (
            ConsoleFormatter,
        )

        formatter = ConsoleFormatter()
        result = _create_sample_result()

        output = formatter.format(result)

        assert isinstance(output, str)
        assert len(output) > 0

    def test_format_sorted_by_access_count_descending(self) -> None:
        """結果が参照回数の降順でソートされていることを検証する。"""
        from bq_table_reference.infrastructure.output_formatters import (
            ConsoleFormatter,
        )

        formatter = ConsoleFormatter()
        result = _create_sample_result()

        output = formatter.format(result)

        # table_a (100) が table_b (50) より先に出現することを確認
        table_a_pos = output.find("table_a")
        table_b_pos = output.find("table_b")
        table_c_pos = output.find("table_c")

        assert table_a_pos < table_b_pos < table_c_pos

    def test_format_contains_required_columns(self) -> None:
        """出力に必要なカラム情報が含まれることを検証する。"""
        from bq_table_reference.infrastructure.output_formatters import (
            ConsoleFormatter,
        )

        formatter = ConsoleFormatter()
        result = _create_sample_result()

        output = formatter.format(result)

        # ヘッダーまたは値としてカラム名が含まれる
        assert "project" in output.lower() or "my-project" in output
        assert "dataset" in output.lower() or "dataset1" in output
        assert "table" in output.lower() or "table_a" in output
        assert "100" in output  # access_count
        assert "information_schema" in output or "info_schema" in output.lower()

    def test_format_shows_warnings_first(self) -> None:
        """警告がある場合、先頭に表示されることを検証する。"""
        from bq_table_reference.infrastructure.output_formatters import (
            ConsoleFormatter,
        )

        formatter = ConsoleFormatter()
        result = _create_result_with_warnings()

        output = formatter.format(result)

        # 警告メッセージがテーブルデータより前に出現
        warning_pos = output.find("Warning")
        table_pos = output.find("table_a")

        assert warning_pos != -1
        assert warning_pos < table_pos

    def test_format_empty_result(self) -> None:
        """結果が空の場合でもエラーにならないことを検証する。"""
        from bq_table_reference.infrastructure.output_formatters import (
            ConsoleFormatter,
        )

        formatter = ConsoleFormatter()
        result = TableAccessResult(
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc),
            project_id="my-project",
            merged_results=[],
        )

        output = formatter.format(result)

        assert isinstance(output, str)


class TestCsvFormatter:
    """CsvFormatter のテスト。"""

    def test_format_returns_csv_string(self) -> None:
        """CsvFormatter.format() が CSV 形式の文字列を返すことを検証する。"""
        from bq_table_reference.infrastructure.output_formatters import CsvFormatter

        formatter = CsvFormatter()
        result = _create_sample_result()

        output = formatter.format(result)

        assert isinstance(output, str)
        lines = output.strip().split("\n")
        assert len(lines) >= 2  # ヘッダー + データ行

    def test_format_has_correct_header(self) -> None:
        """ヘッダー行が正しいカラム名を含むことを検証する。"""
        from bq_table_reference.infrastructure.output_formatters import CsvFormatter

        formatter = CsvFormatter()
        result = _create_sample_result()

        output = formatter.format(result)

        header_line = output.strip().split("\n")[0]
        assert "project_id" in header_line
        assert "dataset_id" in header_line
        assert "table_id" in header_line
        assert "access_count" in header_line
        assert "source" in header_line

    def test_format_data_rows(self) -> None:
        """データ行が正しい値を含むことを検証する。"""
        from bq_table_reference.infrastructure.output_formatters import CsvFormatter

        formatter = CsvFormatter()
        result = _create_sample_result()

        output = formatter.format(result)

        lines = output.strip().split("\n")
        # 最初のデータ行 (table_a, access_count=100)
        data_line = lines[1]
        assert "my-project" in data_line
        assert "dataset1" in data_line
        assert "table_a" in data_line
        assert "100" in data_line

    def test_write_to_file(self) -> None:
        """ファイルに書き出せることを検証する。"""
        from bq_table_reference.infrastructure.output_formatters import CsvFormatter

        formatter = CsvFormatter()
        result = _create_sample_result()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.csv"
            formatter.write_to_file(result, output_path)

            assert output_path.exists()
            content = output_path.read_text()
            assert "project_id" in content
            assert "table_a" in content

    def test_write_to_file_creates_parent_directories(self) -> None:
        """親ディレクトリが存在しない場合、作成されることを検証する。"""
        from bq_table_reference.infrastructure.output_formatters import CsvFormatter

        formatter = CsvFormatter()
        result = _create_sample_result()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "output.csv"
            formatter.write_to_file(result, output_path)

            assert output_path.exists()


class TestJsonFormatter:
    """JsonFormatter のテスト。"""

    def test_format_returns_json_string(self) -> None:
        """JsonFormatter.format() が JSON 形式の文字列を返すことを検証する。"""
        from bq_table_reference.infrastructure.output_formatters import JsonFormatter

        formatter = JsonFormatter()
        result = _create_sample_result()

        output = formatter.format(result)

        # 有効な JSON であることを確認
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_format_contains_required_fields(self) -> None:
        """JSON に集計期間、project_id、warnings、table_accesses が含まれることを検証する。"""
        from bq_table_reference.infrastructure.output_formatters import JsonFormatter

        formatter = JsonFormatter()
        result = _create_sample_result()

        output = formatter.format(result)
        parsed = json.loads(output)

        assert "start_date" in parsed
        assert "end_date" in parsed
        assert "project_id" in parsed
        assert "warnings" in parsed
        assert "table_accesses" in parsed

    def test_format_table_accesses_structure(self) -> None:
        """table_accesses の各エントリが正しい構造を持つことを検証する。"""
        from bq_table_reference.infrastructure.output_formatters import JsonFormatter

        formatter = JsonFormatter()
        result = _create_sample_result()

        output = formatter.format(result)
        parsed = json.loads(output)

        accesses = parsed["table_accesses"]
        assert len(accesses) == 3  # merged_results の数

        first_access = accesses[0]
        assert "project_id" in first_access
        assert "dataset_id" in first_access
        assert "table_id" in first_access
        assert "access_count" in first_access
        assert "source" in first_access

    def test_write_to_file(self) -> None:
        """ファイルに書き出せることを検証する。"""
        from bq_table_reference.infrastructure.output_formatters import JsonFormatter

        formatter = JsonFormatter()
        result = _create_sample_result()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.json"
            formatter.write_to_file(result, output_path)

            assert output_path.exists()
            content = json.loads(output_path.read_text())
            assert content["project_id"] == "my-project"

    def test_format_with_warnings(self) -> None:
        """警告がある場合、JSON に含まれることを検証する。"""
        from bq_table_reference.infrastructure.output_formatters import JsonFormatter

        formatter = JsonFormatter()
        result = _create_result_with_warnings()

        output = formatter.format(result)
        parsed = json.loads(output)

        assert len(parsed["warnings"]) == 2
        assert "180日" in parsed["warnings"][0]


class TestOutputFormatterProtocol:
    """OutputFormatter Protocol のテスト。"""

    def test_console_formatter_satisfies_protocol(self) -> None:
        """ConsoleFormatter が OutputFormatter Protocol を満たすことを検証する。"""
        from bq_table_reference.infrastructure.output_formatters import (
            ConsoleFormatter,
            OutputFormatter,
        )

        formatter: OutputFormatter = ConsoleFormatter()
        result = _create_sample_result()

        # Protocol のメソッドが呼び出せる
        output = formatter.format(result)
        assert isinstance(output, str)

    def test_csv_formatter_satisfies_protocol(self) -> None:
        """CsvFormatter が OutputFormatter Protocol を満たすことを検証する。"""
        from bq_table_reference.infrastructure.output_formatters import (
            CsvFormatter,
            OutputFormatter,
        )

        formatter: OutputFormatter = CsvFormatter()
        result = _create_sample_result()

        output = formatter.format(result)
        assert isinstance(output, str)

    def test_json_formatter_satisfies_protocol(self) -> None:
        """JsonFormatter が OutputFormatter Protocol を満たすことを検証する。"""
        from bq_table_reference.infrastructure.output_formatters import (
            JsonFormatter,
            OutputFormatter,
        )

        formatter: OutputFormatter = JsonFormatter()
        result = _create_sample_result()

        output = formatter.format(result)
        assert isinstance(output, str)

    def test_protocol_format_method_signature(self) -> None:
        """OutputFormatter.format() のシグネチャが正しいことを検証する。"""
        from typing import get_type_hints

        from bq_table_reference.infrastructure.output_formatters import OutputFormatter

        hints = get_type_hints(OutputFormatter.format)

        # 引数に result がある
        assert "result" in hints
        # 戻り値が str
        assert hints["return"] is str
