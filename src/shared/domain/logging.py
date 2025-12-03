"""ロギングインターフェース定義。

ロギング機能の抽象インターフェースをProtocolで定義する。
"""

from typing import Any, Protocol


class Logger(Protocol):
    """ロガーのインターフェース。

    アプリケーション全体で使用するロギング機能の抽象化。
    実装はinfra層で提供される。
    """

    def debug(self, message: str, **kwargs: Any) -> None:
        """DEBUGレベルのログを出力する。

        Args:
            message: ログメッセージ
            **kwargs: 追加のコンテキスト情報
        """
        ...

    def info(self, message: str, **kwargs: Any) -> None:
        """INFOレベルのログを出力する。

        Args:
            message: ログメッセージ
            **kwargs: 追加のコンテキスト情報
        """
        ...

    def warning(self, message: str, **kwargs: Any) -> None:
        """WARNINGレベルのログを出力する。

        Args:
            message: ログメッセージ
            **kwargs: 追加のコンテキスト情報
        """
        ...

    def error(self, message: str, **kwargs: Any) -> None:
        """ERRORレベルのログを出力する。

        Args:
            message: ログメッセージ
            **kwargs: 追加のコンテキスト情報
        """
        ...
