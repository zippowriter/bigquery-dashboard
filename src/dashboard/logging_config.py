"""ロギング設定モジュール。

アプリケーション全体で使用するロガーインスタンスを管理する。
"""

import logging
from functools import lru_cache

from src.dashboard.domain.logging import Logger
from src.dashboard.infra.console_logger import ConsoleLogger


@lru_cache(maxsize=1)
def get_logger() -> Logger:
    """アプリケーション共通のロガーを取得する。

    シングルトンパターンでロガーを提供する。
    将来的にCloud Logging等に切り替える場合はここを変更する。

    Returns:
        Loggerプロトコル準拠のロガーインスタンス
    """
    return ConsoleLogger(
        name="bigquery-dashboard",
        level=logging.DEBUG,
    )
