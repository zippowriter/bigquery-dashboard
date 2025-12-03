"""CSVファイルキャッシュリポジトリ。

テーブル情報と利用統計をCSVファイルに保存・読み込みする。
"""

import csv
import tempfile
from pathlib import Path

from src.shared.domain.logging import Logger
from src.shared.domain.models import TableInfo, TableUsage
from src.shared.logging_config import get_logger


class CsvCacheRepository:
    """CSVファイルをキャッシュとして使用するリポジトリ。

    一時ディレクトリにCSVファイルを保存し、起動時間を短縮する。
    """

    def __init__(self, cache_dir: Path | None = None, logger: Logger | None = None):
        """リポジトリを初期化する。

        Args:
            cache_dir: キャッシュディレクトリ。Noneの場合は一時ディレクトリを使用。
            logger: ロガーインスタンス（省略時はデフォルトロガーを使用）
        """
        self._cache_dir = cache_dir or Path(tempfile.gettempdir()) / "bigquery-dashboard"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._logger = logger or get_logger()

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
        self._logger.debug("テーブルキャッシュ読み込み開始", path=str(self.tables_cache_path))
        if not self.tables_cache_path.exists():
            self._logger.warning("キャッシュファイル未存在", path=str(self.tables_cache_path))
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
        self._logger.debug("テーブルキャッシュ読み込み完了", count=len(tables))
        return tables

    def fetch_usage_stats(self, project_id: str, region: str) -> list[TableUsage]:
        """CSVから利用統計を読み込む。

        Args:
            project_id: GCPプロジェクトID（互換性のため、実際には使用しない）
            region: BigQueryリージョン（互換性のため、実際には使用しない）

        Returns:
            テーブル利用統計のリスト。キャッシュファイルが存在しない場合は空リスト。
        """
        self._logger.debug("利用統計キャッシュ読み込み開始", path=str(self.usage_cache_path))
        if not self.usage_cache_path.exists():
            self._logger.debug("利用統計キャッシュファイル未存在", path=str(self.usage_cache_path))
            return []

        usage_stats: list[TableUsage] = []
        with self.usage_cache_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # is_leafフィールドは後方互換性のためオプション扱い
                is_leaf_str = row.get("is_leaf", "").lower()
                is_leaf = is_leaf_str in ("true", "1", "yes")
                usage_stats.append(
                    TableUsage(
                        dataset_id=row["dataset_id"],
                        table_id=row["table_id"],
                        reference_count=int(row["reference_count"]),
                        unique_users=int(row["unique_users"]),
                        is_leaf=is_leaf,
                    )
                )
        self._logger.debug("利用統計キャッシュ読み込み完了", count=len(usage_stats))
        return usage_stats

    def save_tables(self, tables: list[TableInfo]) -> None:
        """テーブル一覧をCSVに保存する。

        Args:
            tables: 保存するテーブル情報のリスト
        """
        self._logger.debug("テーブルキャッシュ保存開始", path=str(self.tables_cache_path), count=len(tables))
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
        self._logger.info("テーブルキャッシュ保存完了", count=len(tables))

    def save_usage_stats(self, usage_stats: list[TableUsage]) -> None:
        """利用統計をCSVに保存する。

        Args:
            usage_stats: 保存する利用統計のリスト
        """
        self._logger.debug("利用統計キャッシュ保存開始", path=str(self.usage_cache_path), count=len(usage_stats))
        with self.usage_cache_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["dataset_id", "table_id", "reference_count", "unique_users", "is_leaf"]
            )
            writer.writeheader()
            for usage in usage_stats:
                writer.writerow(
                    {
                        "dataset_id": usage.dataset_id,
                        "table_id": usage.table_id,
                        "reference_count": usage.reference_count,
                        "unique_users": usage.unique_users,
                        "is_leaf": str(usage.is_leaf).lower(),
                    }
                )
        self._logger.info("利用統計キャッシュ保存完了", count=len(usage_stats))

    def clear_cache(self) -> None:
        """キャッシュファイルを削除する。"""
        self._logger.info("キャッシュクリア開始", cache_dir=str(self._cache_dir))
        if self.tables_cache_path.exists():
            self.tables_cache_path.unlink()
        if self.usage_cache_path.exists():
            self.usage_cache_path.unlink()
        self._logger.info("キャッシュクリア完了")
