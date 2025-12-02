"""リネージ情報取得モジュール。

Data Lineage APIを使用してテーブル間のリネージ関係を取得する。
"""

from typing import Any, Protocol

from google.cloud.datacatalog_lineage_v1 import LineageClient
from google.cloud.datacatalog_lineage_v1.types import EntityReference, SearchLinksRequest


class LineageClientProtocol(Protocol):
    """LineageClientのProtocol定義（テスト用）。"""

    def search_links(self, request: SearchLinksRequest) -> Any:
        """下流リンクを検索する。"""
        ...


class LineageRepositoryProtocol(Protocol):
    """LineageRepositoryのProtocol定義。"""

    def get_leaf_tables(
        self,
        project_id: str,
        location: str,
        table_fqns: list[str],
    ) -> set[str]:
        """リーフテーブルのFQNセットを返す。"""
        ...


class LineageRepository:
    """Data Lineage APIを使用してリネージ情報を取得する。

    BigQueryテーブルの下流リンクを検索し、リーフテーブル（下流がないテーブル）を特定する。
    """

    _client: LineageClient | None = None

    def __init__(self, client: LineageClientProtocol | None = None) -> None:
        """リポジトリを初期化する。

        Args:
            client: LineageClientインスタンス。Noneの場合はデフォルトを使用。
        """
        self._injected_client = client

    def _get_client(self) -> LineageClientProtocol:
        """LineageClientを取得する。

        Returns:
            LineageClientインスタンス
        """
        if self._injected_client is not None:
            return self._injected_client

        if LineageRepository._client is None:
            LineageRepository._client = LineageClient()
        return LineageRepository._client

    def get_leaf_tables(
        self,
        project_id: str,
        location: str,
        table_fqns: list[str],
    ) -> set[str]:
        """リーフテーブル（下流がないテーブル）のFQNセットを返す。

        Data Lineage APIを使用して各テーブルの下流リンクを検索し、
        下流が存在しないテーブルをリーフとして特定する。

        Args:
            project_id: GCPプロジェクトID（Lineage API用）
            location: ロケーション（例: us）
            table_fqns: 検査対象テーブルのFQN一覧（bigquery:project.dataset.table形式）

        Returns:
            リーフテーブルのFQNセット
        """
        client = self._get_client()
        parent = f"projects/{project_id}/locations/{location}"
        non_leaf_tables: set[str] = set()

        for fqn in table_fqns:
            request = SearchLinksRequest(
                parent=parent,
                source=EntityReference(fully_qualified_name=fqn),
            )

            # 下流が1つでもあれば非リーフ
            for _ in client.search_links(request=request):
                non_leaf_tables.add(fqn)
                break

        # 全テーブルから非リーフを除いたものがリーフ
        return set(table_fqns) - non_leaf_tables
