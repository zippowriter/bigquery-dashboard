"""バッチ処理ランナー。

BigQueryからデータを取得し、CSVキャッシュに保存する。
"""

from src.batch.config import BatchConfig
from src.shared.domain.logging import Logger
from src.shared.domain.services import TableUsageService
from src.shared.infra.bigquery import BigQueryTableRepository
from src.shared.infra.csv_cache import CsvCacheRepository
from src.shared.infra.lineage import LineageRepository
from src.shared.logging_config import get_logger


class BatchRunner:
    """バッチ処理の実行クラス。

    BigQueryからテーブル情報と利用統計を取得し、
    Lineage APIでリーフテーブルを特定してCSVに保存する。
    """

    def __init__(
        self,
        config: BatchConfig,
        bigquery_repo: BigQueryTableRepository | None = None,
        csv_cache: CsvCacheRepository | None = None,
        lineage_repo: LineageRepository | None = None,
        logger: Logger | None = None,
    ) -> None:
        """バッチランナーを初期化する。

        Args:
            config: バッチ設定
            bigquery_repo: BigQueryリポジトリ（省略時はデフォルトを使用）
            csv_cache: CSVキャッシュリポジトリ（省略時はデフォルトを使用）
            lineage_repo: Lineageリポジトリ（省略時はデフォルトを使用）
            logger: ロガー（省略時はデフォルトを使用）
        """
        self._config = config
        self._bigquery_repo = bigquery_repo or BigQueryTableRepository()
        self._csv_cache = csv_cache or CsvCacheRepository(cache_dir=config.cache_dir)
        self._lineage_repo = lineage_repo or LineageRepository()
        self._logger = logger or get_logger()

    def run(self) -> None:
        """バッチ処理を実行する。

        1. BigQueryからテーブル一覧と利用統計を取得
        2. データを結合
        3. Lineage APIでリーフテーブルを特定
        4. CSVキャッシュに保存
        """
        self._logger.info(
            "バッチ処理開始",
            project_id=self._config.project_id,
            region=self._config.region,
        )

        if not self._config.project_id:
            self._logger.error("project_idが設定されていません")
            raise ValueError("project_idが設定されていません")

        # 1. BigQueryからデータ取得
        self._logger.info("BigQueryからデータ取得中")
        tables = self._bigquery_repo.fetch_tables(self._config.project_id)
        usage_stats = self._bigquery_repo.fetch_usage_stats(
            self._config.project_id, self._config.region
        )
        self._logger.info(
            "BigQueryデータ取得完了",
            tables_count=len(tables),
            usage_count=len(usage_stats),
        )

        # 2. データ結合
        merged = TableUsageService.merge_usage_data(tables, usage_stats)

        # 3. リネージ情報取得・結合
        self._logger.info("Lineage API呼び出し中")
        table_fqns = [
            f"bigquery:{self._config.project_id}.{u.dataset_id}.{u.table_id}"
            for u in merged
        ]

        # Lineage APIのロケーションはregionから変換（region-us -> us）
        lineage_location = self._config.region.replace("region-", "")

        leaf_fqns = self._lineage_repo.get_leaf_tables(
            project_id=self._config.project_id,
            location=lineage_location,
            table_fqns=table_fqns,
        )

        final_data = TableUsageService.merge_with_leaf_info(
            merged, leaf_fqns, self._config.project_id
        )
        self._logger.info(
            "リーフテーブル特定完了",
            leaf_count=len(leaf_fqns),
            total_count=len(final_data),
        )

        # 4. CSVに保存
        self._logger.info("CSVキャッシュに保存中", cache_dir=str(self._config.cache_dir))
        self._csv_cache.save_tables(tables)
        self._csv_cache.save_usage_stats(final_data)

        self._logger.info("バッチ処理完了")
