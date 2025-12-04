"""ファイル出力リポジトリのインターフェース定義."""

from collections.abc import Sequence
from pathlib import Path
from typing import Literal, Protocol

from domain.entities.lineage import LeafTable
from domain.entities.table import CheckedTable


class FileWriterRepository(Protocol):
    """テーブル情報をファイルに出力するリポジトリのインターフェース."""

    def write_checked_tables(
        self,
        tables: Sequence[CheckedTable],
        output_path: Path,
        output_format: Literal["csv", "json"] = "csv",
    ) -> None:
        """CheckedTableをファイルに出力する.

        Args:
            tables: 出力対象のCheckedTableリスト
            output_path: 出力先ファイルパス
            output_format: 出力形式 ("csv" or "json")

        Raises:
            FileWriterError: ファイル出力に失敗した場合
        """
        ...

    def write_leaf_tables(
        self,
        tables: Sequence[LeafTable],
        output_path: Path,
        output_format: Literal["csv", "json"] = "csv",
    ) -> None:
        """LeafTableをファイルに出力する.

        Args:
            tables: 出力対象のLeafTableリスト
            output_path: 出力先ファイルパス
            output_format: 出力形式 ("csv" or "json")

        Raises:
            FileWriterError: ファイル出力に失敗した場合
        """
        ...
