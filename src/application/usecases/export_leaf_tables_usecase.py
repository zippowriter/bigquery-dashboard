"""リーフテーブルエクスポートユースケース."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from domain.repositories.file_writer_repository import FileWriterRepository
from domain.repositories.lineage_repository import LineageRepository
from domain.repositories.table_repository import TableRepository
from domain.value_objects.table_id import TableId


@dataclass
class ExportLeafTablesRequest:
    """エクスポートリクエスト.

    project_ids と root_tables は排他的に指定する。
    - project_ids: プロジェクト内の全テーブルからリーフを抽出
    - root_tables: 指定したルートテーブルから下流を辿ってリーフを抽出

    allowed_project_ids を指定すると、リネージ探索を許可されたプロジェクト内に制限する。
    """

    project_ids: Sequence[str] | None = None
    root_tables: Sequence[TableId] | None = None
    allowed_project_ids: Sequence[str] | None = None
    output_path: Path = Path("output/leaf_tables.csv")
    output_format: Literal["csv", "json"] = "csv"

    def __post_init__(self) -> None:
        """バリデーション."""
        if self.project_ids is None and self.root_tables is None:
            raise ValueError(
                "project_ids または root_tables のどちらかを指定してください"
            )
        if self.project_ids is not None and self.root_tables is not None:
            raise ValueError("project_ids と root_tables は同時に指定できません")


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
        if request.root_tables is not None:
            # ルートテーブルから下流を辿ってリーフを取得
            leaf_tables = self._lineage_repository.find_leaf_tables_from_roots(
                request.root_tables,
                allowed_project_ids=request.allowed_project_ids,
            )
            total_count = len(request.root_tables)
        else:
            # プロジェクト内の全テーブルからリーフを抽出
            # __post_init__のバリデーションにより、ここではproject_idsは必ずNoneではない
            assert request.project_ids is not None
            tables = self._table_repository.list_tables(request.project_ids)
            table_ids = [table.table_id for table in tables]
            leaf_tables = self._lineage_repository.get_leaf_tables(
                table_ids,
                allowed_project_ids=request.allowed_project_ids,
            )
            total_count = len(tables)

        # ファイルに出力
        self._file_writer.write_leaf_tables(
            leaf_tables,
            request.output_path,
            request.output_format,
        )

        return ExportLeafTablesResult(
            total_tables_count=total_count,
            leaf_tables_count=len(leaf_tables),
            output_path=request.output_path,
        )
