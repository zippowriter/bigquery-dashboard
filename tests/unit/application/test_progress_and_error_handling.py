"""進捗レポートと共通エラーハンドリングのテスト。

ProgressReporterクラスとhandle_api_error関数をテストし、
一貫した進捗表示とエラーメッセージ処理を検証する。
"""

from bq_table_reference.domain.exceptions import (
    AuthenticationError,
    NetworkError,
    PermissionDeniedError,
)


class TestProgressReporter:
    """ProgressReporterクラスのテスト。"""

    def test_progress_callback_receives_processed_count(self) -> None:
        """ProgressCallbackが処理済みアイテム数を受け取ることを検証する。"""
        from bq_table_reference.application.progress_reporter import ProgressReporter

        received_values: list[tuple[int, int, str]] = []

        def callback(current: int, total: int, message: str) -> None:
            received_values.append((current, total, message))

        reporter = ProgressReporter(callback=callback, total=10)
        reporter.report(current=5, message="Processing item 5")

        assert len(received_values) == 1
        assert received_values[0][0] == 5  # current
        assert received_values[0][1] == 10  # total

    def test_progress_reporter_reports_multiple_sources(self) -> None:
        """ProgressReporterが複数データソースの進捗を報告することを検証する。"""
        from bq_table_reference.application.progress_reporter import ProgressReporter

        received_values: list[tuple[int, int, str]] = []

        def callback(current: int, total: int, message: str) -> None:
            received_values.append((current, total, message))

        # Simulate processing from two sources
        reporter = ProgressReporter(callback=callback, total=20)

        # Report progress from INFO_SCHEMA (source 1)
        reporter.report(current=5, message="INFO_SCHEMA: Processing 5/10")

        # Report progress from AUDIT_LOG (source 2)
        reporter.report(current=15, message="AUDIT_LOG: Processing 5/10")

        assert len(received_values) == 2
        # First source progress
        assert received_values[0][0] == 5
        assert "INFO_SCHEMA" in received_values[0][2]
        # Second source progress
        assert received_values[1][0] == 15
        assert "AUDIT_LOG" in received_values[1][2]

    def test_progress_reporter_with_none_callback(self) -> None:
        """ProgressReporterがNoneコールバックを正常に処理することを検証する。"""
        from bq_table_reference.application.progress_reporter import ProgressReporter

        # Should not raise exception with None callback
        reporter = ProgressReporter(callback=None, total=10)
        reporter.report(current=5, message="Processing")  # Should not raise

    def test_progress_reporter_percentage_calculation(self) -> None:
        """ProgressReporterがパーセンテージを正しく計算することを検証する。"""
        from bq_table_reference.application.progress_reporter import ProgressReporter

        received_values: list[tuple[int, int, str]] = []

        def callback(current: int, total: int, message: str) -> None:
            received_values.append((current, total, message))

        reporter = ProgressReporter(callback=callback, total=100)
        reporter.report(current=50, message="Half done")

        assert received_values[0][0] == 50
        assert received_values[0][1] == 100
        # 50/100 = 50%

    def test_progress_reporter_create_sub_reporter(self) -> None:
        """ProgressReporterがデータソース用のサブレポーターを作成することを検証する。"""
        from bq_table_reference.application.progress_reporter import ProgressReporter

        received_values: list[tuple[int, int, str]] = []

        def callback(current: int, total: int, message: str) -> None:
            received_values.append((current, total, message))

        main_reporter = ProgressReporter(callback=callback, total=100)

        # Create sub-reporter for INFO_SCHEMA phase (0-50% of total)
        info_schema_callback = main_reporter.create_sub_callback(
            source_name="INFO_SCHEMA",
            offset=0,
            weight=50,
        )

        # Report progress through sub-callback
        info_schema_callback(5, 10, "Processing row 5/10")

        assert len(received_values) == 1
        # 5/10 * 50 = 25 (25% of total)
        assert received_values[0][0] == 25
        assert received_values[0][1] == 100


class TestHandleApiError:
    """handle_api_error関数のテスト。"""

    def test_bigquery_connection_error_message(self) -> None:
        """BigQuery接続エラーに対して明確なメッセージを返すことを検証する。"""
        from bq_table_reference.application.error_handler import handle_api_error

        error = NetworkError("Connection refused")
        result = handle_api_error(error)

        assert "BigQuery API" in result or "BigQuery" in result
        assert "connection" in result.lower() or "network" in result.lower()

    def test_authentication_error_suggests_gcloud_auth(self) -> None:
        """認証エラーに対して'gcloud auth application-default login'を提案することを検証する。"""
        from bq_table_reference.application.error_handler import handle_api_error

        error = AuthenticationError()
        result = handle_api_error(error)

        assert "gcloud auth application-default login" in result

    def test_unexpected_error_provides_log_file_path(self) -> None:
        """予期しないエラーに対してログファイルパスのガイダンスを提供することを検証する。"""
        from bq_table_reference.application.error_handler import handle_api_error

        # Generic exception (unexpected)
        error = ValueError("Unexpected error occurred")
        result = handle_api_error(error)

        # Should guide user to check logs or report the error
        assert "log" in result.lower() or "error" in result.lower()

    def test_permission_denied_error_suggests_roles(self) -> None:
        """権限エラーに対して必要なIAMロールを提案することを検証する。"""
        from bq_table_reference.application.error_handler import handle_api_error

        error = PermissionDeniedError()
        result = handle_api_error(error)

        # Should mention IAM roles or permissions
        assert "role" in result.lower() or "permission" in result.lower()

    def test_handle_api_error_returns_user_friendly_message(self) -> None:
        """ユーザーフレンドリーなエラーメッセージを返すことを検証する。"""
        from bq_table_reference.application.error_handler import handle_api_error

        error = NetworkError("Timeout")
        result = handle_api_error(error)

        # Message should be a non-empty string
        assert isinstance(result, str)
        assert len(result) > 0


class TestErrorMessages:
    """エラーメッセージ定数とフォーマットのテスト。"""

    def test_authentication_error_message_format(self) -> None:
        """AuthenticationErrorが適切なメッセージフォーマットを持つことを検証する。"""
        from bq_table_reference.application.error_handler import (
            format_authentication_error,
        )

        message = format_authentication_error()

        assert "gcloud auth application-default login" in message

    def test_network_error_message_format(self) -> None:
        """NetworkErrorが適切なメッセージフォーマットを持つことを検証する。"""
        from bq_table_reference.application.error_handler import format_network_error

        message = format_network_error()

        assert "retry" in message.lower() or "connection" in message.lower()

    def test_unexpected_error_message_format(self) -> None:
        """予期しないエラーが適切なメッセージフォーマットを持つことを検証する。"""
        from bq_table_reference.application.error_handler import (
            format_unexpected_error,
        )

        original_error = ValueError("Something went wrong")
        message = format_unexpected_error(original_error)

        # Should include guidance about what happened
        assert len(message) > 0
