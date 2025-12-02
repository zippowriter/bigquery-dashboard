"""Application configuration module."""

import os

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """Application configuration.

    Manages dashboard settings including title, host, port, and debug mode.
    """

    title: str = Field(
        default="BigQueryテーブル利用状況",
        min_length=1,
        description="ダッシュボードのタイトル",
    )
    host: str = Field(
        default="127.0.0.1",
        description="サーバーバインドアドレス",
    )
    port: int = Field(
        default=8050,
        ge=1024,
        le=65535,
        description="サーバーポート番号",
    )
    debug: bool = Field(
        default=True,
        description="デバッグモードの有効/無効",
    )
    project_id: str | None = Field(
        default_factory=lambda: os.environ.get("GOOGLE_CLOUD_PROJECT"),
        description="BigQuery対象プロジェクトID",
    )
    region: str = Field(
        default_factory=lambda: os.environ.get("BIGQUERY_REGION", "region-us"),
        description="BigQueryリージョン（INFORMATION_SCHEMAクエリ用）",
    )
