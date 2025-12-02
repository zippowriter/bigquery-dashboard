"""キャッシュ付きリポジトリのテスト。"""

from pathlib import Path

from src.dashboard.domain.models import TableInfo, TableUsage
from src.dashboard.infra.cached_repository import CachedTableRepository
from src.dashboard.infra.csv_cache import CsvCacheRepository


class FakeBigQueryRepository:
    """テスト用のFake BigQueryリポジトリ。"""

    def __init__(
        self,
        tables: list[TableInfo] | None = None,
        usage_stats: list[TableUsage] | None = None,
    ):
        self._tables = tables or []
        self._usage_stats = usage_stats or []
        self.fetch_tables_called = False
        self.fetch_usage_stats_called = False
        self.fetch_all_called = False

    def fetch_tables(self, project_id: str) -> list[TableInfo]:
        self.fetch_tables_called = True
        return self._tables

    def fetch_usage_stats(self, project_id: str, region: str) -> list[TableUsage]:
        self.fetch_usage_stats_called = True
        return self._usage_stats

    def fetch_all(
        self, project_id: str, region: str
    ) -> tuple[list[TableInfo], list[TableUsage]]:
        self.fetch_all_called = True
        return self._tables, self._usage_stats


class TestCachedTableRepository:
    """CachedTableRepositoryのテスト。"""

    def test_uses_cache_when_available(self, tmp_path: Path) -> None:
        """キャッシュが存在する場合、CSVから読み込むことを検証する。"""
        csv_cache = CsvCacheRepository(cache_dir=tmp_path)
        cached_tables = [TableInfo(dataset_id="cached_ds", table_id="cached_t")]
        csv_cache.save_tables(cached_tables)
        csv_cache.save_usage_stats([])

        fake_bq = FakeBigQueryRepository(
            tables=[TableInfo(dataset_id="bq_ds", table_id="bq_t")]
        )

        repo = CachedTableRepository(csv_cache=csv_cache, bigquery_repo=fake_bq)
        tables = repo.fetch_tables("any-project")

        assert len(tables) == 1
        assert tables[0].dataset_id == "cached_ds"
        assert not fake_bq.fetch_tables_called

    def test_uses_bigquery_when_no_cache(self, tmp_path: Path) -> None:
        """キャッシュが存在しない場合、BigQueryから取得することを検証する。"""
        csv_cache = CsvCacheRepository(cache_dir=tmp_path)
        fake_bq = FakeBigQueryRepository(
            tables=[TableInfo(dataset_id="bq_ds", table_id="bq_t")]
        )

        repo = CachedTableRepository(csv_cache=csv_cache, bigquery_repo=fake_bq)
        tables = repo.fetch_tables("any-project")

        assert len(tables) == 1
        assert tables[0].dataset_id == "bq_ds"
        assert fake_bq.fetch_tables_called

    def test_has_cache(self, tmp_path: Path) -> None:
        """has_cacheがCSVキャッシュの状態を反映することを検証する。"""
        csv_cache = CsvCacheRepository(cache_dir=tmp_path)
        fake_bq = FakeBigQueryRepository()

        repo = CachedTableRepository(csv_cache=csv_cache, bigquery_repo=fake_bq)

        assert repo.has_cache() is False

        csv_cache.save_tables([])

        assert repo.has_cache() is True


class TestRefresh:
    """refreshメソッドのテスト。"""

    def test_refresh_fetches_from_bigquery_and_saves_cache(self, tmp_path: Path) -> None:
        """refreshがBigQueryから取得してキャッシュに保存することを検証する。"""
        csv_cache = CsvCacheRepository(cache_dir=tmp_path)
        bq_tables = [TableInfo(dataset_id="bq_ds", table_id="bq_t")]
        bq_usage = [
            TableUsage(dataset_id="bq_ds", table_id="bq_t", reference_count=10, unique_users=3)
        ]
        fake_bq = FakeBigQueryRepository(tables=bq_tables, usage_stats=bq_usage)

        repo = CachedTableRepository(csv_cache=csv_cache, bigquery_repo=fake_bq)

        # キャッシュがないことを確認
        assert not repo.has_cache()

        # refreshを実行
        tables, usage_stats = repo.refresh("test-project", "region-us")

        # BigQueryから取得されたことを確認
        assert fake_bq.fetch_all_called
        assert len(tables) == 1
        assert tables[0].dataset_id == "bq_ds"
        assert len(usage_stats) == 1

        # キャッシュが作成されたことを確認
        assert repo.has_cache()

        # 次回はキャッシュから読み込まれることを確認
        fake_bq.fetch_tables_called = False
        cached_tables = repo.fetch_tables("test-project")
        assert not fake_bq.fetch_tables_called
        assert cached_tables[0].dataset_id == "bq_ds"


class TestClearCache:
    """clear_cacheメソッドのテスト。"""

    def test_clear_cache_removes_cache(self, tmp_path: Path) -> None:
        """clear_cacheがキャッシュを削除することを検証する。"""
        csv_cache = CsvCacheRepository(cache_dir=tmp_path)
        csv_cache.save_tables([TableInfo(dataset_id="ds", table_id="t")])

        repo = CachedTableRepository(csv_cache=csv_cache)

        assert repo.has_cache() is True

        repo.clear_cache()

        assert repo.has_cache() is False
