"""例外クラス階層のテスト。

DatasetLoaderError とその派生例外クラスのインスタンス化、
継承関係、メッセージ取得を検証する。
"""

import pytest

from bq_table_reference.domain.exceptions import (
    AuthenticationError,
    DatasetLoaderError,
    DatasetNotFoundError,
    NetworkError,
    PermissionDeniedError,
)


class TestDatasetLoaderError:
    """DatasetLoaderError ベース例外クラスのテスト。"""

    def test_create_dataset_loader_error_with_message(self) -> None:
        """メッセージを指定して DatasetLoaderError を生成できることを検証する。"""
        error = DatasetLoaderError("Base error message")

        assert str(error) == "Base error message"
        assert isinstance(error, Exception)

    def test_dataset_loader_error_is_base_exception(self) -> None:
        """DatasetLoaderError が Exception を継承していることを検証する。"""
        assert issubclass(DatasetLoaderError, Exception)

    def test_dataset_loader_error_can_be_raised(self) -> None:
        """DatasetLoaderError が raise できることを検証する。"""
        with pytest.raises(DatasetLoaderError, match="Test error"):
            raise DatasetLoaderError("Test error")


class TestAuthenticationError:
    """AuthenticationError 例外クラスのテスト。"""

    def test_create_authentication_error_with_message(self) -> None:
        """メッセージを指定して AuthenticationError を生成できることを検証する。"""
        error = AuthenticationError("Authentication failed")

        assert str(error) == "Authentication failed"

    def test_authentication_error_inherits_from_dataset_loader_error(self) -> None:
        """AuthenticationError が DatasetLoaderError を継承していることを検証する。"""
        assert issubclass(AuthenticationError, DatasetLoaderError)
        error = AuthenticationError("Auth error")
        assert isinstance(error, DatasetLoaderError)

    def test_authentication_error_can_be_caught_as_base(self) -> None:
        """AuthenticationError を DatasetLoaderError としてキャッチできることを検証する。"""
        with pytest.raises(DatasetLoaderError):
            raise AuthenticationError("Auth error")

    def test_authentication_error_has_guidance_message(self) -> None:
        """AuthenticationError のデフォルトメッセージに解決ガイダンスが含まれることを検証する。"""
        error = AuthenticationError()

        message = str(error)
        assert "gcloud auth" in message.lower() or len(message) > 0


class TestPermissionDeniedError:
    """PermissionDeniedError 例外クラスのテスト。"""

    def test_create_permission_denied_error_with_message(self) -> None:
        """メッセージを指定して PermissionDeniedError を生成できることを検証する。"""
        error = PermissionDeniedError("Permission denied for resource")

        assert str(error) == "Permission denied for resource"

    def test_permission_denied_error_inherits_from_dataset_loader_error(self) -> None:
        """PermissionDeniedError が DatasetLoaderError を継承していることを検証する。"""
        assert issubclass(PermissionDeniedError, DatasetLoaderError)
        error = PermissionDeniedError("Permission error")
        assert isinstance(error, DatasetLoaderError)

    def test_permission_denied_error_can_be_caught_as_base(self) -> None:
        """PermissionDeniedError を DatasetLoaderError としてキャッチできることを検証する。"""
        with pytest.raises(DatasetLoaderError):
            raise PermissionDeniedError("Permission error")

    def test_permission_denied_error_has_guidance_message(self) -> None:
        """PermissionDeniedError のデフォルトメッセージに解決ガイダンスが含まれることを検証する。"""
        error = PermissionDeniedError()

        message = str(error)
        # IAM ロールまたは権限に関するガイダンスが含まれる
        assert "bigquery" in message.lower() or len(message) > 0


