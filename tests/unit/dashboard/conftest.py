"""テスト用の共通フィクスチャ。"""

from typing import Any

import pytest


class FakeLogger:
    """テスト用のFakeロガー。

    ログメッセージを記録し、テストで検証可能にする。
    """

    def __init__(self) -> None:
        """FakeLoggerを初期化する。"""
        self.messages: list[tuple[str, str, dict[str, Any]]] = []

    def debug(self, message: str, **kwargs: Any) -> None:
        """DEBUGレベルのログを記録する。"""
        self.messages.append(("DEBUG", message, kwargs))

    def info(self, message: str, **kwargs: Any) -> None:
        """INFOレベルのログを記録する。"""
        self.messages.append(("INFO", message, kwargs))

    def warning(self, message: str, **kwargs: Any) -> None:
        """WARNINGレベルのログを記録する。"""
        self.messages.append(("WARNING", message, kwargs))

    def error(self, message: str, **kwargs: Any) -> None:
        """ERRORレベルのログを記録する。"""
        self.messages.append(("ERROR", message, kwargs))

    def has_message(self, level: str, message: str) -> bool:
        """指定されたレベルとメッセージが記録されているか確認する。

        Args:
            level: ログレベル（DEBUG, INFO, WARNING, ERROR）
            message: ログメッセージ（部分一致）

        Returns:
            該当するログが存在する場合True
        """
        return any(lvl == level and message in msg for lvl, msg, _ in self.messages)


@pytest.fixture
def fake_logger() -> FakeLogger:
    """テスト用のFakeLoggerを提供する。"""
    return FakeLogger()
