import os

from pathlib import Path

import pandas as pd

from google.cloud import bigquery


DATA_SOURCE_PATH = Path("source_data")
TABLES_PATH = DATA_SOURCE_PATH / "tables.csv"
COUNTS_PATH = DATA_SOURCE_PATH / "counts.csv"
LEAF_NODES_PATH = DATA_SOURCE_PATH / "leaf_nodes.csv"
ALL_TABLES_PATH = DATA_SOURCE_PATH / "all_tables.csv"


def main() -> None:
    os.makedirs("source_data", exist_ok=True)

    client = bigquery.Client()

    if not TABLES_PATH.exists():
        with open("sql/tables.sql", "r") as f:
            sql = f.read()
        query_job = client.query(sql)
        result = query_job.result()
        tables_df = result.to_dataframe()
        tables_df.to_csv(TABLES_PATH, index=False)
    else:
        tables_df = pd.read_csv(TABLES_PATH)

    if not COUNTS_PATH.exists():
        with open("sql/table_reference_count.sql", "r") as f:
            sql = f.read()
        query_job = client.query(sql)
        result = query_job.result()
        counts_df = result.to_dataframe()
        counts_df.to_csv(COUNTS_PATH, index=False)
    else:
        counts_df = pd.read_csv(COUNTS_PATH)

    if not LEAF_NODES_PATH.exists():
        leaf_node_df = pd.read_csv(
            "../../typescript/bigquery-table-observation/output/lineage.csv"
        )
        leaf_node_df.to_csv(LEAF_NODES_PATH, index=False)
    else:
        leaf_node_df = pd.read_csv(LEAF_NODES_PATH)

    all_tables_df = tables_df.merge(
        counts_df,
        on=["project_id", "dataset_id", "table_id"],
        how="left",
    )
    all_tables_df.fillna(0, inplace=True)

    all_tables_df.merge(
        leaf_node_df,
        on=["project_id", "dataset_id", "table_id"],
        how="inner",
    ).to_csv(ALL_TABLES_PATH, index=False)


if __name__ == "__main__":
    main()
