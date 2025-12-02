"""Cloud Audit Logsからテーブル参照情報を取得するアダプター。

Cloud Logging APIを使用して、BigQueryのtableDataReadイベントから
テーブルの参照回数を取得する。
"""

import logging
import re
import time
from collections import Counter
from collections.abc import Callable, Iterator
from datetime import datetime, timedelta, timezone
from typing import cast

from google.api_core import exceptions as api_exceptions
from google.cloud import logging as cloud_logging

from bq_table_reference.domain.exceptions import (
    NetworkError,
    PermissionDeniedError,
)
from bq_table_reference.domain.models import (
    DataSource,
    FilterConfig,
    TableAccessCount,
)

# ロガー設定
_logger = logging.getLogger(__name__)

# リソース名のパース用正規表現
_RESOURCE_NAME_PATTERN = re.compile(
    r"projects/(?P<project_id>[^/]+)/datasets/(?P<dataset_id>[^/]+)/tables/(?P<table_id>[^/]+)"
)

# デフォルトのリトライ設定
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_RETRY_DELAY = 1.0  # 秒
_BACKOFF_MULTIPLIER = 2.0


def build_log_filter(
    project_id: str,
    filter_config: FilterConfig,
) -> str:
    """Cloud Logging用のフィルタ文字列を生成する。

    Args:
        project_id: GCPプロジェクトID
        filter_config: フィルタリング条件

    Returns:
        生成されたフィルタ文字列
    """
    # 基本フィルタ
    filters = [
        'resource.type="bigquery_dataset"',
        'protoPayload.metadata.tableDataRead:*',
    ]

    # 期間フィルタの生成
    if filter_config.start_date is not None and filter_config.end_date is not None:
        start_str = filter_config.start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = filter_config.end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        filters.append(f'timestamp>="{start_str}"')
        filters.append(f'timestamp<"{end_str}"')
    else:
        # 過去N日間
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(days=filter_config.days)
        start_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        filters.append(f'timestamp>="{start_str}"')

    return " AND ".join(filters)


def parse_resource_name(resource_name: str) -> dict[str, str] | None:
    """リソース名からproject/dataset/tableを抽出する。

    Args:
        resource_name: BigQueryリソース名
            (例: "projects/my-project/datasets/my_dataset/tables/my_table")

    Returns:
        抽出された情報の辞書、またはパース失敗時はNone
    """
    if not resource_name:
        return None

    match = _RESOURCE_NAME_PATTERN.search(resource_name)
    if match:
        return {
            "project_id": match.group("project_id"),
            "dataset_id": match.group("dataset_id"),
            "table_id": match.group("table_id"),
        }
    return None


def aggregate_table_access_counts(
    parsed_entries: list[dict[str, str]],
) -> list[TableAccessCount]:
    """パース済みエントリをテーブル単位で集計する。

    Args:
        parsed_entries: パース済みのエントリリスト

    Returns:
        TableAccessCountのリスト（集計済み）
    """
    if not parsed_entries:
        return []

    # (project_id, dataset_id, table_id) をキーにカウント
    counter: Counter[tuple[str, str, str]] = Counter()
    for entry in parsed_entries:
        key = (entry["project_id"], entry["dataset_id"], entry["table_id"])
        counter[key] += 1

    # TableAccessCountリストに変換
    results: list[TableAccessCount] = []
    for (project_id, dataset_id, table_id), count in counter.items():
        results.append(
            TableAccessCount(
                project_id=project_id,
                dataset_id=dataset_id,
                table_id=table_id,
                access_count=count,
                source=DataSource.AUDIT_LOG,
            )
        )

    # 参照回数の降順でソート
    results.sort(key=lambda x: x.access_count, reverse=True)
    return results


