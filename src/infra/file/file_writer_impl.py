"""ファイル出力リポジトリの実装."""

from collections.abc import Sequence
from pathlib import Path
from typing import Literal

import pandas as pd

from domain.entities.lineage import LeafTable
from domain.entities.table import CheckedTable
from infra.file.exceptions import FileWriterError


class PandasFileWriter:
    """pandasを使用したファイル出力リポジトリ実装."""

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
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            df = pd.DataFrame(
                [
                    {
                        "project_id": t.table_id.project_id,
                        "dataset_id": t.table_id.dataset_id,
                        "table_id": t.table_id.table_id,
                        "table_type": t.table_type,
                        "job_count": t.job_count,
                        "unique_user": t.unique_user,
                    }
                    for t in tables
                ]
            )

            self._write_dataframe(df, output_path, output_format)

        except OSError as e:
            raise FileWriterError(
                f"Failed to write file: {output_path}",
                cause=e,
            ) from e

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
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            df = pd.DataFrame(
                [
                    {
                        "project_id": t.table_id.project_id,
                        "dataset_id": t.table_id.dataset_id,
                        "table_id": t.table_id.table_id,
                        "fqn": f"{t.table_id.project_id}.{t.table_id.dataset_id}.{t.table_id.table_id}",
                        "upstream_count": t.upstream_count,
                    }
                    for t in tables
                ]
            )

            self._write_dataframe(df, output_path, output_format)

        except OSError as e:
            raise FileWriterError(
                f"Failed to write file: {output_path}",
                cause=e,
            ) from e

    def _write_dataframe(
        self,
        df: pd.DataFrame,
        output_path: Path,
        output_format: Literal["csv", "json"],
    ) -> None:
        """DataFrameをファイルに出力する共通処理.

        Args:
            df: 出力対象のDataFrame
            output_path: 出力先ファイルパス
            output_format: 出力形式 ("csv" or "json")

        Raises:
            FileWriterError: サポートされていない形式の場合
        """
        if output_format == "csv":
            df.to_csv(output_path, index=False, encoding="utf-8")
        elif output_format == "json":
            df.to_json(
                output_path,
                orient="records",
                force_ascii=False,
                indent=2,
            )
        else:
            raise FileWriterError(f"Unsupported format: {output_format}")
