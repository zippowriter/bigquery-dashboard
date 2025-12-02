"""コンソールロガー実装。

Python標準loggingモジュールを使用したロガー。
"""

import logging
from typing import Any


class ConsoleLogger:
    """コンソール出力のロガー実装。

    Python標準loggingモジュールをラップし、
    domain層のLoggerプロトコルに準拠する。
    """

    def __init__(
        self,
        name: str = "bigquery-dashboard",
        level: int = logging.INFO,
    ) -> None:
        """ロガーを初期化する。

        Args:
            name: ロガー名
            level: ログレベル（logging.DEBUG, INFO等）
        """
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)

        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(level)
            formatter = logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    def _format_kwargs(self, kwargs: dict[str, Any]) -> str:
        """kwargsをログ出力用文字列に変換する。

        Args:
            kwargs: 追加のコンテキスト情報

        Returns:
            フォーマット済み文字列（空の場合は空文字列）
        """
        if not kwargs:
            return ""
        return " | " + " ".join(f"{k}={v}" for k, v in kwargs.items())

    def debug(self, message: str, **kwargs: Any) -> None:
        """DEBUGレベルのログを出力する。

        Args:
            message: ログメッセージ
            **kwargs: 追加のコンテキスト情報
        """
        self._logger.debug(f"{message}{self._format_kwargs(kwargs)}")

    def info(self, message: str, **kwargs: Any) -> None:
        """INFOレベルのログを出力する。

        Args:
            message: ログメッセージ
            **kwargs: 追加のコンテキスト情報
        """
        self._logger.info(f"{message}{self._format_kwargs(kwargs)}")

    def warning(self, message: str, **kwargs: Any) -> None:
        """WARNINGレベルのログを出力する。

        Args:
            message: ログメッセージ
            **kwargs: 追加のコンテキスト情報
        """
        self._logger.warning(f"{message}{self._format_kwargs(kwargs)}")

    def error(self, message: str, **kwargs: Any) -> None:
        """ERRORレベルのログを出力する。

        Args:
            message: ログメッセージ
            **kwargs: 追加のコンテキスト情報
        """
        self._logger.error(f"{message}{self._format_kwargs(kwargs)}")
