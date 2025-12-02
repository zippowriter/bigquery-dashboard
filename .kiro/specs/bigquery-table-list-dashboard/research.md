# Research & Design Decisions

---
**Purpose**: 本機能の技術設計に影響を与える調査結果と設計判断の根拠を記録する。

**Usage**:
- ディスカバリーフェーズでの調査活動とその結果を記録
- `design.md`に収まりきらない詳細なトレードオフを文書化
- 将来の監査や再利用のための参照情報を提供
---

## Summary
- **Feature**: `bigquery-table-list-dashboard`
- **Discovery Scope**: Extension（既存システムへの機能追加）
- **Key Findings**:
  - google-cloud-bigquery の `list_datasets()` と `list_tables()` APIで全テーブル一覧を取得可能
  - Plotly の `go.Table` で pandas.DataFrame を直接テーブル表示可能
  - Dash の `dcc.Graph` コンポーネントで Plotly Figure を埋め込み可能

## Research Log

### BigQuery テーブル一覧取得API

- **Context**: 対象プロジェクトの全テーブル情報を取得する方法の調査
- **Sources Consulted**:
  - [Google Cloud BigQuery - List Tables](https://docs.cloud.google.com/bigquery/docs/samples/bigquery-list-tables)
  - [Google Cloud BigQuery - List Datasets](https://cloud.google.com/bigquery/docs/samples/bigquery-list-datasets)
  - [Stack Overflow - Get list of tables in BigQuery](https://stackoverflow.com/questions/56656880/get-list-of-tables-in-bigquery-dataset-using-python-and-bigquery-api)
- **Findings**:
  - `bigquery.Client()` を使用してクライアントオブジェクトを生成
  - `client.list_datasets()` で `DatasetListItem` のイテレータを取得
  - `client.list_tables(dataset_id)` で `TableListItem` のイテレータを取得
  - 各テーブルオブジェクトは `project`, `dataset_id`, `table_id` プロパティを持つ
  - 認証は Application Default Credentials (ADC) を使用
- **Implications**:
  - データセットごとにループして全テーブルを取得する必要がある
  - API呼び出しは同期的に実行される
  - 認証エラー時は例外がスローされる

### Plotly テーブル表示

- **Context**: pandas.DataFrame を Plotly テーブルとして表示する方法の調査
- **Sources Consulted**:
  - [Plotly - Tables in Python](https://plotly.com/python/table/)
  - [Plotly graph_objects.Table API Reference](https://plotly.github.io/plotly.py-docs/generated/plotly.graph_objects.Table.html)
  - [Stack Overflow - Plotly Table from DataFrame](https://stackoverflow.com/questions/50188840/plotly-create-table-with-rowname-from-pandas-dataframe)
- **Findings**:
  - `go.Table` で表形式のデータを表示可能
  - `header=dict(values=list(df.columns))` でヘッダーを設定
  - `cells=dict(values=df.transpose().values.tolist())` で大量データに対応
  - スタイリング: `fill_color`, `align`, `font` などで外観をカスタマイズ可能
  - Dash では `dcc.Graph(figure=fig)` で Figure を埋め込む
- **Implications**:
  - pandas.DataFrame から Plotly Figure への変換は単純な処理で実現可能
  - 既存の `layout.py` 内で `dcc.Graph` コンポーネントを追加する形で実装

### 既存アーキテクチャとの整合性

- **Context**: 既存のレイヤードアーキテクチャへの統合方法の確認
- **Sources Consulted**:
  - 既存コード: `src/dashboard/config.py`, `layout.py`, `app.py`, `server.py`
  - `.kiro/steering/structure.md`
- **Findings**:
  - 4層構造: config, layout, app, server
  - Pydantic による設定管理パターン確立済み
  - `build_layout()` 関数でUIコンポーネントを構築
  - 関数ベースの実装（クラス設計は避ける）
- **Implications**:
  - BigQueryクライアント処理は新規モジュール `bigquery_client.py` に集約
  - 設定クラス `AppConfig` に `project_id` を追加
  - `layout.py` の `build_layout()` を拡張してテーブル表示を追加

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| 関数ベース拡張 | 既存の関数構造を維持し、新規モジュールを追加 | シンプル、既存パターン踏襲、保守性高い | 複雑な状態管理には不向き | 要件の「必要最低限のコード量」に合致 |
| クラスベース設計 | Service/Repository パターンを導入 | 拡張性、テスト容易性 | 要件に反する過剰設計 | 今回は採用しない |

## Design Decisions

### Decision: BigQueryクライアント処理の単一モジュール集約

- **Context**: BigQuery APIの呼び出しロジックの配置先
- **Alternatives Considered**:
  1. `layout.py` 内に直接実装 - 責務の分離が不十分
  2. 新規 `bigquery_client.py` モジュール作成 - 責務分離、テスト容易
  3. クラスベースの Repository パターン - 過剰設計
- **Selected Approach**: `src/dashboard/bigquery_client.py` として新規モジュールを作成
- **Rationale**:
  - 要件4.3「BigQueryクライアント処理を単一モジュールに集約」を満たす
  - 既存の `src/dashboard/` パッケージ構造に適合
  - 単体テストが容易
- **Trade-offs**:
  - メリット: 責務分離、保守性向上
  - デメリット: ファイル数が1つ増加
- **Follow-up**: なし

### Decision: Plotly go.Table の使用

- **Context**: テーブル表示コンポーネントの選択
- **Alternatives Considered**:
  1. `dash.html.Table` - 基本的なHTMLテーブル、スタイリング手動
  2. `dash_table.DataTable` - 高機能だがオーバースペック
  3. `plotly.graph_objects.Table` - Plotlyエコシステム統合、適度な機能
- **Selected Approach**: `plotly.graph_objects.Table` を使用
- **Rationale**:
  - 要件3.1「Plotlyのテーブルコンポーネントを使用」を満たす
  - pandas.DataFrame との親和性が高い
  - 既存の Dash アプリケーションに自然に統合
- **Trade-offs**:
  - メリット: Plotlyエコシステムとの一貫性、シンプルなAPI
  - デメリット: DataTable ほどのインタラクティブ機能なし（今回は不要）
- **Follow-up**: なし

### Decision: アプリケーション起動時のデータ取得

- **Context**: BigQueryからのデータ取得タイミング
- **Alternatives Considered**:
  1. 起動時に一度取得 - シンプル、レスポンス高速
  2. リクエスト毎に取得 - 最新データ、負荷増加
  3. 定期更新（Interval）- 中間的だが複雑化
- **Selected Approach**: アプリケーション起動時に一度取得
- **Rationale**:
  - 要件1.1「ダッシュボードアプリケーションが起動した時」に合致
  - シンプルな実装でコード量最小化
  - ユーザーがリロードすれば最新データを取得可能
- **Trade-offs**:
  - メリット: シンプル、高速
  - デメリット: 起動後のテーブル変更は反映されない（リロード必要）
- **Follow-up**: 将来的に自動更新が必要になった場合は `dcc.Interval` の追加を検討

## Risks & Mitigations

- **BigQuery API 認証エラー** - ADC が設定されていない場合にエラー発生。エラーメッセージを画面に表示して対処方法を案内する。
- **大量テーブルによるパフォーマンス低下** - 数百以上のテーブルがある場合に取得時間が長くなる可能性。起動時に一度だけ取得するため影響は限定的。
- **API クォータ超過** - 頻繁な起動で発生する可能性は低いが、本番環境では注意が必要。

## References

- [Google Cloud BigQuery - List Tables](https://docs.cloud.google.com/bigquery/docs/samples/bigquery-list-tables) - テーブル一覧取得の公式サンプル
- [Google Cloud BigQuery - List Datasets](https://cloud.google.com/bigquery/docs/samples/bigquery-list-datasets) - データセット一覧取得の公式サンプル
- [Plotly Tables in Python](https://plotly.com/python/table/) - Plotly テーブルの公式ドキュメント
- [plotly.graph_objects.Table API](https://plotly.github.io/plotly.py-docs/generated/plotly.graph_objects.Table.html) - go.Table の API リファレンス
