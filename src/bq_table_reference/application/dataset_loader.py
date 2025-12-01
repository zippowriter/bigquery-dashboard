"""データセットローダー。

データセット・テーブルのロード、オンメモリ保持、検索機能を提供するファサード。
"""

import logging

from typing import Protocol

from bq_table_reference.domain.exceptions import DatasetLoaderError
from bq_table_reference.domain.models import DatasetInfo, LoadResult, TableInfo
from bq_table_reference.infrastructure.bq_client_adapter import BQClientAdapter


logger = logging.getLogger(__name__)


class ProgressCallback(Protocol):
    """一括ロード中の進捗を報告するためのプロトコル。"""

    def __call__(self, current: int, total: int, dataset_id: str) -> None:
        """進捗を報告する。

        Args:
            current: これまでに処理されたデータセット数。
            total: 処理対象のデータセット総数。
            dataset_id: 処理中のデータセットID。
        """
        ...


class DatasetLoader:
    """データセット・テーブルのロード、オンメモリ保持、検索機能を提供するファサード。

    BQClientAdapter を使用してデータを取得し、辞書によるインデックスで
    O(1) 検索を実現する。

    Attributes:
        _adapter: BigQuery クライアントアダプター
        _datasets: データセット ID をキーとする DatasetInfo の辞書
        _tables: フルパスをキーとする TableInfo の辞書
        _tables_by_dataset: データセット ID をキーとする TableInfo リストの辞書

    Examples:
        >>> adapter = BQClientAdapter(project="my-project")
        >>> loader = DatasetLoader(adapter=adapter)
        >>> result = loader.load_all("my-project")
        >>> print(f"Loaded {result.datasets_success} datasets")
    """

    def __init__(
        self,
        adapter: BQClientAdapter | None = None,
        project: str | None = None,
    ) -> None:
        """ローダーを初期化する。

        Args:
            adapter: 事前設定済みのアダプター（オプション）。None の場合は新規作成。
            project: GCP プロジェクト ID。adapter が None の場合は必須。

        Raises:
            ValueError: adapter も project も指定されていない場合。
            AuthenticationError: 有効な認証情報が見つからない場合。
        """
        if adapter is None and project is None:
            raise ValueError("adapter または project を指定してください")

        if adapter is not None:
            self._adapter = adapter
        else:
            # project が指定されている場合は新規アダプターを作成
            self._adapter = BQClientAdapter(project=project)

        # オンメモリデータ保持構造
        self._datasets: dict[str, DatasetInfo] = {}
        self._tables: dict[str, TableInfo] = {}
        self._tables_by_dataset: dict[str, list[TableInfo]] = {}

    @property
    def datasets(self) -> list[DatasetInfo]:
        """ロード済みの全データセットを返す。

        Returns:
            DatasetInfo オブジェクトのリスト。
        """
        return list[DatasetInfo](self._datasets.values())

    @property
    def tables(self) -> list[TableInfo]:
        """ロード済みの全テーブルを返す。

        Returns:
            TableInfo オブジェクトのリスト。
        """
        return list[TableInfo](self._tables.values())

    def load_all(
        self,
        project: str,
        on_progress: ProgressCallback | None = None,
    ) -> LoadResult:
        """プロジェクトから全データセットとテーブルをロードする。

        Args:
            project: GCP プロジェクト ID。
            on_progress: 進捗報告用のコールバック（オプション）。

        Returns:
            LoadResult: 成功/失敗件数のサマリー。

        Note:
            個別データセットでのエラーはログに記録され LoadResult.errors に保存されるが、
            他のデータセットの処理は継続される。
        """
        datasets_success = 0
        datasets_failed = 0
        tables_total = 0
        errors: dict[str, str] = {}

        # データセット一覧を取得（リストに変換して総数を把握）
        datasets = list[DatasetInfo](self._adapter.list_datasets(project))
        total_datasets = len(datasets)

        for index, dataset in enumerate[DatasetInfo](datasets, start=1):
            # データセットを内部辞書に登録
            self._datasets[dataset.dataset_id] = dataset

            # 進捗コールバックを呼び出し
            if on_progress is not None:
                on_progress(index, total_datasets, dataset.dataset_id)

            # テーブル一覧を取得
            try:
                tables = list[TableInfo](
                    self._adapter.list_tables(dataset.dataset_id, project)
                )

                # テーブルを内部辞書に登録
                for table in tables:
                    self._tables[table.full_path] = table

                # データセット別テーブル辞書に登録
                if dataset.dataset_id not in self._tables_by_dataset:
                    self._tables_by_dataset[dataset.dataset_id] = []
                self._tables_by_dataset[dataset.dataset_id].extend(tables)

                tables_total += len(tables)
                datasets_success += 1

            except DatasetLoaderError as e:
                # エラーをログに記録
                logger.warning(
                    f"データセット '{dataset.dataset_id}' のテーブル取得に失敗しました: {e}"
                )
                errors[dataset.dataset_id] = str(e)
                datasets_failed += 1

        return LoadResult(
            datasets_success=datasets_success,
            datasets_failed=datasets_failed,
            tables_total=tables_total,
            errors=errors,
        )

    def get_dataset(self, dataset_id: str) -> DatasetInfo | None:
        """ID でデータセット情報を取得する。

        Args:
            dataset_id: BigQuery データセット ID。

        Returns:
            見つかった場合は DatasetInfo、それ以外は None。

        計算量: O(1)
        """
        return self._datasets.get(dataset_id)

    def get_table(self, full_path: str) -> TableInfo | None:
        """フルパスでテーブル情報を取得する。

        Args:
            full_path: "project.dataset.table" 形式のテーブルフルパス。

        Returns:
            見つかった場合は TableInfo、それ以外は None。
        """
        return self._tables.get(full_path)

    def get_tables_by_dataset(self, dataset_id: str) -> list[TableInfo]:
        """データセット内の全テーブルを取得する。

        Args:
            dataset_id: BigQuery データセット ID。

        Returns:
            TableInfo オブジェクトのリスト。データセットが見つからない場合は空リスト。
        """
        return self._tables_by_dataset.get(dataset_id, [])
