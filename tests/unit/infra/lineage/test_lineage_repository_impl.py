"""DataCatalogLineageRepositoryのユニットテスト."""

from unittest.mock import Mock, patch

import pytest

from domain.value_objects.table_id import TableId
from infra.lineage.lineage_repository_impl import DataCatalogLineageRepository


class TestFindLeafTablesFromRoots:
    """find_leaf_tables_from_rootsメソッドのテストクラス."""

    @pytest.fixture
    def mock_client_factory(self) -> Mock:
        """モックClientFactoryのフィクスチャ."""
        mock = Mock()
        mock.location = "us"
        mock.get_client.return_value.__enter__ = Mock(return_value=Mock())
        mock.get_client.return_value.__exit__ = Mock(return_value=None)
        return mock

    def test_empty_root_tables(self, mock_client_factory: Mock) -> None:
        """空のルートテーブルリストで空リストが返ることを確認."""
        repo = DataCatalogLineageRepository(mock_client_factory)
        result = repo.find_leaf_tables_from_roots([])
        assert result == []

    def test_single_root_is_leaf(self, mock_client_factory: Mock) -> None:
        """ルート自体がリーフの場合を確認."""
        repo = DataCatalogLineageRepository(mock_client_factory)

        root = TableId(project_id="project-a", dataset_id="raw", table_id="events")

        with (
            patch.object(
                repo, "_search_downstream_tables", return_value=[]
            ) as mock_downstream,
            patch.object(
                repo, "_search_upstream_tables", return_value=[]
            ) as mock_upstream,
        ):
            result = repo.find_leaf_tables_from_roots([root])

        assert len(result) == 1
        assert result[0].table_id == root
        assert result[0].upstream_count == 0
        mock_downstream.assert_called_once()
        mock_upstream.assert_called_once()

    def test_single_root_with_downstream_leaf(self, mock_client_factory: Mock) -> None:
        """単一ルートから下流リーフを見つける場合を確認."""
        repo = DataCatalogLineageRepository(mock_client_factory)

        root = TableId(project_id="project-a", dataset_id="raw", table_id="events")
        leaf = TableId(project_id="project-a", dataset_id="reports", table_id="final")

        # rootの下流はleaf、leafの下流は空
        def mock_downstream(client, project_id, fqn):
            if "events" in fqn:
                return [leaf]
            return []

        def mock_upstream(client, project_id, fqn):
            if "final" in fqn:
                return [root]
            return []

        with (
            patch.object(
                repo, "_search_downstream_tables", side_effect=mock_downstream
            ),
            patch.object(repo, "_search_upstream_tables", side_effect=mock_upstream),
        ):
            result = repo.find_leaf_tables_from_roots([root])

        assert len(result) == 1
        assert result[0].table_id == leaf
        assert result[0].upstream_count == 1

    def test_multiple_leaves(self, mock_client_factory: Mock) -> None:
        """複数のリーフが見つかる場合を確認."""
        repo = DataCatalogLineageRepository(mock_client_factory)

        root = TableId(project_id="project-a", dataset_id="raw", table_id="events")
        leaf1 = TableId(
            project_id="project-a", dataset_id="reports", table_id="report1"
        )
        leaf2 = TableId(
            project_id="project-a", dataset_id="reports", table_id="report2"
        )

        # rootから2つのリーフへ分岐
        def mock_downstream(client, project_id, fqn):
            if "events" in fqn:
                return [leaf1, leaf2]
            return []

        def mock_upstream(client, project_id, fqn):
            return [root]

        with (
            patch.object(
                repo, "_search_downstream_tables", side_effect=mock_downstream
            ),
            patch.object(repo, "_search_upstream_tables", side_effect=mock_upstream),
        ):
            result = repo.find_leaf_tables_from_roots([root])

        assert len(result) == 2
        table_ids = [r.table_id for r in result]
        assert leaf1 in table_ids
        assert leaf2 in table_ids

    def test_cycle_detection(self, mock_client_factory: Mock) -> None:
        """循環参照がある場合に無限ループしないことを確認."""
        repo = DataCatalogLineageRepository(mock_client_factory)

        table_a = TableId(project_id="project-a", dataset_id="raw", table_id="table_a")
        table_b = TableId(project_id="project-a", dataset_id="raw", table_id="table_b")
        table_c = TableId(project_id="project-a", dataset_id="raw", table_id="table_c")

        # A -> B -> C -> A (循環)
        def mock_downstream(client, project_id, fqn):
            if "table_a" in fqn:
                return [table_b]
            elif "table_b" in fqn:
                return [table_c]
            elif "table_c" in fqn:
                return [table_a]  # 循環
            return []

        call_count = 0

        def counting_downstream(client, project_id, fqn):
            nonlocal call_count
            call_count += 1
            if call_count > 10:
                pytest.fail("無限ループが検出されました")
            return mock_downstream(client, project_id, fqn)

        with patch.object(
            repo, "_search_downstream_tables", side_effect=counting_downstream
        ):
            result = repo.find_leaf_tables_from_roots([table_a])

        # 循環のためリーフは見つからない
        assert len(result) == 0
        # 各テーブルは1回ずつのみ訪問される
        assert call_count == 3

    def test_deep_hierarchy(self, mock_client_factory: Mock) -> None:
        """深い階層のリネージを正しく探索できることを確認."""
        repo = DataCatalogLineageRepository(mock_client_factory)

        tables = [
            TableId(project_id="project-a", dataset_id="raw", table_id=f"table_{i}")
            for i in range(5)
        ]

        # table_0 -> table_1 -> table_2 -> table_3 -> table_4 (leaf)
        def mock_downstream(client, project_id, fqn):
            for i in range(4):
                if f"table_{i}" in fqn:
                    return [tables[i + 1]]
            return []

        def mock_upstream(client, project_id, fqn):
            for i in range(1, 5):
                if f"table_{i}" in fqn:
                    return [tables[i - 1]]
            return []

        with (
            patch.object(
                repo, "_search_downstream_tables", side_effect=mock_downstream
            ),
            patch.object(repo, "_search_upstream_tables", side_effect=mock_upstream),
        ):
            result = repo.find_leaf_tables_from_roots([tables[0]])

        assert len(result) == 1
        assert result[0].table_id == tables[4]
        assert result[0].upstream_count == 1

    def test_cross_project_lineage(self, mock_client_factory: Mock) -> None:
        """プロジェクトを跨いだリネージを正しく探索できることを確認."""
        repo = DataCatalogLineageRepository(mock_client_factory)

        root = TableId(project_id="project-a", dataset_id="raw", table_id="events")
        middle = TableId(
            project_id="project-b", dataset_id="staging", table_id="events"
        )
        leaf = TableId(project_id="project-c", dataset_id="reports", table_id="final")

        # project-a -> project-b -> project-c
        def mock_downstream(client, project_id, fqn):
            if "project-a" in fqn:
                return [middle]
            elif "project-b" in fqn:
                return [leaf]
            return []

        def mock_upstream(client, project_id, fqn):
            if "project-c" in fqn:
                return [middle]
            elif "project-b" in fqn:
                return [root]
            return []

        with (
            patch.object(
                repo, "_search_downstream_tables", side_effect=mock_downstream
            ),
            patch.object(repo, "_search_upstream_tables", side_effect=mock_upstream),
        ):
            result = repo.find_leaf_tables_from_roots([root])

        assert len(result) == 1
        assert result[0].table_id == leaf
        assert result[0].table_id.project_id == "project-c"

    def test_project_filtering_skips_outside_projects(
        self, mock_client_factory: Mock
    ) -> None:
        """許可されたプロジェクト外のテーブルをスキップすることを確認."""
        repo = DataCatalogLineageRepository(mock_client_factory)

        root = TableId(project_id="project-a", dataset_id="raw", table_id="events")
        middle = TableId(
            project_id="project-b", dataset_id="staging", table_id="events"
        )
        leaf = TableId(project_id="project-c", dataset_id="reports", table_id="final")

        # project-a -> project-b -> project-c
        def mock_downstream(client, project_id, fqn):
            if "project-a" in fqn:
                return [middle]
            elif "project-b" in fqn:
                return [leaf]
            return []

        def mock_upstream(client, project_id, fqn):
            return []

        with (
            patch.object(
                repo, "_search_downstream_tables", side_effect=mock_downstream
            ),
            patch.object(repo, "_search_upstream_tables", side_effect=mock_upstream),
        ):
            # project-a のみ許可 → project-b に到達した時点で探索終了
            # project-a がリーフとして扱われる
            result = repo.find_leaf_tables_from_roots(
                [root], allowed_project_ids=["project-a"]
            )

        assert len(result) == 1
        assert result[0].table_id == root
        assert result[0].table_id.project_id == "project-a"

    def test_project_filtering_allows_multiple_projects(
        self, mock_client_factory: Mock
    ) -> None:
        """複数プロジェクトを許可した場合の探索を確認."""
        repo = DataCatalogLineageRepository(mock_client_factory)

        root = TableId(project_id="project-a", dataset_id="raw", table_id="events")
        middle = TableId(
            project_id="project-b", dataset_id="staging", table_id="events"
        )
        leaf = TableId(project_id="project-c", dataset_id="reports", table_id="final")

        # project-a -> project-b -> project-c
        def mock_downstream(client, project_id, fqn):
            if "project-a" in fqn:
                return [middle]
            elif "project-b" in fqn:
                return [leaf]
            return []

        def mock_upstream(client, project_id, fqn):
            if "project-b" in fqn:
                return [root]
            return []

        with (
            patch.object(
                repo, "_search_downstream_tables", side_effect=mock_downstream
            ),
            patch.object(repo, "_search_upstream_tables", side_effect=mock_upstream),
        ):
            # project-a と project-b を許可 → project-c に到達した時点で探索終了
            # project-b がリーフとして扱われる
            result = repo.find_leaf_tables_from_roots(
                [root], allowed_project_ids=["project-a", "project-b"]
            )

        assert len(result) == 1
        assert result[0].table_id == middle
        assert result[0].table_id.project_id == "project-b"

    def test_project_filtering_none_allows_all(self, mock_client_factory: Mock) -> None:
        """allowed_project_ids=None の場合は全プロジェクトを探索することを確認."""
        repo = DataCatalogLineageRepository(mock_client_factory)

        root = TableId(project_id="project-a", dataset_id="raw", table_id="events")
        leaf = TableId(project_id="project-b", dataset_id="reports", table_id="final")

        def mock_downstream(client, project_id, fqn):
            if "project-a" in fqn:
                return [leaf]
            return []

        def mock_upstream(client, project_id, fqn):
            if "project-b" in fqn:
                return [root]
            return []

        with (
            patch.object(
                repo, "_search_downstream_tables", side_effect=mock_downstream
            ),
            patch.object(repo, "_search_upstream_tables", side_effect=mock_upstream),
        ):
            # allowed_project_ids=None なので全プロジェクトを探索
            result = repo.find_leaf_tables_from_roots([root], allowed_project_ids=None)

        assert len(result) == 1
        assert result[0].table_id == leaf
        assert result[0].table_id.project_id == "project-b"


