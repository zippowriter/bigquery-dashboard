"""CSVキャッシュリポジトリのテスト。"""

import tempfile
from pathlib import Path

import pytest

from src.dashboard.domain.models import TableInfo, TableUsage
from src.dashboard.infra.csv_cache import CsvCacheRepository


class TestCsvCacheRepository:
    """CsvCacheRepositoryのテスト。"""

    def test_creates_cache_directory(self, tmp_path: Path) -> None:
        """キャッシュディレクトリが存在しない場合、作成されることを検証する。"""
        cache_dir = tmp_path / "test-cache"
        assert not cache_dir.exists()

        CsvCacheRepository(cache_dir=cache_dir)

        assert cache_dir.exists()

    def test_has_cache_returns_false_when_no_cache(self, tmp_path: Path) -> None:
        """キャッシュファイルが存在しない場合、Falseを返却することを検証する。"""
        repo = CsvCacheRepository(cache_dir=tmp_path)

        assert repo.has_cache() is False

    def test_has_cache_returns_true_when_cache_exists(self, tmp_path: Path) -> None:
        """キャッシュファイルが存在する場合、Trueを返却することを検証する。"""
        repo = CsvCacheRepository(cache_dir=tmp_path)

        # キャッシュファイルを作成
        repo.save_tables([TableInfo(dataset_id="ds1", table_id="t1")])

        assert repo.has_cache() is True


class TestSaveAndFetchTables:
    """テーブル一覧の保存・読み込みテスト。"""

    def test_save_and_fetch_tables(self, tmp_path: Path) -> None:
        """テーブル一覧を保存して読み込めることを検証する。"""
        repo = CsvCacheRepository(cache_dir=tmp_path)
        tables = [
            TableInfo(dataset_id="ds1", table_id="t1"),
            TableInfo(dataset_id="ds2", table_id="t2"),
        ]

        repo.save_tables(tables)
        fetched = repo.fetch_tables("any-project")

        assert len(fetched) == 2
        assert fetched[0].dataset_id == "ds1"
        assert fetched[0].table_id == "t1"
        assert fetched[1].dataset_id == "ds2"
        assert fetched[1].table_id == "t2"

    def test_save_empty_tables(self, tmp_path: Path) -> None:
        """空のテーブルリストを保存できることを検証する。"""
        repo = CsvCacheRepository(cache_dir=tmp_path)

        repo.save_tables([])
        fetched = repo.fetch_tables("any-project")

        assert fetched == []

    def test_fetch_tables_raises_when_no_cache(self, tmp_path: Path) -> None:
        """キャッシュファイルが存在しない場合、FileNotFoundErrorをスローすることを検証する。"""
        repo = CsvCacheRepository(cache_dir=tmp_path)

        with pytest.raises(FileNotFoundError):
            repo.fetch_tables("any-project")


class TestSaveAndFetchUsageStats:
    """利用統計の保存・読み込みテスト。"""

    def test_save_and_fetch_usage_stats(self, tmp_path: Path) -> None:
        """利用統計を保存して読み込めることを検証する。"""
        repo = CsvCacheRepository(cache_dir=tmp_path)
        usage_stats = [
            TableUsage(dataset_id="ds1", table_id="t1", reference_count=10, unique_users=3),
            TableUsage(dataset_id="ds2", table_id="t2", reference_count=5, unique_users=2),
        ]

        repo.save_usage_stats(usage_stats)
        fetched = repo.fetch_usage_stats("any-project", "any-region")

        assert len(fetched) == 2
        assert fetched[0].dataset_id == "ds1"
        assert fetched[0].reference_count == 10
        assert fetched[0].unique_users == 3
        assert fetched[1].dataset_id == "ds2"

    def test_fetch_usage_stats_returns_empty_when_no_cache(self, tmp_path: Path) -> None:
        """キャッシュファイルが存在しない場合、空リストを返却することを検証する。"""
        repo = CsvCacheRepository(cache_dir=tmp_path)

        fetched = repo.fetch_usage_stats("any-project", "any-region")

        assert fetched == []


class TestClearCache:
    """キャッシュクリアのテスト。"""

    def test_clear_cache_removes_files(self, tmp_path: Path) -> None:
        """キャッシュファイルが削除されることを検証する。"""
        repo = CsvCacheRepository(cache_dir=tmp_path)
        repo.save_tables([TableInfo(dataset_id="ds1", table_id="t1")])
        repo.save_usage_stats([TableUsage(dataset_id="ds1", table_id="t1", reference_count=1, unique_users=1)])

        assert repo.tables_cache_path.exists()
        assert repo.usage_cache_path.exists()

        repo.clear_cache()

        assert not repo.tables_cache_path.exists()
        assert not repo.usage_cache_path.exists()

    def test_clear_cache_does_not_raise_when_no_cache(self, tmp_path: Path) -> None:
        """キャッシュファイルが存在しない場合でもエラーにならないことを検証する。"""
        repo = CsvCacheRepository(cache_dir=tmp_path)

        repo.clear_cache()  # 例外が発生しないことを確認


class TestDefaultCacheDirectory:
    """デフォルトキャッシュディレクトリのテスト。"""

    def test_uses_temp_directory_by_default(self) -> None:
        """デフォルトで一時ディレクトリを使用することを検証する。"""
        repo = CsvCacheRepository()

        expected_dir = Path(tempfile.gettempdir()) / "bigquery-dashboard"
        assert repo._cache_dir == expected_dir
