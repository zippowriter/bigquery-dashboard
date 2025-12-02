"""ドメインインターフェースのプロトコル定義。

このモジュールは、データソースアダプターや
アプリケーションで使用されるその他のインターフェースの契約を確立するProtocolクラスを定義する。
"""

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from bq_table_reference.domain.models import FilterConfig, TableAccessCount


# 進捗コールバック関数の型エイリアス。
# コールバックは進捗レポート用に(current, total, message)を受け取る。
ProgressCallback = Callable[[int, int, str], None]


@runtime_checkable
class TableAccessDataSourceProtocol(Protocol):
    """テーブルアクセスデータソースアダプターのプロトコル。

    このプロトコルは、テーブルアクセスカウントデータを提供するために
    データソースアダプター（InfoSchemaAdapter、AuditLogAdapter）が
    実装すべき契約を定義する。

    実装は以下を処理する必要がある:
    - 基盤となるデータソースへの接続
    - クエリ実行と結果のパース
    - エラーハンドリングと適切な例外の送出

    Example:
        >>> class MyAdapter:
        ...     def fetch_table_access(
        ...         self,
        ...         project_id: str,
        ...         filter_config: FilterConfig,
        ...         progress_callback: ProgressCallback | None = None,
        ...     ) -> list[TableAccessCount]:
        ...         # 実装をここに記述
        ...         return []
    """

    def fetch_table_access(
        self,
        project_id: str,
        filter_config: FilterConfig,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> list[TableAccessCount]:
        """データソースからテーブルアクセスカウントを取得する。

        Args:
            project_id: クエリ対象のGCPプロジェクトID。
            filter_config: クエリのフィルタリング条件。
            progress_callback: 進捗レポート用のオプションのコールバック関数。
                長時間実行操作中に(current, total, message)で呼び出される。

        Returns:
            テーブルアクセス統計を表すTableAccessCountオブジェクトのリスト。

        Raises:
            AuthenticationError: データソースへの認証が失敗した場合。
                ユーザーは'gcloud auth application-default login'を実行する必要がある。
            PermissionDeniedError: ユーザーに必要な権限がない場合。
                INFORMATION_SCHEMAの場合: 'roles/bigquery.resourceViewer'が必要。
                Audit Logsの場合: 'roles/logging.viewer'が必要。
            NetworkError: ネットワーク接続の問題が発生した場合。
                ユーザーは接続を確認してリトライする必要がある。
        """
        ...
