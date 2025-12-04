"""テーブル参照回数エクスポートユースケース."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from domain.repositories.file_writer_repository import FileWriterRepository
from domain.repositories.table_repository import TableRepository


@dataclass
class ExportReferenceCountRequest:
    """エクスポートリクエスト."""

    project_ids: Sequence[str]
    days_back: int = 90
    output_path: Path = Path("output/reference_counts.csv")
    output_format: Literal["csv", "json"] = "csv"


@dataclass
class ExportReferenceCountResult:
    """エクスポート結果."""

    tables_count: int
    output_path: Path


class ExportReferenceCountUseCase:
    """テーブル参照回数をファイルにエクスポートするユースケース."""

    def __init__(
        self,
        table_repository: TableRepository,
        file_writer: FileWriterRepository,
    ) -> None:
        """初期化.

        Args:
            table_repository: テーブルリポジトリ
            file_writer: ファイル出力リポジトリ
        """
        self._table_repository = table_repository
        self._file_writer = file_writer

    def execute(
        self,
        request: ExportReferenceCountRequest,
    ) -> ExportReferenceCountResult:
        """テーブル参照回数を取得してファイルに出力する.

        Args:
            request: エクスポートリクエスト

        Returns:
            エクスポート結果

        Raises:
            TableRepositoryError: テーブル情報取得に失敗した場合
            FileWriterError: ファイル出力に失敗した場合
        """
        # 1. テーブル一覧を取得
        tables = self._table_repository.list_tables(request.project_ids)

        # 2. 参照回数を取得
        checked_tables = self._table_repository.get_table_reference_counts(
            tables,
            days_back=request.days_back,
        )

        # 3. ファイルに出力
        self._file_writer.write_checked_tables(
            checked_tables,
            request.output_path,
            request.output_format,
        )

        return ExportReferenceCountResult(
            tables_count=len(checked_tables),
            output_path=request.output_path,
        )
