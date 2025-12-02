"""API操作の共通エラーハンドリング。

このモジュールは、BigQueryおよびCloud Logging API操作のための
集中的なエラーハンドリングとユーザーフレンドリーなエラーメッセージフォーマットを提供する。
"""

from bq_table_reference.domain.exceptions import (
    AuthenticationError,
    DatasetLoaderError,
    NetworkError,
    PermissionDeniedError,
)


def format_authentication_error() -> str:
    """認証エラーメッセージをフォーマットする。

    Returns:
        認証問題の解決方法を提案するユーザーフレンドリーなメッセージ。
    """
    return (
        "Authentication failed. Please run 'gcloud auth application-default login' "
        "to set up your credentials, then retry the operation."
    )


def format_network_error() -> str:
    """ネットワークエラーメッセージをフォーマットする。

    Returns:
        ネットワーク接続問題に対するユーザーフレンドリーなメッセージ。
    """
    return (
        "A network error occurred while connecting to the BigQuery API. "
        "Please check your internet connection and retry. "
        "If the problem persists, try again later."
    )


def format_permission_error() -> str:
    """権限拒否エラーメッセージをフォーマットする。

    Returns:
        必要なIAMロールを提案するユーザーフレンドリーなメッセージ。
    """
    return (
        "Permission denied. Ensure your account has the required IAM roles:\n"
        "- For INFORMATION_SCHEMA: 'roles/bigquery.resourceViewer' or "
        "'bigquery.jobs.listAll' permission\n"
        "- For Audit Logs: 'roles/logging.viewer' or "
        "'logging.logEntries.list' permission"
    )


def format_unexpected_error(error: Exception) -> str:
    """予期しないエラーメッセージをフォーマットする。

    Args:
        error: 発生した元の例外。

    Returns:
        予期しないエラーに対するガイダンス付きのユーザーフレンドリーなメッセージ。
    """
    error_type = type(error).__name__
    error_message = str(error)

    return (
        f"An unexpected error occurred: {error_type}\n"
        f"Details: {error_message}\n"
        "Please check the application logs for more information. "
        "If this error persists, please report it with the error details above."
    )


def handle_api_error(error: Exception) -> str:
    """APIエラーを処理してユーザーフレンドリーなメッセージを返す。

    この関数はAPI操作からの例外を受け取り、
    問題解決方法のガイダンス付きの適切なユーザーフレンドリーなエラーメッセージを返す。

    Args:
        error: API操作中に発生した例外。

    Returns:
        ユーザーフレンドリーなエラーメッセージ文字列。

    Example:
        >>> from bq_table_reference.domain.exceptions import NetworkError
        >>> error = NetworkError("Connection timeout")
        >>> message = handle_api_error(error)
        >>> print(message)
        A network error occurred while connecting to the BigQuery API...
    """
    if isinstance(error, AuthenticationError):
        return format_authentication_error()

    if isinstance(error, PermissionDeniedError):
        return format_permission_error()

    if isinstance(error, NetworkError):
        return format_network_error()

    if isinstance(error, DatasetLoaderError):
        # Other DatasetLoaderError subclasses
        return str(error)

    # Unexpected error
    return format_unexpected_error(error)
