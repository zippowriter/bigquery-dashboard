"""キャッシュ付きリポジトリ実装。

CSVキャッシュとBigQueryリポジトリを組み合わせた複合リポジトリを提供する。
"""

from typing import Protocol

from src.shared.domain.logging import Logger
from src.shared.domain.models import TableInfo, TableUsage
from src.shared.infra.bigquery import BigQueryTableRepository
from src.shared.infra.csv_cache import CsvCacheRepository
from src.shared.logging_config import get_logger


class BigQueryRepositoryProtocol(Protocol):
    """BigQueryリポジトリのプロトコル。"""

    def fetch_tables(self, project_id: str) -> list[TableInfo]:
        """テーブル一覧を取得する。"""
        ...

    def fetch_usage_stats(self, project_id: str, region: str) -> list[TableUsage]:
        """利用統計を取得する。"""
        ...

    def fetch_all(
        self, project_id: str, region: str
    ) -> tuple[list[TableInfo], list[TableUsage]]:
        """テーブル一覧と利用統計を一括取得する。"""
        ...


class CachedTableRepository:
    """CSVキャッシュ優先のテーブルリポジトリ。

    キャッシュが存在すればCSVからデータを読み込み、
    存在しなければBigQuery APIから取得してキャッシュに保存する。
    """

    def __init__(
        self,
        csv_cache: CsvCacheRepository | None = None,
        bigquery_repo: BigQueryRepositoryProtocol | None = None,
        logger: Logger | None = None,
    ):
        """リポジトリを初期化する。

        Args:
            csv_cache: CSVキャッシュリポジトリ。Noneの場合はデフォルトを使用。
            bigquery_repo: BigQueryリポジトリ。Noneの場合はデフォルトを使用。
            logger: ロガーインスタンス（省略時はデフォルトロガーを使用）
        """
        self._csv_cache = csv_cache or CsvCacheRepository()
        self._bigquery_repo: BigQueryRepositoryProtocol = bigquery_repo or BigQueryTableRepository()
        self._logger = logger or get_logger()

    def has_cache(self) -> bool:
        """キャッシュが存在するかチェックする。

        Returns:
            キャッシュファイルが存在する場合True
        """
        return self._csv_cache.has_cache()

    def fetch_tables(self, project_id: str) -> list[TableInfo]:
        """テーブル一覧を取得する。

        キャッシュが存在すればCSVから、なければBigQuery APIから取得する。

        Args:
            project_id: GCPプロジェクトID

        Returns:
            テーブル情報のリスト
        """
        if self._csv_cache.has_cache():
            self._logger.debug("キャッシュヒット: テーブル一覧をCSVから取得")
            return self._csv_cache.fetch_tables(project_id)
        self._logger.debug("キャッシュミス: テーブル一覧をBigQuery APIから取得")
        return self._bigquery_repo.fetch_tables(project_id)

    def fetch_usage_stats(self, project_id: str, region: str) -> list[TableUsage]:
        """利用統計を取得する。

        キャッシュが存在すればCSVから、なければBigQuery APIから取得する。

        Args:
            project_id: GCPプロジェクトID
            region: BigQueryリージョン

        Returns:
            テーブル利用統計のリスト
        """
        if self._csv_cache.has_cache():
            self._logger.debug("キャッシュヒット: 利用統計をCSVから取得")
            return self._csv_cache.fetch_usage_stats(project_id, region)
        self._logger.debug("キャッシュミス: 利用統計をBigQuery APIから取得")
        return self._bigquery_repo.fetch_usage_stats(project_id, region)

    def refresh(self, project_id: str, region: str) -> tuple[list[TableInfo], list[TableUsage]]:
        """BigQueryからデータを再取得してCSVに保存する。

        Args:
            project_id: GCPプロジェクトID
            region: BigQueryリージョン

        Returns:
            (テーブル一覧, 利用統計) のタプル
        """
        self._logger.info("データリフレッシュ開始", project_id=project_id, region=region)
        tables, usage_stats = self._bigquery_repo.fetch_all(project_id, region)
        self._csv_cache.save_tables(tables)
        self._csv_cache.save_usage_stats(usage_stats)
        self._logger.info("データリフレッシュ完了", tables_count=len(tables), usage_count=len(usage_stats))
        return tables, usage_stats

    def clear_cache(self) -> None:
        """キャッシュを削除する。"""
        self._csv_cache.clear_cache()
