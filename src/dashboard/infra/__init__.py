"""インフラ層モジュール。

外部システムとの通信、技術的詳細の実装を提供する。
"""

from src.shared.infra.bigquery import BigQueryTableRepository

__all__ = [
    "BigQueryTableRepository",
]