class AuditLogAdapter:
    """Cloud Audit Logsからテーブル参照情報を取得するアダプター。

    Cloud Logging APIを使用してBigQueryのtableDataReadイベントを取得し、
    テーブルの参照回数を集計する。

    Example:
        >>> from google.cloud import logging as cloud_logging
        >>> client = cloud_logging.Client()
        >>> adapter = AuditLogAdapter(logging_client=client)
        >>> results = adapter.fetch_table_access("my-project", FilterConfig())
    """

    def __init__(
        self,
        logging_client: cloud_logging.Client,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        retry_delay: float = _DEFAULT_RETRY_DELAY,
    ) -> None:
        """初期化。

        Args:
            logging_client: Cloud Loggingクライアント
            max_retries: 最大リトライ回数（デフォルト: 3）
            retry_delay: 初期リトライ遅延秒数（デフォルト: 1.0）
        """
        self._client = logging_client
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    def fetch_table_access(
        self,
        project_id: str,
        filter_config: FilterConfig,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> list[TableAccessCount]:
        """Cloud Audit Logsからテーブル参照回数を取得する。

        Args:
            project_id: GCPプロジェクトID
            filter_config: フィルタリング条件
            progress_callback: 進捗コールバック関数

        Returns:
            TableAccessCountのリスト

        Raises:
            PermissionDeniedError: logging.logEntries.list権限がない場合
            NetworkError: ネットワークエラーが発生した場合
        """
        log_filter = build_log_filter(
            project_id=project_id,
            filter_config=filter_config,
        )

        # リトライ付きでログエントリを取得
        entries = self._list_entries_with_retry(
            project_id=project_id,
            log_filter=log_filter,
        )

        # ログエントリをパース
        parsed_entries: list[dict[str, str]] = []
        processed_count = 0

        for entry in entries:
            resource_name = self._extract_resource_name(entry)
            if resource_name:
                parsed = parse_resource_name(resource_name)
                if parsed:
                    parsed_entries.append(parsed)

            processed_count += 1
            if progress_callback is not None:
                progress_callback(
                    processed_count,
                    processed_count,  # 総数は不明なので現在のカウントを使用
                    f"Processing log entry {processed_count}",
                )

        # 0件の場合は警告をログ出力
        if not parsed_entries:
            _logger.warning(
                "Audit Logs からテーブル参照情報が取得できませんでした。"
                "Data Access ログが有効化されていない可能性があります。"
            )

        # 集計して返す
        return aggregate_table_access_counts(parsed_entries)

    def _list_entries_with_retry(
        self,
        project_id: str,
        log_filter: str,
    ) -> Iterator[object]:
        """リトライ付きでログエントリを取得する。

        Args:
            project_id: GCPプロジェクトID
            log_filter: フィルタ文字列

        Yields:
            ログエントリ (TextEntry | StructEntry | ProtobufEntry | LogEntry)

        Raises:
            PermissionDeniedError: 権限エラーの場合
            NetworkError: ネットワークエラーの場合
        """
        retry_count = 0
        delay = self._retry_delay

        while True:
            try:
                # list_entries returns various log entry types
                entries: Iterator[object] = iter(
                    self._client.list_entries(
                        filter_=log_filter,
                        resource_names=[f"projects/{project_id}"],
                    )
                )
                # イテレータを消費して結果を返す
                for entry in entries:
                    yield entry
                return
            except api_exceptions.PermissionDenied as e:
                raise PermissionDeniedError(
                    "Cloud Audit Logs へのアクセス権限がありません。"
                    "'roles/logging.viewer' ロールまたは "
                    "'logging.logEntries.list' 権限が必要です。"
                ) from e
            except api_exceptions.ResourceExhausted as e:
                retry_count += 1
                if retry_count > self._max_retries:
                    raise NetworkError(
                        "Cloud Logging API のレート制限に達しました。"
                        "しばらく待ってから再試行してください。"
                    ) from e
                _logger.warning(
                    f"Rate limit exceeded, retrying in {delay} seconds... "
                    f"(attempt {retry_count}/{self._max_retries})"
                )
                time.sleep(delay)
                delay *= _BACKOFF_MULTIPLIER
            except api_exceptions.ServiceUnavailable as e:
                raise NetworkError() from e

    def _extract_resource_name(self, entry: object) -> str | None:
        """ログエントリからリソース名を抽出する。

        Args:
            entry: ログエントリ

        Returns:
            リソース名、または抽出できない場合はNone
        """
        try:
            # payloadがdict形式の場合 (StructEntry)
            if hasattr(entry, "payload"):
                payload: object = getattr(entry, "payload")
                if isinstance(payload, dict) and "resourceName" in payload:
                    # google-cloud-loggingライブラリの型定義が不完全なため
                    # dict[str, object]として扱う
                    typed_payload = cast(dict[str, object], payload)
                    raw_value: object = typed_payload.get("resourceName")
                    if isinstance(raw_value, str):
                        return raw_value
            # proto形式の場合 (ProtobufEntry)
            if hasattr(entry, "proto_payload"):
                proto_payload: object = getattr(entry, "proto_payload")
                if hasattr(proto_payload, "resource_name"):
                    resource_name_attr: object = getattr(proto_payload, "resource_name")
                    if isinstance(resource_name_attr, str):
                        return resource_name_attr
        except Exception:
            _logger.debug(f"Failed to extract resource name from entry: {entry}")
        return None
