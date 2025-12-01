"""ドメインモデル定義。

BigQuery のデータセットとテーブルのメタデータを表現する型安全なデータ構造。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DatasetInfo(BaseModel):
    """BigQuery データセットのメタデータを表現するイミュータブルなデータ構造。

    Attributes:
        dataset_id: BigQuery データセット ID
        project: GCP プロジェクト ID
        full_path: "project.dataset" 形式のフルパス
        created: データセット作成日時（オプショナル）
        modified: データセット最終更新日時（オプショナル）
        location: データセットのロケーション（オプショナル）
    """

    model_config = ConfigDict(frozen=True)

    dataset_id: str
    project: str
    full_path: str
    created: datetime | None
    modified: datetime | None
    location: str | None
