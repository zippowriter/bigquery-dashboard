"""バッチ処理メインモジュール。

バッチ処理のエントリーポイントを提供する。
"""

from src.batch.config import BatchConfig
from src.batch.runner import BatchRunner


def main() -> None:
    """バッチ処理のメインエントリーポイント。

    環境変数から設定を読み込み、バッチ処理を実行する。
    """
    config = BatchConfig()
    runner = BatchRunner(config)
    runner.run()


if __name__ == "__main__":
    main()
