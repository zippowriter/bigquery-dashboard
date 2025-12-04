from pathlib import Path

from application.usecases.export_leaf_tables_usecase import (
    ExportLeafTablesRequest,
    ExportLeafTablesUseCase,
)
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

# UseCase実行
usecase = ExportLeafTablesUseCase(table_repo, lineage_repo, file_writer)
result = usecase.execute(
    ExportLeafTablesRequest(
        project_ids=["abematv-data", "abematv-analysis", "abematv-data-tech"],
        output_path=Path("output/leaf_tables.csv"),
        output_format="csv",
    )
)

print(f"Total tables: {result.total_tables_count}")
print(f"Leaf tables: {result.leaf_tables_count}")
print(f"Output: {result.output_path}")
