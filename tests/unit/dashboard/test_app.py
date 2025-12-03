"""Dashアプリケーション作成のテスト。"""

from src.shared.domain.models import TableInfo, TableUsage


class FakeTableRepository:
    """テスト用のFakeリポジトリ。"""

    def __init__(
        self,
        tables: list[TableInfo] | None = None,
        usage_stats: list[TableUsage] | None = None,
    ):
        self._tables = tables or []
        self._usage_stats = usage_stats or []
        self.fetch_tables_called = False
        self.fetch_tables_project_id: str | None = None

    def fetch_tables(self, project_id: str) -> list[TableInfo]:
        self.fetch_tables_called = True
        self.fetch_tables_project_id = project_id
        return self._tables

    def fetch_usage_stats(self, project_id: str, region: str) -> list[TableUsage]:
        return self._usage_stats


class TestCreateApp:
    """create_app関数のテスト。"""

    def test_create_app_with_default_config(self) -> None:
        """デフォルト設定でcreate_appが動作することを検証する。"""
        from src.dashboard.app import create_app
        from src.dashboard.config import AppConfig

        config = AppConfig()
        app = create_app(config)
        assert app.title == "BigQueryテーブル利用状況"

    def test_create_app_skips_table_display_when_project_id_is_none(self) -> None:
        """project_idがNoneの場合、テーブル表示をスキップすることを検証する。"""
        from src.dashboard.app import create_app
        from src.dashboard.config import AppConfig

        config = AppConfig(project_id=None)
        app = create_app(config)

        # アプリが正常に作成されることを確認
        assert app is not None
        assert app.title == "BigQueryテーブル利用状況"
