from pydantic import BaseModel

from domain.value_objects.table_id import TableId
from domain.value_objects.table_type import TableType


class Table(BaseModel):
    """BigQueryのテーブルのモデル"""

    table_id: TableId
    table_type: TableType


class CheckedTable(Table):
    """参照回数が調べられたテーブルのモデル"""

    job_count: int
    unique_user: int


class CandidateTable(Table):
    """削除候補となるテーブルのモデル"""

    data_owner: str
