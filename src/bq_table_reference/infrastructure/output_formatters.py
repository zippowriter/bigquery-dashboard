"""出力フォーマッター。

TableAccessResult を様々な形式で出力するフォーマッタークラス群。
"""

import csv
import io
import json
from pathlib import Path
from typing import Protocol

from bq_table_reference.domain.models import TableAccessCount, TableAccessResult


class OutputFormatter(Protocol):
    """出力フォーマッターの共通 Protocol。

    全ての出力フォーマッターはこの Protocol を満たす必要がある。
    """

    def format(self, result: TableAccessResult) -> str:
        """結果をフォーマットして文字列として返す。

        Args:
            result: 集計結果

        Returns:
            フォーマット済み文字列
        """
        ...


class ConsoleFormatter:
    """コンソール出力用フォーマッター。

    TableAccessResult を表形式の文字列としてフォーマットする。
    """

    def format(self, result: TableAccessResult) -> str:
        """結果を表形式の文字列としてフォーマットする。

        参照回数の降順でソートして出力する。
        警告がある場合は先頭に表示する。

        Args:
            result: 集計結果

        Returns:
            フォーマット済み文字列
        """
        output_lines: list[str] = []

        # 警告を先頭に表示
        if result.warnings:
            for warning in result.warnings:
                output_lines.append(f"[WARNING] {warning}")
            output_lines.append("")  # 空行

        # ヘッダー
        output_lines.append(self._format_header())
        output_lines.append(self._format_separator())

        # データ行（参照回数の降順でソート）
        sorted_results = sorted(
            result.merged_results,
            key=lambda x: x.access_count,
            reverse=True,
        )

        for access in sorted_results:
            output_lines.append(self._format_row(access))

        return "\n".join(output_lines)

    def _format_header(self) -> str:
        """ヘッダー行をフォーマットする。"""
        return (
            f"{'project_id':<20} | "
            f"{'dataset_id':<20} | "
            f"{'table_id':<30} | "
            f"{'access_count':>12} | "
            f"{'source':<20}"
        )

    def _format_separator(self) -> str:
        """区切り線をフォーマットする。"""
        return "-" * 112

    def _format_row(self, access: TableAccessCount) -> str:
        """データ行をフォーマットする。"""
        return (
            f"{access.project_id:<20} | "
            f"{access.dataset_id:<20} | "
            f"{access.table_id:<30} | "
            f"{access.access_count:>12} | "
            f"{access.source.value:<20}"
        )


class CsvFormatter:
    """CSV 出力用フォーマッター。

    TableAccessResult を CSV 形式でフォーマットする。
    """

    def format(self, result: TableAccessResult) -> str:
        """結果を CSV 形式の文字列としてフォーマットする。

        Args:
            result: 集計結果

        Returns:
            CSV フォーマット済み文字列
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # ヘッダー行
        writer.writerow(
            ["project_id", "dataset_id", "table_id", "access_count", "source"]
        )

        # データ行（参照回数の降順でソート）
        sorted_results = sorted(
            result.merged_results,
            key=lambda x: x.access_count,
            reverse=True,
        )

        for access in sorted_results:
            writer.writerow(
                [
                    access.project_id,
                    access.dataset_id,
                    access.table_id,
                    access.access_count,
                    access.source.value,
                ]
            )

        return output.getvalue()

    def write_to_file(self, result: TableAccessResult, path: Path) -> None:
        """結果を CSV ファイルとして書き出す。

        Args:
            result: 集計結果
            path: 出力先パス
        """
        # 親ディレクトリを作成
        path.parent.mkdir(parents=True, exist_ok=True)

        content = self.format(result)
        path.write_text(content, encoding="utf-8")


class JsonFormatter:
    """JSON 出力用フォーマッター。

    TableAccessResult を JSON 形式でフォーマットする。
    """

    def format(self, result: TableAccessResult) -> str:
        """結果を JSON 形式の文字列としてフォーマットする。

        Args:
            result: 集計結果

        Returns:
            JSON フォーマット済み文字列
        """
        # テーブルアクセス情報を辞書のリストに変換
        table_accesses: list[dict[str, str | int]] = [
            {
                "project_id": access.project_id,
                "dataset_id": access.dataset_id,
                "table_id": access.table_id,
                "access_count": access.access_count,
                "source": access.source.value,
            }
            for access in result.merged_results
        ]

        output_dict: dict[str, str | list[str] | list[dict[str, str | int]]] = {
            "start_date": result.start_date.isoformat(),
            "end_date": result.end_date.isoformat(),
            "project_id": result.project_id,
            "warnings": result.warnings,
            "table_accesses": table_accesses,
        }

        return json.dumps(output_dict, ensure_ascii=False, indent=2)

    def write_to_file(self, result: TableAccessResult, path: Path) -> None:
        """結果を JSON ファイルとして書き出す。

        Args:
            result: 集計結果
            path: 出力先パス
        """
        # 親ディレクトリを作成
        path.parent.mkdir(parents=True, exist_ok=True)

        content = self.format(result)
        path.write_text(content, encoding="utf-8")
