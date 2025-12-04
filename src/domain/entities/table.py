from typing import Literal

from pydantic import BaseModel

from domain.value_objects.table_id import TableId


class Table(BaseModel):
    """BigQueryのテーブルのモデル"""

    table_id: TableId
    table_type: Literal[
        "BASE TABLE",
        "VIEW",
        "EXTERNAL",
        "CLONE",
        "SNAPSHOT",
        "MATERIALIZED VIEW",
    ]


class CheckedTable(BaseModel):
    """参照回数が調べられたテーブルのモデル"""

    table_id: TableId
    table_type: Literal[
        "BASE TABLE",
        "VIEW",
        "EXTERNAL",
        "CLONE",
        "SNAPSHOT",
        "MATERIALIZED VIEW",
    ]
    job_count: int
    unique_user: int


class CandidateTable(BaseModel):
    """削除候補となるテーブルのモデル"""

    table_id: TableId
    table_type: Literal[
        "BASE TABLE",
        "VIEW",
        "EXTERNAL",
        "CLONE",
        "SNAPSHOT",
        "MATERIALIZED VIEW",
    ]
    data_owner: str
