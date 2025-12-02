"""テーブルアクセスカウント用の進捗レポート機能。

このモジュールは、テーブルアクセスカウント操作中に
複数のデータソースにわたる進捗レポートを管理するProgressReporterクラスを提供する。
"""

from collections.abc import Callable


# Type alias for progress callback function
ProgressCallback = Callable[[int, int, str], None]


class ProgressReporter:
    """テーブルアクセスカウント操作用の進捗レポーター。

    このクラスは、データソースアダプターからの更新を受け取り、
    ユーザー提供のコールバックに転送することで進捗レポートを管理する。
    複数のデータソースからの進捗レポートをサポートする。

    Example:
        >>> def my_callback(current: int, total: int, message: str) -> None:
        ...     print(f"Progress: {current}/{total} - {message}")
        >>> reporter = ProgressReporter(callback=my_callback, total=100)
        >>> reporter.report(current=50, message="Half done")
        Progress: 50/100 - Half done
    """

    def __init__(
        self,
        callback: ProgressCallback | None,
        total: int,
    ) -> None:
        """進捗レポーターを初期化する。

        Args:
            callback: 進捗更新を受け取るコールバック関数。
                Noneの場合、進捗レポートは無視される。
            total: 全ソースで処理するアイテムの総数。
        """
        self._callback = callback
        self._total = total

    def report(self, current: int, message: str) -> None:
        """コールバックに進捗を報告する。

        Args:
            current: 現在の進捗値。
            message: 現在の操作を説明するメッセージ。
        """
        if self._callback is not None:
            self._callback(current, self._total, message)

    def create_sub_callback(
        self,
        source_name: str,
        offset: int,
        weight: int,
    ) -> ProgressCallback:
        """特定のデータソース用のサブコールバックを作成する。

        データソースアダプターに渡せるコールバックを作成する。
        サブコールバックは、オフセットと重みに基づいて
        アダプターのローカル進捗を全体進捗に変換する。

        Args:
            source_name: データソースの名前（メッセージのプレフィックス用）。
            offset: 全体進捗における開始オフセット（0-100スケール）。
            weight: このソースが全体進捗に寄与する重み（パーセンテージ）。

        Returns:
            データソースアダプターに渡すのに適したコールバック関数。

        Example:
            >>> reporter = ProgressReporter(callback=print_progress, total=100)
            >>> # INFO_SCHEMAは進捗の最初の50%を取得
            >>> info_callback = reporter.create_sub_callback("INFO_SCHEMA", offset=0, weight=50)
            >>> # AUDIT_LOGは次の50%を取得
            >>> audit_callback = reporter.create_sub_callback("AUDIT_LOG", offset=50, weight=50)
        """

        def sub_callback(current: int, total: int, message: str) -> None:
            if total > 0:
                # Calculate the scaled progress
                # current/total gives the fraction complete for this source
                # Multiply by weight to get the contribution to overall progress
                # Add offset for the starting position
                scaled_current = offset + int((current / total) * weight)
            else:
                scaled_current = offset

            # Prefix message with source name
            prefixed_message = f"{source_name}: {message}"

            self.report(current=scaled_current, message=prefixed_message)

        return sub_callback
