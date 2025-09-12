import pandera as pa

from pandera import DataFrameModel


class UserWatchTime(DataFrameModel):
    user_id: str = pa.Field(nullable=False)
    total_watch_time: int = pa.Field(nullable=False)
