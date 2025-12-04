"""リーフテーブルエクスポートユースケース."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from domain.repositories.file_writer_repository import FileWriterRepository
from domain.repositories.lineage_repository import LineageRepository
from domain.repositories.table_repository import TableRepository


@dataclass
class ExportLeafTablesRequest:
    """エクスポートリクエスト."""

    project_ids: Sequence[str]
    output_path: Path = Path("output/leaf_tables.csv")
    output_format: Literal["csv", "json"] = "csv"


@dataclass
class ExportLeafTablesResult:
    """エクスポート結果."""

    total_tables_count: int
    leaf_tables_count: int
    output_path: Path


class ExportLeafTablesUseCase:
    """リーフテーブルをファイルにエクスポートするユースケース.

    リーフテーブル = 下流に他のテーブルを持たないテーブル（最終的なアウトプット）
    """

    def __init__(
        self,
        table_repository: TableRepository,
        lineage_repository: LineageRepository,
        file_writer: FileWriterRepository,
    ) -> None:
        """初期化.

        Args:
            table_repository: テーブルリポジトリ
            lineage_repository: リネージリポジトリ
            file_writer: ファイル出力リポジトリ
        """
        self._table_repository = table_repository
        self._lineage_repository = lineage_repository
        self._file_writer = file_writer

    def execute(
        self,
        request: ExportLeafTablesRequest,
    ) -> ExportLeafTablesResult:
        """リーフテーブルを取得してファイルに出力する.

        Args:
            request: エクスポートリクエスト

        Returns:
            エクスポート結果

        Raises:
            TableRepositoryError: テーブル情報取得に失敗した場合
            LineageRepositoryError: リネージ情報取得に失敗した場合
            FileWriterError: ファイル出力に失敗した場合
        """
        # 1. テーブル一覧を取得
        tables = self._table_repository.list_tables(request.project_ids)

        # 2. テーブルIDのリストを作成
        table_ids = [table.table_id for table in tables]

        # 3. リーフテーブルを特定
        leaf_tables = self._lineage_repository.get_leaf_tables(table_ids)

        # 4. ファイルに出力
        self._file_writer.write_leaf_tables(
            leaf_tables,
            request.output_path,
            request.output_format,
        )

        return ExportLeafTablesResult(
            total_tables_count=len(tables),
            leaf_tables_count=len(leaf_tables),
            output_path=request.output_path,
        )
