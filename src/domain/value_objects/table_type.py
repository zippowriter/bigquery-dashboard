from typing import Literal

TableType = Literal[
    "BASE TABLE",
    "VIEW",
    "EXTERNAL",
    "CLONE",
    "SNAPSHOT",
    "MATERIALIZED VIEW",
]
