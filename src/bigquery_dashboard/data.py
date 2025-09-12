import pandas as pd
import pandas_gbq as pgbq
import pandera as pa

from pandera.typing.pandas import DataFrame

from bigquery_dashboard.model import UserWatchTime


@pa.check_types()
def get_table_from_bq(sql: str, project_id: str) -> DataFrame[UserWatchTime]:
    df = pgbq.read_gbq(sql, project_id=project_id)
    return UserWatchTime.validate(df)
