"""Lineage APIを使用したLineageRepositoryの実装."""

from collections import deque
from collections.abc import Sequence

from google.api_core.exceptions import GoogleAPIError
from google.cloud.datacatalog_lineage_v1 import (
    EntityReference,
    LineageClient,
    SearchLinksRequest,
)

from domain.entities.lineage import LeafTable, LineageNode
from domain.value_objects.table_id import TableId
from infra.lineage.client import LineageClientFactory
from infra.lineage.exceptions import LineageApiError, LineageRepositoryError


class DataCatalogLineageRepository:
    """Lineage APIを使用したLineageRepositoryの実装."""

    def __init__(self, client_factory: LineageClientFactory) -> None:
        """初期化.

        Args:
            client_factory: Lineage APIクライアントファクトリ
        """
        self._client_factory = client_factory

    def get_table_lineage(self, table_id: TableId) -> LineageNode:
        """指定されたテーブルのリネージ情報を取得する.

        Args:
            table_id: 対象テーブルのID

        Returns:
            LineageNode エンティティ

        Raises:
            LineageRepositoryError: リネージ情報取得に失敗した場合
        """
        try:
            with self._client_factory.get_client() as client:
                fqn = self._build_bigquery_fqn(table_id)

                upstream_tables = self._search_upstream_tables(
                    client, table_id.project_id, fqn
                )

                downstream_tables = self._search_downstream_tables(
                    client, table_id.project_id, fqn
                )

                return LineageNode(
                    table_id=table_id,
                    upstream_tables=upstream_tables,
                    downstream_tables=downstream_tables,
                    is_leaf=len(downstream_tables) == 0,
                )

        except LineageApiError as e:
            raise LineageRepositoryError(
                f"テーブル {table_id} のリネージ情報取得に失敗しました: {e}",
                cause=e,
            ) from e

    def get_leaf_tables(
        self,
        table_ids: Sequence[TableId],
        allowed_project_ids: Sequence[str] | None = None,
    ) -> list[LeafTable]:
        """指定されたテーブルの中からリーフノードを特定する.

        Args:
            table_ids: 対象テーブルIDのリスト
            allowed_project_ids: 探索を許可するプロジェクトIDのリスト。
                指定した場合、これらのプロジェクト内のテーブルのみを探索対象とする。
                Noneの場合は全プロジェクトを探索対象とする。

        Returns:
            LeafTable エンティティのリスト

        Raises:
            LineageRepositoryError: リーフノード判定に失敗した場合
        """
        if not table_ids:
            return []

        allowed_projects = set(allowed_project_ids) if allowed_project_ids else None
        leaf_tables: list[LeafTable] = []

        try:
            with self._client_factory.get_client() as client:
                for table_id in table_ids:
                    fqn = self._build_bigquery_fqn(table_id)

                    downstream_tables = self._search_downstream_tables(
                        client, table_id.project_id, fqn
                    )

                    # 許可されたプロジェクト内の下流テーブルのみをフィルタリング
                    if allowed_projects is not None:
                        downstream_tables = [
                            dt
                            for dt in downstream_tables
                            if dt.project_id in allowed_projects
                        ]

                    if len(downstream_tables) == 0:
                        upstream_tables = self._search_upstream_tables(
                            client, table_id.project_id, fqn
                        )

                        leaf_tables.append(
                            LeafTable(
                                table_id=table_id,
                                upstream_count=len(upstream_tables),
                            )
                        )

            return leaf_tables

        except LineageApiError as e:
            raise LineageRepositoryError(
                f"リーフノード判定に失敗しました: {e}",
                cause=e,
            ) from e

    def find_leaf_tables_from_roots(
        self,
        root_tables: Sequence[TableId],
        allowed_project_ids: Sequence[str] | None = None,
    ) -> list[LeafTable]:
        """指定されたルートテーブルから下流を辿り、リーフノードを取得する.

        BFS（幅優先探索）でルートテーブルから下流を辿り、
        下流を持たないテーブル（リーフノード）を収集する。

        Args:
            root_tables: 探索の起点となるテーブルIDのリスト
            allowed_project_ids: 探索を許可するプロジェクトIDのリスト。
                指定した場合、これらのプロジェクト内のテーブルのみを探索対象とする。
                許可外のプロジェクトのテーブルは探索キューに追加されず、
                その先の下流は辿らない。Noneの場合は全プロジェクトを探索対象とする。

        Returns:
            LeafTable エンティティのリスト

        Raises:
            LineageRepositoryError: リーフノード探索に失敗した場合
        """
        if not root_tables:
            return []

        allowed_projects = set(allowed_project_ids) if allowed_project_ids else None
        leaf_tables: list[LeafTable] = []
        visited: set[str] = set()
        queue: deque[TableId] = deque(root_tables)

        try:
            with self._client_factory.get_client() as client:
                while queue:
                    current = queue.popleft()
                    fqn = self._build_bigquery_fqn(current)

                    if fqn in visited:
                        continue
                    visited.add(fqn)

                    downstream = self._search_downstream_tables(
                        client, current.project_id, fqn
                    )

                    # 許可されたプロジェクト内の下流テーブルのみをフィルタリング
                    if allowed_projects is not None:
                        downstream = [
                            dt for dt in downstream if dt.project_id in allowed_projects
                        ]

                    if not downstream:
                        upstream = self._search_upstream_tables(
                            client, current.project_id, fqn
                        )
                        leaf_tables.append(
                            LeafTable(
                                table_id=current,
                                upstream_count=len(upstream),
                            )
                        )
                    else:
                        for dt in downstream:
                            if self._build_bigquery_fqn(dt) not in visited:
                                queue.append(dt)

            return leaf_tables

        except LineageApiError as e:
            raise LineageRepositoryError(
                f"ルートからのリーフノード探索に失敗しました: {e}",
                cause=e,
            ) from e

    def _build_bigquery_fqn(self, table_id: TableId) -> str:
        """BigQueryテーブルのFully Qualified Nameを構築する.

        Args:
            table_id: テーブルID

        Returns:
            Lineage API用のFQN (例: "bigquery:project.dataset.table")
        """
        return (
            f"bigquery:{table_id.project_id}.{table_id.dataset_id}.{table_id.table_id}"
        )

    def _search_upstream_tables(
        self,
        client: LineageClient,
        project_id: str,
        target_fqn: str,
    ) -> list[TableId]:
        """上流テーブル（このテーブルを作成するためのソーステーブル）を検索する.

        Args:
            client: Lineage APIクライアント
            project_id: 検索対象プロジェクトID
            target_fqn: 対象テーブルのFQN

        Returns:
            上流テーブルIDのリスト

        Raises:
            LineageApiError: API呼び出しに失敗した場合
        """
        try:
            parent = f"projects/{project_id}/locations/{self._client_factory.location}"

            target_ref = EntityReference()
            target_ref.fully_qualified_name = target_fqn

            request = SearchLinksRequest(
                parent=parent,
                target=target_ref,
            )

            upstream_tables: list[TableId] = []

            for link in client.search_links(request=request):
                source_fqn = link.source.fully_qualified_name
                table_id = self._parse_bigquery_fqn(source_fqn)
                if table_id is not None:
                    upstream_tables.append(table_id)

            return upstream_tables

        except GoogleAPIError as e:
            raise LineageApiError(
                f"上流テーブル検索に失敗しました: {e}",
                operation="search_links (upstream)",
                cause=e,
            ) from e

    def _search_downstream_tables(
        self,
        client: LineageClient,
        project_id: str,
        source_fqn: str,
    ) -> list[TableId]:
        """下流テーブル（このテーブルを参照しているテーブル）を検索する.

        Args:
            client: Lineage APIクライアント
            project_id: 検索対象プロジェクトID
            source_fqn: 対象テーブルのFQN

        Returns:
            下流テーブルIDのリスト

        Raises:
            LineageApiError: API呼び出しに失敗した場合
        """
        try:
            parent = f"projects/{project_id}/locations/{self._client_factory.location}"

            source_ref = EntityReference()
            source_ref.fully_qualified_name = source_fqn

            request = SearchLinksRequest(
                parent=parent,
                source=source_ref,
            )

            downstream_tables: list[TableId] = []

            for link in client.search_links(request=request):
                target_fqn = link.target.fully_qualified_name
                table_id = self._parse_bigquery_fqn(target_fqn)
                if table_id is not None:
                    downstream_tables.append(table_id)

            return downstream_tables

        except GoogleAPIError as e:
            raise LineageApiError(
                f"下流テーブル検索に失敗しました: {e}",
                operation="search_links (downstream)",
                cause=e,
            ) from e

    def _parse_bigquery_fqn(self, fqn: str) -> TableId | None:
        """Lineage APIのFQNからTableIdを解析する.

        Args:
            fqn: Fully Qualified Name
                通常形式: "bigquery:project.dataset.table"
                シャーディング形式: "bigquery:sharded:project.dataset.table"

        Returns:
            TableIdまたはNone（BigQueryテーブルでない場合）
        """
        if not fqn.startswith("bigquery:"):
            return None

        # "bigquery:" プレフィックスを除去
        table_path = fqn[9:]  # len("bigquery:") = 9

        # "sharded:" プレフィックスがある場合は除去
        if table_path.startswith("sharded:"):
            table_path = table_path[8:]  # len("sharded:") = 8

        parts = table_path.split(".")

        if len(parts) != 3:
            return None

        return TableId(
            project_id=parts[0],
            dataset_id=parts[1],
            table_id=parts[2],
        )
