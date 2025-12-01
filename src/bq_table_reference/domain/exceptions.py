"""カスタム例外クラス階層。

BigQuery 操作に関するエラーを分類し、
ユーザーフレンドリーなメッセージを提供する例外クラス群。
"""


class DatasetLoaderError(Exception):
    """DatasetLoader 操作のベース例外クラス。

    全ての DatasetLoader 関連エラーの基底クラス。
    このクラスを catch することで、全ての派生例外をまとめて処理できる。
    """

    pass


class AuthenticationError(DatasetLoaderError):
    """認証に失敗した場合に発生する例外。

    有効な認証情報が見つからない場合や、認証情報が無効な場合に発生する。
    """

    def __init__(self, message: str | None = None) -> None:
        """AuthenticationError を初期化する。

        Args:
            message: エラーメッセージ。None の場合はデフォルトメッセージを使用。
        """
        if message is None:
            message = (
                "認証に失敗しました。'gcloud auth application-default login' を実行して "
                "認証情報を設定してください。"
            )
        super().__init__(message)


class PermissionDeniedError(DatasetLoaderError):
    """必要な権限がない場合に発生する例外。

    BigQuery リソースへのアクセスに必要な IAM 権限がない場合に発生する。
    """

    def __init__(self, message: str | None = None) -> None:
        """PermissionDeniedError を初期化する。

        Args:
            message: エラーメッセージ。None の場合はデフォルトメッセージを使用。
        """
        if message is None:
            message = (
                "アクセス権限がありません。BigQuery へのアクセスには "
                "'roles/bigquery.dataViewer' または 'roles/bigquery.user' ロールが必要です。"
            )
        super().__init__(message)


class DatasetNotFoundError(DatasetLoaderError):
    """指定されたデータセットが存在しない場合に発生する例外。

    指定されたデータセット ID が BigQuery 上に存在しない場合に発生する。
    """

    pass


class NetworkError(DatasetLoaderError):
    """ネットワークエラーが発生した場合に発生する例外。

    BigQuery API への接続に失敗した場合や、タイムアウトが発生した場合に発生する。
    """

    def __init__(self, message: str | None = None) -> None:
        """NetworkError を初期化する。

        Args:
            message: エラーメッセージ。None の場合はデフォルトメッセージを使用。
        """
        if message is None:
            message = (
                "ネットワークエラーが発生しました。接続を確認し、しばらく待ってから "
                "retry してください。"
            )
        super().__init__(message)
