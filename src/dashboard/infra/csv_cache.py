"""CSVファイルキャッシュリポジトリ。

テーブル情報と利用統計をCSVファイルに保存・読み込みする。
"""

import csv
import tempfile
from pathlib import Path

from src.dashboard.domain.models import TableInfo, TableUsage


class CsvCacheRepository:
    """CSVファイルをキャッシュとして使用するリポジトリ。

    一時ディレクトリにCSVファイルを保存し、起動時間を短縮する。
    """

    def __init__(self, cache_dir: Path | None = None):
        """リポジトリを初期化する。

        Args:
            cache_dir: キャッシュディレクトリ。Noneの場合は一時ディレクトリを使用。
        """
        self._cache_dir = cache_dir or Path(tempfile.gettempdir()) / "bigquery-dashboard"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def tables_cache_path(self) -> Path:
        """テーブル一覧キャッシュファイルのパス。"""
        return self._cache_dir / "tables.csv"

    @property
    def usage_cache_path(self) -> Path:
        """利用統計キャッシュファイルのパス。"""
        return self._cache_dir / "usage_stats.csv"

    def has_cache(self) -> bool:
        """キャッシュファイルが存在するかチェックする。

        Returns:
            テーブルキャッシュファイルが存在する場合True
        """
        return self.tables_cache_path.exists()

    def fetch_tables(self, project_id: str) -> list[TableInfo]:
        """CSVからテーブル一覧を読み込む。

        Args:
            project_id: GCPプロジェクトID（互換性のため、実際には使用しない）

        Returns:
            テーブル情報のリスト

        Raises:
            FileNotFoundError: キャッシュファイルが存在しない場合
        """
        if not self.tables_cache_path.exists():
            raise FileNotFoundError(f"キャッシュファイルが存在しません: {self.tables_cache_path}")

        tables: list[TableInfo] = []
        with self.tables_cache_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tables.append(
                    TableInfo(
                        dataset_id=row["dataset_id"],
                        table_id=row["table_id"],
                    )
                )
        return tables

    def fetch_usage_stats(self, project_id: str, region: str) -> list[TableUsage]:
        """CSVから利用統計を読み込む。

        Args:
            project_id: GCPプロジェクトID（互換性のため、実際には使用しない）
            region: BigQueryリージョン（互換性のため、実際には使用しない）

        Returns:
            テーブル利用統計のリスト。キャッシュファイルが存在しない場合は空リスト。
        """
        if not self.usage_cache_path.exists():
            return []

        usage_stats: list[TableUsage] = []
        with self.usage_cache_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                usage_stats.append(
                    TableUsage(
                        dataset_id=row["dataset_id"],
                        table_id=row["table_id"],
                        reference_count=int(row["reference_count"]),
                        unique_users=int(row["unique_users"]),
                    )
                )
        return usage_stats

    def save_tables(self, tables: list[TableInfo]) -> None:
        """テーブル一覧をCSVに保存する。

        Args:
            tables: 保存するテーブル情報のリスト
        """
        with self.tables_cache_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["dataset_id", "table_id"])
            writer.writeheader()
            for table in tables:
                writer.writerow(
                    {
                        "dataset_id": table.dataset_id,
                        "table_id": table.table_id,
                    }
                )

    def save_usage_stats(self, usage_stats: list[TableUsage]) -> None:
        """利用統計をCSVに保存する。

        Args:
            usage_stats: 保存する利用統計のリスト
        """
        with self.usage_cache_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["dataset_id", "table_id", "reference_count", "unique_users"]
            )
            writer.writeheader()
            for usage in usage_stats:
                writer.writerow(
                    {
                        "dataset_id": usage.dataset_id,
                        "table_id": usage.table_id,
                        "reference_count": usage.reference_count,
                        "unique_users": usage.unique_users,
                    }
                )

    def clear_cache(self) -> None:
        """キャッシュファイルを削除する。"""
        if self.tables_cache_path.exists():
            self.tables_cache_path.unlink()
        if self.usage_cache_path.exists():
            self.usage_cache_path.unlink()