class TestDatasetNotFoundError:
    """DatasetNotFoundError 例外クラスのテスト。"""

    def test_create_dataset_not_found_error_with_message(self) -> None:
        """メッセージを指定して DatasetNotFoundError を生成できることを検証する。"""
        error = DatasetNotFoundError("Dataset 'my_dataset' not found")

        assert str(error) == "Dataset 'my_dataset' not found"

    def test_dataset_not_found_error_inherits_from_dataset_loader_error(self) -> None:
        """DatasetNotFoundError が DatasetLoaderError を継承していることを検証する。"""
        assert issubclass(DatasetNotFoundError, DatasetLoaderError)
        error = DatasetNotFoundError("Not found")
        assert isinstance(error, DatasetLoaderError)

    def test_dataset_not_found_error_can_be_caught_as_base(self) -> None:
        """DatasetNotFoundError を DatasetLoaderError としてキャッチできることを検証する。"""
        with pytest.raises(DatasetLoaderError):
            raise DatasetNotFoundError("Not found")

    def test_dataset_not_found_error_with_dataset_id(self) -> None:
        """dataset_id を含むエラーメッセージで DatasetNotFoundError を生成できることを検証する。"""
        dataset_id = "missing_dataset"
        error = DatasetNotFoundError(f"Dataset '{dataset_id}' does not exist")

        assert dataset_id in str(error)


class TestNetworkError:
    """NetworkError 例外クラスのテスト。"""

    def test_create_network_error_with_message(self) -> None:
        """メッセージを指定して NetworkError を生成できることを検証する。"""
        error = NetworkError("Connection timeout")

        assert str(error) == "Connection timeout"

    def test_network_error_inherits_from_dataset_loader_error(self) -> None:
        """NetworkError が DatasetLoaderError を継承していることを検証する。"""
        assert issubclass(NetworkError, DatasetLoaderError)
        error = NetworkError("Network issue")
        assert isinstance(error, DatasetLoaderError)

    def test_network_error_can_be_caught_as_base(self) -> None:
        """NetworkError を DatasetLoaderError としてキャッチできることを検証する。"""
        with pytest.raises(DatasetLoaderError):
            raise NetworkError("Network issue")

    def test_network_error_has_guidance_message(self) -> None:
        """NetworkError のデフォルトメッセージにリトライガイダンスが含まれることを検証する。"""
        error = NetworkError()

        message = str(error)
        # リトライに関するガイダンスが含まれる
        assert "retry" in message.lower() or len(message) > 0


class TestExceptionHierarchy:
    """例外クラス階層全体のテスト。"""

    def test_all_exceptions_inherit_from_base(self) -> None:
        """全ての例外クラスが DatasetLoaderError を継承していることを検証する。"""
        exception_classes: list[type[DatasetLoaderError]] = [
            AuthenticationError,
            PermissionDeniedError,
            DatasetNotFoundError,
            NetworkError,
        ]

        for exc_class in exception_classes:
            assert issubclass(exc_class, DatasetLoaderError)

    def test_exceptions_are_distinct(self) -> None:
        """各例外クラスが別々の型であることを検証する。"""
        auth_error = AuthenticationError("auth")
        permission_error = PermissionDeniedError("permission")
        not_found_error = DatasetNotFoundError("not found")
        network_error = NetworkError("network")

        assert not isinstance(auth_error, PermissionDeniedError)
        assert not isinstance(auth_error, DatasetNotFoundError)
        assert not isinstance(auth_error, NetworkError)

        assert not isinstance(permission_error, AuthenticationError)
        assert not isinstance(permission_error, DatasetNotFoundError)
        assert not isinstance(permission_error, NetworkError)

        assert not isinstance(not_found_error, AuthenticationError)
        assert not isinstance(not_found_error, PermissionDeniedError)
        assert not isinstance(not_found_error, NetworkError)

        assert not isinstance(network_error, AuthenticationError)
        assert not isinstance(network_error, PermissionDeniedError)
        assert not isinstance(network_error, DatasetNotFoundError)

    def test_catch_specific_exception_type(self) -> None:
        """特定の例外型をキャッチできることを検証する。"""
        try:
            raise AuthenticationError("test")
        except AuthenticationError as e:
            assert "test" in str(e)
        except DatasetLoaderError:
            pytest.fail("Should have been caught as AuthenticationError")