class TestParseBigqueryFqn:
    """_parse_bigquery_fqnメソッドのテストクラス."""

    @pytest.fixture
    def mock_client_factory(self) -> Mock:
        """モックClientFactoryのフィクスチャ."""
        mock = Mock()
        mock.location = "us"
        return mock

    @pytest.fixture
    def repo(self, mock_client_factory: Mock) -> DataCatalogLineageRepository:
        """リポジトリのフィクスチャ."""
        return DataCatalogLineageRepository(mock_client_factory)

    def test_normal_fqn(self, repo: DataCatalogLineageRepository) -> None:
        """通常のFQN形式をパースできることを確認."""
        result = repo._parse_bigquery_fqn("bigquery:project-a.dataset.table")
        assert result is not None
        assert result.project_id == "project-a"
        assert result.dataset_id == "dataset"
        assert result.table_id == "table"

    def test_sharded_fqn(self, repo: DataCatalogLineageRepository) -> None:
        """シャーディング形式のFQNをパースできることを確認."""
        result = repo._parse_bigquery_fqn("bigquery:sharded:project-a.dataset.table")
        assert result is not None
        assert result.project_id == "project-a"
        assert result.dataset_id == "dataset"
        assert result.table_id == "table"

    def test_non_bigquery_fqn(self, repo: DataCatalogLineageRepository) -> None:
        """BigQuery以外のFQNでNoneが返ることを確認."""
        result = repo._parse_bigquery_fqn("spanner:project.instance.database")
        assert result is None

    def test_invalid_parts_count(self, repo: DataCatalogLineageRepository) -> None:
        """パーツ数が不正な場合Noneが返ることを確認."""
        result = repo._parse_bigquery_fqn("bigquery:project.dataset")
        assert result is None

    def test_empty_string(self, repo: DataCatalogLineageRepository) -> None:
        """空文字列でNoneが返ることを確認."""
        result = repo._parse_bigquery_fqn("")
        assert result is None
