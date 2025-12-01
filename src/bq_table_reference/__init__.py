"""BigQuery テーブル参照分析ツール。

データセットとテーブルのメタデータを取得・管理するためのパッケージ。

Examples:
    >>> from bq_table_reference import DatasetLoader
    >>> loader = DatasetLoader(project="my-project")
    >>> result = loader.load_all("my-project")
    >>> print(f"Loaded {result.datasets_success} datasets")
"""

__version__ = "0.1.0"
