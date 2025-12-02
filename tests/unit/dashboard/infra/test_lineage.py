"""LineageRepositoryのテスト。"""

from typing import Any

from google.cloud.datacatalog_lineage_v1.types import SearchLinksRequest

from src.dashboard.infra.lineage import LineageRepository


class FakeLineageClient:
    """テスト用のFake LineageClient。

    事前定義されたdownstream_mapに基づいて下流リンクを返す。
    """

    def __init__(self, downstream_map: dict[str, list[str]]) -> None:
        """Fakeクライアントを初期化する。

        Args:
            downstream_map: ソースFQN -> 下流FQNリストのマッピング
        """
        self._downstream_map = downstream_map

    def search_links(self, request: SearchLinksRequest) -> list[Any]:
        """モックの下流リンク検索。

        Args:
            request: 検索リクエスト

        Returns:
            下流テーブルを示すFakeリンクのリスト
        """
        source_fqn = request.source.fully_qualified_name
        downstream_fqns = self._downstream_map.get(source_fqn, [])

        # FakeLinkオブジェクトを返す
        return [FakeLink(source_fqn, target_fqn) for target_fqn in downstream_fqns]


class FakeLink:
    """テスト用のFake Link。"""

    def __init__(self, source_fqn: str, target_fqn: str) -> None:
        """Fakeリンクを初期化する。"""
        self.source = FakeEntityReference(source_fqn)
        self.target = FakeEntityReference(target_fqn)


class FakeEntityReference:
    """テスト用のFake EntityReference。"""

    def __init__(self, fqn: str) -> None:
        """Fakeエンティティ参照を初期化する。"""
        self.fully_qualified_name = fqn


class TestLineageRepository:
    """LineageRepositoryのテスト。"""

    def test_get_leaf_tables_returns_tables_without_downstream(self) -> None:
        """下流がないテーブルがリーフとして識別されることを検証する。"""
        # t1 -> t2 の関係があり、t2は下流なし
        downstream_map: dict[str, list[str]] = {
            "bigquery:proj.ds.t1": ["bigquery:proj.ds.t2"],
            "bigquery:proj.ds.t2": [],
        }
        fake_client = FakeLineageClient(downstream_map)
        repo = LineageRepository(client=fake_client)

        table_fqns = [
            "bigquery:proj.ds.t1",
            "bigquery:proj.ds.t2",
        ]

        result = repo.get_leaf_tables(
            project_id="proj",
            location="us",
            table_fqns=table_fqns,
        )

        # t2のみがリーフ
        assert result == {"bigquery:proj.ds.t2"}

    def test_get_leaf_tables_excludes_tables_with_downstream(self) -> None:
        """下流があるテーブルはリーフから除外されることを検証する。"""
        downstream_map = {
            "bigquery:proj.ds.t1": ["bigquery:proj.ds.t2"],
        }
        fake_client = FakeLineageClient(downstream_map)
        repo = LineageRepository(client=fake_client)

        table_fqns = ["bigquery:proj.ds.t1"]

        result = repo.get_leaf_tables(
            project_id="proj",
            location="us",
            table_fqns=table_fqns,
        )

        # t1は下流があるのでリーフではない
        assert result == set()

    def test_get_leaf_tables_returns_all_when_no_downstream(self) -> None:
        """全テーブルに下流がない場合、全テーブルがリーフになることを検証する。"""
        fake_client = FakeLineageClient({})
        repo = LineageRepository(client=fake_client)

        table_fqns = [
            "bigquery:proj.ds.t1",
            "bigquery:proj.ds.t2",
            "bigquery:proj.ds.t3",
        ]

        result = repo.get_leaf_tables(
            project_id="proj",
            location="us",
            table_fqns=table_fqns,
        )

        # 全てリーフ
        assert result == set(table_fqns)

    def test_get_leaf_tables_handles_empty_input(self) -> None:
        """空の入力リストに対して空のセットを返すことを検証する。"""
        fake_client = FakeLineageClient({})
        repo = LineageRepository(client=fake_client)

        result = repo.get_leaf_tables(
            project_id="proj",
            location="us",
            table_fqns=[],
        )

        assert result == set()
