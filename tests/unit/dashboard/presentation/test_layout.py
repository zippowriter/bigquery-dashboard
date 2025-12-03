"""レイアウト構築のテスト。"""

from dash import html
from google.api_core.exceptions import GoogleAPIError

from src.shared.domain.models import TableInfo, TableUsage
from src.dashboard.presentation.layout import build_data_content, build_layout


class FakeLineageRepository:
    """テスト用のFake LineageRepository。

    常に全テーブルをリーフとして返す軽量なテスト用実装。
    """

    def __init__(self, leaf_fqns: set[str] | None = None) -> None:
        """Fakeリポジトリを初期化する。

        Args:
            leaf_fqns: リーフとして返すFQNセット。Noneの場合は全テーブルをリーフとして返す。
        """
        self._leaf_fqns = leaf_fqns

    def get_leaf_tables(
        self,
        project_id: str,
        location: str,
        table_fqns: list[str],
    ) -> set[str]:
        """リーフテーブルを返却する。"""
        if self._leaf_fqns is not None:
            return self._leaf_fqns
        # デフォルトでは全テーブルをリーフとして返す
        return set(table_fqns)


class FakeTableRepository:
    """テスト用のFakeリポジトリ。

    Protocolに準拠した軽量なテスト用実装。モック不要でテスト可能。
    """

    def __init__(
        self,
        tables: list[TableInfo] | None = None,
        usage_stats: list[TableUsage] | None = None,
        raise_error: GoogleAPIError | None = None,
    ):
        """Fakeリポジトリを初期化する。

        Args:
            tables: fetch_tablesで返却するテーブルリスト
            usage_stats: fetch_usage_statsで返却する利用統計リスト
            raise_error: メソッド呼び出し時にスローするエラー
        """
        self._tables = tables or []
        self._usage_stats = usage_stats or []
        self._raise_error = raise_error

    def fetch_tables(self, project_id: str) -> list[TableInfo]:
        """テーブル一覧を返却する。"""
        if self._raise_error:
            raise self._raise_error
        return self._tables

    def fetch_usage_stats(self, project_id: str, region: str) -> list[TableUsage]:
        """利用統計を返却する。"""
        if self._raise_error:
            raise self._raise_error
        return self._usage_stats


class TestBuildLayout:
    """build_layout関数のテスト。"""

    def test_returns_div(self) -> None:
        """html.Divコンポーネントを返却することを検証する。"""
        layout = build_layout()
        assert isinstance(layout, html.Div)

    def test_contains_refresh_button(self) -> None:
        """更新ボタンが含まれることを検証する。"""
        layout = build_layout()
        layout_str = str(layout)
        assert "refresh-button" in layout_str

    def test_contains_config_store(self) -> None:
        """設定ストアが含まれることを検証する。"""
        layout = build_layout(project_id="test-project")
        layout_str = str(layout)
        assert "app-config" in layout_str

    def test_with_project_id_and_repository_returns_div(self) -> None:
        """project_idとリポジトリを渡した場合もhtml.Divを返却することを検証する。"""
        fake_repo = FakeTableRepository(
            tables=[TableInfo(dataset_id="ds1", table_id="t1")],
            usage_stats=[
                TableUsage(dataset_id="ds1", table_id="t1", reference_count=10, unique_users=3)
            ],
        )
        fake_lineage_repo = FakeLineageRepository()

        layout = build_layout(
            project_id="test-project",
            repository=fake_repo,
            lineage_repository=fake_lineage_repo,
        )

        assert isinstance(layout, html.Div)

    def test_with_datatable_when_tables_exist(self) -> None:
        """テーブルが存在する場合、DataTableが含まれることを検証する。"""
        fake_repo = FakeTableRepository(
            tables=[
                TableInfo(dataset_id="ds1", table_id="t1"),
                TableInfo(dataset_id="ds2", table_id="t2"),
            ],
            usage_stats=[
                TableUsage(dataset_id="ds1", table_id="t1", reference_count=10, unique_users=3),
            ],
        )
        fake_lineage_repo = FakeLineageRepository()

        layout = build_layout(
            project_id="test-project",
            repository=fake_repo,
            lineage_repository=fake_lineage_repo,
        )

        assert isinstance(layout, html.Div)
        layout_str = str(layout)
        assert "DataTable" in layout_str or "usage-table" in layout_str

    def test_with_none_project_id_skips_data_container(self) -> None:
        """project_id=Noneの場合、データコンテナをスキップすることを検証する。"""
        layout = build_layout(project_id=None)

        assert isinstance(layout, html.Div)
        layout_str = str(layout)
        assert "data-container" not in layout_str


class TestBuildDataContent:
    """build_data_content関数のテスト。"""

    def test_returns_datatable_when_tables_exist(self) -> None:
        """テーブルが存在する場合、DataTableを返却することを検証する。"""
        fake_repo = FakeTableRepository(
            tables=[TableInfo(dataset_id="ds1", table_id="t1")],
            usage_stats=[
                TableUsage(dataset_id="ds1", table_id="t1", reference_count=10, unique_users=3)
            ],
        )
        fake_lineage_repo = FakeLineageRepository()

        content = build_data_content(
            "test-project", "region-us", fake_repo, fake_lineage_repo
        )

        content_str = str(content)
        assert "DataTable" in content_str or "usage-table" in content_str

    def test_shows_error_message_on_api_error(self) -> None:
        """BigQuery API接続エラー時にエラーメッセージを返却することを検証する。"""
        fake_repo = FakeTableRepository(
            raise_error=GoogleAPIError("API Error"),
        )
        fake_lineage_repo = FakeLineageRepository()

        content = build_data_content(
            "test-project", "region-us", fake_repo, fake_lineage_repo
        )

        content_str = str(content)
        assert "エラー" in content_str or "Error" in content_str

    def test_shows_empty_message_when_no_tables(self) -> None:
        """テーブル情報が0件の場合にメッセージを返却することを検証する。"""
        fake_repo = FakeTableRepository(tables=[], usage_stats=[])
        fake_lineage_repo = FakeLineageRepository()

        content = build_data_content(
            "test-project", "region-us", fake_repo, fake_lineage_repo
        )

        content_str = str(content)
        assert "存在しません" in content_str or "テーブルが" in content_str
