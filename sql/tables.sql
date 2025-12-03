WITH
abematv_data_tables AS (
  SELECT
    table_catalog AS project_id,
    table_schema AS dataset_id,
    table_name AS table_id,
    table_type
  FROM `abematv-data.region-us`.INFORMATION_SCHEMA.TABLES
  WHERE
    table_schema NOT IN (
      'auditlog_bigquery_v2',
      'abematv_bigquery_log',
      'patriot_abematv_bigquery_log'
    )
    AND table_schema NOT LIKE r'test_%'
),

abematv_analysis_tables AS (
  SELECT
    table_catalog AS project_id,
    table_schema AS dataset_id,
    table_name AS table_id,
    table_type
  FROM `abematv-analysis.region-us`.INFORMATION_SCHEMA.TABLES
  WHERE
    table_schema NOT IN (
      'abematv_bigquery_log',
      'patriot_117478195',
      'patriot_153256568'
    )
    AND table_schema NOT LIKE r'test_%'
),

abematv_data_tech_tables AS (
  SELECT
    table_catalog AS project_id,
    table_schema AS dataset_id,
    table_name AS table_id,
    table_type
  FROM `abematv-data-tech.region-us`.INFORMATION_SCHEMA.TABLES
  WHERE
    table_schema NOT LIKE r'test_%'
)

SELECT
  project_id,
  dataset_id,
  table_id,
  table_type
FROM
  abematv_data_tables
FULL OUTER JOIN abematv_analysis_tables USING (project_id, dataset_id, table_id, table_type)
FULL OUTER JOIN abematv_data_tech_tables USING (project_id, dataset_id, table_id, table_type)
