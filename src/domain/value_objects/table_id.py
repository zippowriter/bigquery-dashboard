from pydantic import BaseModel


class TableId(BaseModel):
    project_id: str
    dataset_id: str
    table_id: str
