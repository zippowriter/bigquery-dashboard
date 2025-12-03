"""バッチ処理用設定モジュール。

環境変数からバッチ処理に必要な設定を読み込む。
"""

import os

from pathlib import Path

from pydantic import BaseModel, Field


class BatchConfig(BaseModel):
    """バッチ処理の設定。

    環境変数から設定値を読み込む。
    """

    project_id: str = Field(
        default_factory=lambda: os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    )
    region: str = Field(
        default_factory=lambda: os.environ.get("BIGQUERY_REGION", "region-us")
    )
    cache_dir: Path = Field(
        default_factory=lambda: Path(
            os.environ.get("CACHE_DIR", "/tmp/bigquery-dashboard")
        )
    )
