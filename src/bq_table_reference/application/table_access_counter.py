"""テーブル参照回数集計のアプリケーションサービス。

TableAccessCounterはテーブル参照回数集計のユースケースを実装するファサードクラス。
複数データソースからのデータ取得、結果の統合、フィルタリングを担当する。
"""

from datetime import datetime, timedelta, timezone
from enum import StrEnum

from bq_table_reference.domain.exceptions import DatasetLoaderError
from bq_table_reference.domain.models import (
    FilterConfig,
    TableAccessCount,
    TableAccessResult,
)
from bq_table_reference.domain.protocols import (
    ProgressCallback,
    TableAccessDataSourceProtocol,
)


class DataSourceOption(StrEnum):
    """データソース選択オプション。

    テーブル参照回数の取得に使用するデータソースを指定する。
    """

    INFO_SCHEMA = "info_schema"
    AUDIT_LOG = "audit_log"
    BOTH = "both"


# INFORMATION_SCHEMAのデータ保持期間（日数）
INFO_SCHEMA_RETENTION_DAYS = 180


def merge_results(
    info_schema_results: list[TableAccessCount],
    audit_log_results: list[TableAccessCount],
) -> list[TableAccessCount]:
    """2つのデータソースの結果をマージする。

    同一テーブル（project, dataset, table が一致）は最大の access_count を採用する。
    結果は access_count の降順でソートされる。

    Args:
        info_schema_results: INFORMATION_SCHEMAからの結果
        audit_log_results: Audit Logからの結果

    Returns:
        マージされた結果のリスト（access_count降順）
    """
    # テーブルのフルパスをキーとして、最大のアクセスカウントを保持
    table_max_counts: dict[str, TableAccessCount] = {}

    for result in info_schema_results + audit_log_results:
        key = result.full_path
        if key not in table_max_counts:
            table_max_counts[key] = result
        elif result.access_count > table_max_counts[key].access_count:
            table_max_counts[key] = result

    # access_count降順でソート
    sorted_results = sorted(
        table_max_counts.values(),
        key=lambda x: x.access_count,
        reverse=True,
    )

    return sorted_results


def apply_filters(
    results: list[TableAccessCount],
    filter_config: FilterConfig,
) -> list[TableAccessCount]:
    """フィルタリング条件を適用する。

    min_access_count以上の結果のみを返す。

    Args:
        results: フィルタリング対象の結果リスト
        filter_config: フィルタリング条件

    Returns:
        フィルタリングされた結果のリスト
    """
    filtered = [r for r in results if r.access_count >= filter_config.min_access_count]
    return filtered


class TableAccessCounter:
    """テーブル参照回数集計のユースケースを実装するファサードクラス。

    複数のデータソース（INFORMATION_SCHEMA、Audit Log）からテーブル参照回数を取得し、
    統合された結果を提供する。
    """

    def __init__(
        self,
        info_schema_adapter: TableAccessDataSourceProtocol | None = None,
        audit_log_adapter: TableAccessDataSourceProtocol | None = None,
    ) -> None:
        """初期化。

        Args:
            info_schema_adapter: INFORMATION_SCHEMAデータソースアダプター
            audit_log_adapter: Audit Logデータソースアダプター
        """
        self._info_schema_adapter = info_schema_adapter
        self._audit_log_adapter = audit_log_adapter

    def count_access(
        self,
        project_id: str,
        filter_config: FilterConfig,
        source: DataSourceOption = DataSourceOption.BOTH,
        on_progress: ProgressCallback | None = None,
    ) -> TableAccessResult:
        """テーブル参照回数を集計する。

        Args:
            project_id: GCPプロジェクトID
            filter_config: フィルタリング条件
            source: データソース選択オプション
            on_progress: 進捗コールバック

        Returns:
            集計結果

        Raises:
            AuthenticationError: 認証失敗時（両ソースが失敗した場合）
            PermissionDeniedError: 権限不足時（両ソースが失敗した場合）
            NetworkError: ネットワークエラー時（両ソースが失敗した場合）
        """
        warnings: list[str] = []
        info_schema_results: list[TableAccessCount] = []
        audit_log_results: list[TableAccessCount] = []

        # 期間が保持期間を超える場合は警告を追加
        if filter_config.days > INFO_SCHEMA_RETENTION_DAYS:
            warnings.append(
                f"指定された期間（{filter_config.days}日）はINFORMATION_SCHEMAの"
                f"保持期間（{INFO_SCHEMA_RETENTION_DAYS}日）を超えています。"
                f"利用可能なデータのみ取得します。"
            )

        # INFORMATION_SCHEMAからの取得
        if source in (DataSourceOption.INFO_SCHEMA, DataSourceOption.BOTH):
            if self._info_schema_adapter is not None:
                try:
                    info_schema_results = self._info_schema_adapter.fetch_table_access(
                        project_id=project_id,
                        filter_config=filter_config,
                        progress_callback=on_progress,
                    )
                except DatasetLoaderError as e:
                    if source == DataSourceOption.INFO_SCHEMA:
                        raise
                    warnings.append(f"INFORMATION_SCHEMAからの取得に失敗しました: {e}")

        # Audit Logからの取得
        if source in (DataSourceOption.AUDIT_LOG, DataSourceOption.BOTH):
            if self._audit_log_adapter is not None:
                try:
                    audit_log_results = self._audit_log_adapter.fetch_table_access(
                        project_id=project_id,
                        filter_config=filter_config,
                        progress_callback=on_progress,
                    )
                except DatasetLoaderError as e:
                    if source == DataSourceOption.AUDIT_LOG:
                        raise
                    warnings.append(f"Audit Logからの取得に失敗しました: {e}")

        # 結果をマージ
        merged_results = merge_results(info_schema_results, audit_log_results)

        # フィルタリングを適用
        filtered_merged = apply_filters(merged_results, filter_config)
        filtered_info = apply_filters(info_schema_results, filter_config)
        filtered_audit = apply_filters(audit_log_results, filter_config)

        # 日付範囲を計算
        now = datetime.now(timezone.utc)
        if filter_config.start_date is not None and filter_config.end_date is not None:
            start_date = filter_config.start_date
            end_date = filter_config.end_date
        else:
            end_date = now
            start_date = now - timedelta(days=filter_config.days)

        return TableAccessResult(
            start_date=start_date,
            end_date=end_date,
            project_id=project_id,
            info_schema_results=filtered_info,
            audit_log_results=filtered_audit,
            merged_results=filtered_merged,
            warnings=warnings,
        )
