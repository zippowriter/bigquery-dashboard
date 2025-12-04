from pathlib import Path

from application.usecases.export_leaf_tables_usecase import (
    ExportLeafTablesRequest,
    ExportLeafTablesUseCase,
)
from domain.value_objects.table_id import TableId
from infra.bigquery.client import BigQueryClientFactory
from infra.bigquery.table_repository_impl import BigQueryTableRepository
from infra.file.file_writer_impl import PandasFileWriter
from infra.lineage.client import LineageClientFactory
from infra.lineage.lineage_repository_impl import DataCatalogLineageRepository


# DI
bq_client_factory = BigQueryClientFactory()
lineage_client_factory = LineageClientFactory(location="us")
table_repo = BigQueryTableRepository(bq_client_factory)
lineage_repo = DataCatalogLineageRepository(lineage_client_factory)
file_writer = PandasFileWriter()

usecase = ExportLeafTablesUseCase(table_repo, lineage_repo, file_writer)

# ルートテーブルを指定してリーフノードを取得
root_tables = [
    TableId(
        project_id="abematv-analysis",
        dataset_id="abematv_action_raw",
        table_id="abematv_mine_activity",
    ),
]

result = usecase.execute(
    ExportLeafTablesRequest(
        root_tables=root_tables,
        output_path=Path("output/leaf_tables_from_roots.csv"),
        output_format="csv",
    )
)

print(f"Root tables: {result.total_tables_count}")
print(f"Leaf tables: {result.leaf_tables_count}")
print(f"Output: {result.output_path}")
