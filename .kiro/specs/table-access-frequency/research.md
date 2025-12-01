# Research & Design Decisions

## Summary
- **Feature**: `table-access-frequency`
- **Discovery Scope**: Extension (既存レイヤードアーキテクチャへの新機能追加)
- **Key Findings**:
  - INFORMATION_SCHEMA.JOBS_BY_PROJECT の `referenced_tables` は ARRAY<STRUCT<project_id, dataset_id, table_id>> 型
  - Cloud Audit Logs の tableDataRead イベントは `resource.type=bigquery_dataset` でフィルタ可能
  - 両データソースは異なる粒度・目的を持ち、相互補完的に利用可能

## Research Log

### INFORMATION_SCHEMA.JOBS_BY_PROJECT の構造調査
- **Context**: 要件1でINFORMATION_SCHEMAからテーブル参照回数を取得する必要がある
- **Sources Consulted**:
  - [Google Cloud BigQuery JOBS view documentation](https://cloud.google.com/bigquery/docs/information-schema-jobs)
  - [BigQuery INFORMATION_SCHEMA Guide (Medium)](https://medium.com/google-cloud/bigquery-information-schema-a6a852535cf1)
  - [Stack Overflow: Query jobs across organisation](https://stackoverflow.com/questions/74458245/get-all-bigquery-query-jobs-across-organisation-that-reference-a-specific-table)
- **Findings**:
  - `referenced_tables` カラムは `ARRAY<STRUCT<project_id STRING, dataset_id STRING, table_id STRING>>` 型
  - `UNNEST(referenced_tables)` で展開してテーブル単位の集計が可能
  - 必要権限: `bigquery.jobs.listAll` (roles/bigquery.resourceViewer に含まれる)
  - リージョン指定が必須: `region-{REGION}.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
  - デフォルト保持期間: 180日
- **Implications**:
  - BQClientAdapter に SQL クエリ実行機能を追加する必要がある
  - リージョン設定をパラメータ化する設計が必要

### Cloud Audit Logs の tableDataRead 調査
- **Context**: 要件2でauditlogからテーブル参照回数を取得する必要がある
- **Sources Consulted**:
  - [BigQuery audit logs overview](https://cloud.google.com/bigquery/docs/reference/auditlogs)
  - [Introduction to audit logs in BigQuery](https://cloud.google.com/bigquery/docs/introduction-audit-workloads)
  - [google-cloud-logging PyPI](https://pypi.org/project/google-cloud-logging/)
- **Findings**:
  - tableDataRead イベントは `resource.type=bigquery_dataset` で識別
  - `protoPayload.metadata.tableDataRead` にイベント詳細が格納
  - `protoPayload.resourceName` から `projects/{project}/datasets/{dataset}/tables/{table}` 形式でテーブル特定
  - Data Access ログは明示的に有効化が必要 (IAM > Audit Logs)
  - google-cloud-logging ライブラリ (v3.11+) で `list_entries()` を使用
  - フィルタ構文: `resource.type="bigquery_dataset" AND protoPayload.metadata.tableDataRead:*`
- **Implications**:
  - 新規依存ライブラリ `google-cloud-logging` の追加が必要
  - auditlog 有効化状態の検出とユーザー通知機能が必要
  - Cloud Logging API のクォータ・レート制限を考慮

### データソース間の重複処理調査
- **Context**: 要件3で両データソースの統合時に重複を考慮する必要がある
- **Sources Consulted**: 調査結果の比較分析
- **Findings**:
  - INFORMATION_SCHEMA: ジョブ単位での参照記録 (1ジョブで複数テーブル参照 = 各1カウント)
  - Audit Logs: テーブル読み取りイベント単位 (1クエリで複数回読み取り可能)
  - 両者は同一アクセスを異なる観点で記録するため、単純合算は不適切
  - 推奨アプローチ: 各ソース別の集計結果を個別表示 + オプションで統合ビュー
- **Implications**:
  - 統合モードでは「最大値」または「ソース選択」の戦略が必要
  - UI/出力で各ソースの値を明示する設計

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| 既存レイヤード拡張 | Domain/Application/Infrastructure の既存レイヤーに新モジュール追加 | 一貫性維持、学習コスト低 | 横断的関心事の処理が複雑になる可能性 | **選択** |
| サービス分離 | テーブル参照回数機能を独立サービス化 | 独立デプロイ可能 | オーバーエンジニアリング、運用複雑化 | 却下 |
| プラグイン方式 | データソースをプラグイン化 | 拡張性高い | 現時点では2ソースのみで過剰設計 | 将来検討 |

## Design Decisions

### Decision: データソースアダプターの設計
- **Context**: INFORMATION_SCHEMA と Audit Logs という異なるAPIを統一的に扱う必要がある
- **Alternatives Considered**:
  1. 単一の BQClientAdapter に全機能を追加
  2. データソースごとに専用アダプターを作成 (Protocol ベース)
- **Selected Approach**: データソースごとに専用アダプター + 共通 Protocol を定義
- **Rationale**:
  - 各データソースのAPI特性が異なる (BigQuery SQL vs Cloud Logging API)
  - テスト時のモック化が容易
  - 将来の新データソース追加に対応可能
- **Trade-offs**: クラス数増加、初期実装コスト増
- **Follow-up**: Protocol 定義の型安全性を静的解析で検証

### Decision: 期間指定パラメータの設計
- **Context**: 要件5で期間指定が必要、両データソースで保持期間制限がある
- **Alternatives Considered**:
  1. 開始日・終了日の両方を指定
  2. 過去N日のみ指定
  3. 開始日のみ指定 (終了は現在日時)
- **Selected Approach**: 過去N日指定 (デフォルト30日) + オプションで開始・終了日指定
- **Rationale**:
  - 最も一般的なユースケースをシンプルに
  - INFORMATION_SCHEMA の保持期間 (180日) を超える場合は警告
- **Trade-offs**: 柔軟性とシンプルさのバランス
- **Follow-up**: CLI オプション設計で使いやすさを検証

### Decision: 出力形式の設計
- **Context**: 要件4で複数の出力形式 (標準出力/CSV/JSON) をサポート
- **Alternatives Considered**:
  1. 各形式専用のフォーマッター関数
  2. Strategy パターンで OutputFormatter Protocol を定義
- **Selected Approach**: OutputFormatter Protocol + 具象クラス (Console/CSV/JSON)
- **Rationale**:
  - 新形式追加が容易
  - テスト可能性が高い
  - 既存のレイヤードアーキテクチャと整合
- **Trade-offs**: 若干のコード量増加
- **Follow-up**: なし

### Decision: 進捗表示の実装
- **Context**: 要件6.4で大量データ処理時の進捗表示が必要
- **Alternatives Considered**:
  1. 既存の ProgressCallback パターンを再利用
  2. 新規の ProgressReporter 抽象化
- **Selected Approach**: 既存 ProgressCallback Protocol を拡張利用
- **Rationale**:
  - 既存コードとの一貫性
  - DatasetLoader で実証済みのパターン
- **Trade-offs**: なし
- **Follow-up**: なし

## Risks & Mitigations

- **Cloud Logging API レート制限** - ページネーション実装とバックオフリトライで対応
- **大規模プロジェクトでのパフォーマンス** - バッチ処理と進捗表示で UX を担保
- **Audit Logs 未有効化** - 明確なエラーメッセージと有効化手順の案内
- **INFORMATION_SCHEMA リージョン指定漏れ** - デフォルトリージョン設定と検証

## References

- [JOBS view | BigQuery | Google Cloud](https://cloud.google.com/bigquery/docs/information-schema-jobs) - INFORMATION_SCHEMA.JOBS の公式ドキュメント
- [BigQuery audit logs overview](https://cloud.google.com/bigquery/docs/reference/auditlogs) - Audit Logs の構造と使用方法
- [google-cloud-logging PyPI](https://pypi.org/project/google-cloud-logging/) - Python クライアントライブラリ (v3.11+)
- [Introduction to audit logs in BigQuery](https://cloud.google.com/bigquery/docs/introduction-audit-workloads) - tableDataRead イベントの詳細
