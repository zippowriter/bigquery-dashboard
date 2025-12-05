from pydantic import BaseModel

from domain.value_objects.table_id import TableId
from domain.value_objects.table_type import TableType


class Table(BaseModel):
    """BigQueryのテーブルのモデル"""

    table_id: TableId
    table_type: TableType


class CheckedTable(BaseModel):
    """参照回数が調べられたテーブルのモデル"""

    table_id: TableId
    table_type: TableType
    job_count: int
    unique_user: int


class CandidateTable(BaseModel):
    """削除候補となるテーブルのモデル"""

    table_id: TableId
    table_type: TableType
    data_owner: str
