"""バッチ処理エントリーポイント。

BigQueryからデータを取得し、CSVキャッシュに保存する。
cron等で定期実行することを想定。

Usage:
    uv run batch
    # または
    python batch.py
"""

from src.batch.main import main


if __name__ == "__main__":
    main()
