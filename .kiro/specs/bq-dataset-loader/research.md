# Research & Design Decisions

## Summary

- **Feature**: `bq-dataset-loader`
- **Discovery Scope**: New Feature (グリーンフィールド)
- **Key Findings**:
  - google-cloud-bigquery ライブラリは `list_datasets()` と `list_tables()` メソッドを提供し、ページネーションを自動処理する
  - Application Default Credentials (ADC) が推奨される認証方式であり、明示的な認証情報ファイルは非推奨
  - Dataset/Table クラスは豊富なメタデータプロパティを持ち、dataclass でラップすることで型安全性を確保できる

## Research Log

### BigQuery Python Client API

- **Context**: データセット・テーブル一覧取得に必要なAPIメソッドの調査
- **Sources Consulted**:
  - [Google Cloud BigQuery Python Client Documentation](https://docs.cloud.google.com/python/docs/reference/bigquery/latest)
  - [Listing Datasets Guide](https://cloud.google.com/bigquery/docs/listing-datasets)
  - [Stack Overflow: Get list of tables](https://stackoverflow.com/questions/56656880/get-list-of-tables-in-bigquery-dataset-using-python-and-bigquery-api)
- **Findings**:
  - `client.list_datasets()` はプロジェクト内の全データセットをイテレータとして返却
  - `client.list_tables(dataset_id)` は指定データセット内の全テーブルをイテレータとして返却
  - 両メソッドともページネーションを内部で自動処理
  - `get_dataset()` / `get_table()` で詳細メタデータを取得可能
- **Implications**: ページネーション処理は SDK が担当するため、ローダー側での実装は不要

### Dataset/Table クラスのプロパティ

- **Context**: オンメモリデータ構造に保持すべき属性の特定
- **Sources Consulted**:
  - [Dataset Class Reference](https://docs.cloud.google.com/python/docs/reference/bigquery/latest/google.cloud.bigquery.dataset.Dataset)
  - [Table Class Reference](https://docs.cloud.google.com/python/docs/reference/bigquery/latest/google.cloud.bigquery.table.Table)
- **Findings**:
  - **Dataset**: `dataset_id`, `project`, `full_dataset_id` (project_id:dataset_id形式), `created`, `modified`, `location`
  - **Table**: `table_id`, `project`, `dataset_id`, `full_table_id` (project-id:dataset_id.table_id形式), `table_type` (TABLE/VIEW/MATERIALIZED_VIEW/EXTERNAL), `created`, `modified`
  - list_tables が返す `TableListItem` はメタデータが限定的（table_type は含まれるが created/modified は含まれない）
- **Implications**: 基本一覧取得には `list_tables` で十分だが、詳細情報が必要な場合は `get_table` の追加呼び出しが必要

### 認証方式

- **Context**: BigQuery への認証方法のベストプラクティス調査
- **Sources Consulted**:
  - [BigQuery Authentication Guide](https://cloud.google.com/bigquery/docs/authentication/)
  - [ADC Client Sample](https://cloud.google.com/bigquery/docs/samples/bigquery-client-default-credentials)
- **Findings**:
  - Application Default Credentials (ADC) が推奨
  - ローカル開発: `gcloud auth application-default login` でセットアップ
  - サービスアカウント: `GOOGLE_APPLICATION_CREDENTIALS` 環境変数でキーファイルパスを指定
  - 明示的なキーファイル管理は非推奨（セキュリティリスク）
  - `bigquery.Client()` はデフォルトで ADC を使用
- **Implications**: クライアント生成時に明示的な認証情報を渡す必要はなく、環境からの自動取得に依存可能

### Python 型ヒントとデータクラス

- **Context**: 型安全なデータ構造の設計パターン調査
- **Sources Consulted**:
  - [Python typing module](https://docs.python.org/3/library/typing.html)
  - [bq-schema library](https://github.com/limehome/bq-schema)
- **Findings**:
  - Python 3.7+ の dataclass は型ヒント付きのデータコンテナとして最適
  - dataclass は実行時の型検証を行わないため、境界で明示的な検証が必要
  - frozen=True オプションでイミュータブルなデータ構造を実現可能
  - Optional 型を適切に使用することで null 安全性を表現
- **Implications**: dataclass を使用し、BigQuery SDK のオブジェクトから変換する際に型を明示的に付与

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| Repository Pattern | データアクセス層を抽象化し、ドメインオブジェクトを返却 | テスト容易性、関心の分離 | 小規模プロジェクトではオーバーヘッド | 将来の拡張性を考慮して採用 |
| Direct Client Usage | BigQuery Client を直接使用 | シンプル、学習コスト低 | テスト困難、依存性の密結合 | 初期段階としては十分だが拡張性に欠ける |
| Adapter Pattern | BigQuery SDK をラップし、独自インターフェースを提供 | SDK 変更への耐性、型安全性 | 実装コスト | Repository と組み合わせて採用 |

**選択**: Repository Pattern + Adapter の組み合わせ
- BigQuery Client を直接使用せず、型安全なドメインオブジェクトに変換
- テスト時はモックリポジトリに差し替え可能

## Design Decisions

### Decision: データ構造の設計

- **Context**: 要件3で定義された「O(1)検索」を実現するデータ構造の選択
- **Alternatives Considered**:
  1. リスト構造 — シンプルだが検索は O(n)
  2. 辞書構造（dict） — キーによる O(1) 検索が可能
  3. dataclass + 辞書の組み合わせ — 型安全性と検索効率を両立
- **Selected Approach**: dataclass による型定義 + dict によるインデックス管理
- **Rationale**: 型ヒントによる IDE サポートと開発効率、辞書による高速検索を両立
- **Trade-offs**: メモリ使用量が若干増加するが、通常のプロジェクト規模では問題にならない
- **Follow-up**: 大規模プロジェクト（1000+ テーブル）でのメモリ使用量を実装時に検証

### Decision: エラーハンドリング戦略

- **Context**: BigQuery API のエラー（認証、権限、Not Found）を適切に処理する方法
- **Alternatives Considered**:
  1. 例外をそのまま伝播 — シンプルだがユーザーフレンドリーでない
  2. カスタム例外にラップ — エラー種別を明確化
  3. Result 型パターン — 関数型アプローチ
- **Selected Approach**: カスタム例外クラス階層を定義
- **Rationale**: Python のイディオムに沿った例外ベースのエラー処理、エラーメッセージの日本語化対応が容易
- **Trade-offs**: 例外処理コードが増加するが、エラー原因の特定が容易になる
- **Follow-up**: google-api-core の例外クラス（`google.api_core.exceptions`）との対応関係を実装時に確認

### Decision: 一括ロード時の部分失敗処理

- **Context**: 要件4.3で定義された「エラー発生時も他のデータセットの処理を継続」の実現方法
- **Alternatives Considered**:
  1. 全て成功するまでリトライ — 1つの失敗で全体がブロック
  2. 失敗を記録して継続 — 部分的な結果を返却
  3. 非同期並列処理 + エラー集約 — 高速だが複雑
- **Selected Approach**: 失敗を記録して継続、サマリーを返却
- **Rationale**: 要件に明示されている動作であり、ユーザーが失敗箇所を把握可能
- **Trade-offs**: 部分的なデータで後続処理を行うリスクがあるため、成功率の可視化が重要
- **Follow-up**: 進捗コールバックの設計を実装時に詳細化

## Risks & Mitigations

- **API Rate Limit**: BigQuery API には呼び出し制限がある — list_tables を大量のデータセットに対して呼び出す場合は注意。軽減策: 必要に応じてバッチ処理とスリープを導入
- **認証情報の不在**: ADC 未設定環境でのエラー — 軽減策: 明確なエラーメッセージと設定ガイダンスを提供
- **大規模プロジェクト**: 数千テーブルのロードに時間がかかる可能性 — 軽減策: 進捗表示と部分ロード機能の提供

## References

- [Google Cloud BigQuery Python Client](https://cloud.google.com/python/docs/reference/bigquery/latest) — 公式リファレンス
- [BigQuery Authentication Guide](https://cloud.google.com/bigquery/docs/authentication/) — 認証方式の詳細
- [Listing Datasets](https://cloud.google.com/bigquery/docs/listing-datasets) — データセット一覧取得のサンプルコード
- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html) — データクラスの公式ドキュメント
