# Implementation Plan

## TDD Workflow
各タスクは以下のサイクルで進める：
1. **RED**: 失敗するテストを書く
2. **GREEN**: テストを通す最小限の実装を書く
3. **REFACTORING**: コードを整理し、重複を排除する

## Tasks

### Task 1: ドメインモデルの定義（外部依存なし・テスト容易性: 高）

- [x] 1.1 DataSource列挙型を定義する
  - **RED**: DataSource.INFORMATION_SCHEMAとDataSource.AUDIT_LOGが存在することを検証するテストを書く
  - **GREEN**: StrEnumを継承したDataSource列挙型を作成する
  - **REFACTORING**: 必要に応じてdocstringを追加
  - _Requirements: 1.3, 2.3_

- [x] 1.2 TableAccessCountモデルを定義する
  - **RED**: project_id, dataset_id, table_id, count, sourceを持つモデルの生成テストを書く
  - **RED**: full_pathプロパティが「project.dataset.table」形式を返すテストを書く
  - **RED**: イミュータブル（frozen=True）であることを検証するテストを書く
  - **GREEN**: Pydantic BaseModelを継承したTableAccessCountを実装する
  - **GREEN**: full_pathをcomputed_fieldとして実装する
  - **REFACTORING**: フィールドのバリデーションルールを整理
  - _Requirements: 1.3, 2.3, 3.1, 4.5_

- [x] 1.3 FilterConfigモデルを定義する
  - **RED**: デフォルト値（days=30）が設定されることを検証するテストを書く
  - **RED**: start_date/end_dateの明示指定が機能することを検証するテストを書く
  - **RED**: dataset_filter, table_pattern, min_countのフィルタ設定テストを書く
  - **RED**: 期間が180日を超える場合に警告を生成するテストを書く
  - **GREEN**: FilterConfigモデルを実装し、model_validatorで期間検証を行う
  - **REFACTORING**: バリデーションロジックをプライベートメソッドに抽出
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 1.4 TableAccessResultモデルを定義する
  - **RED**: project_id, start_date, end_dateを保持することを検証するテストを書く
  - **RED**: info_schema_results, audit_log_results, merged_resultsを個別に保持するテストを書く
  - **RED**: warningsリストを保持し、追加できることを検証するテストを書く
  - **GREEN**: TableAccessResultモデルを実装する
  - **REFACTORING**: 結果アクセス用のヘルパープロパティを追加
  - _Requirements: 3.1, 3.2, 4.1_

- [x] 1.5 例外クラスを定義する
  - **RED**: AuditLogNotEnabledErrorが有効化手順メッセージを含むことを検証するテストを書く
  - **RED**: QueryTimeoutErrorがタイムアウト調整方法を含むことを検証するテストを書く
  - **RED**: PermissionDeniedErrorが必要な権限情報を含むことを検証するテストを書く
  - **GREEN**: 各例外クラスをDatasetLoaderErrorを継承して実装する
  - **REFACTORING**: エラーメッセージのテンプレートを定数化
  - _Requirements: 2.6, 6.3_

### Task 2: 出力フォーマッターの実装（I/Oのみ・テスト容易性: 高）

- [x] 2.1 ConsoleFormatterを実装する
  - **RED**: TableAccessResultを受け取り、表形式の文字列を返すテストを書く
  - **RED**: 参照回数の降順でソートされていることを検証するテストを書く
  - **RED**: project_id, dataset, table, count, sourceの各カラムが含まれることを検証するテストを書く
  - **RED**: warningsがある場合、先頭に表示されることを検証するテストを書く
  - **GREEN**: ConsoleFormatterクラスを実装し、format()メソッドで文字列を返す
  - **REFACTORING**: 表のフォーマット処理をヘルパーメソッドに抽出
  - _Requirements: 4.1, 4.2, 4.5_

- [x] 2.2 CsvFormatterを実装する
  - **RED**: TableAccessResultをCSV形式の文字列に変換するテストを書く
  - **RED**: ヘッダー行が正しいカラム名を含むことを検証するテストを書く
  - **RED**: ファイルパスを指定して書き出せることを検証するテストを書く
  - **RED**: 出力パスが存在しない場合のエラーハンドリングテストを書く
  - **GREEN**: CsvFormatterクラスを実装し、format()とwrite_to_file()メソッドを実装する
  - **REFACTORING**: csvモジュールを使用した実装に統一
  - _Requirements: 4.3, 4.5_

- [x] 2.3 JsonFormatterを実装する
  - **RED**: TableAccessResultをJSON形式の文字列に変換するテストを書く
  - **RED**: 集計期間、project_id、warnings、table_accessesを含むことを検証するテストを書く
  - **RED**: ファイルパスを指定して書き出せることを検証するテストを書く
  - **GREEN**: JsonFormatterクラスを実装し、format()とwrite_to_file()メソッドを実装する
  - **REFACTORING**: Pydanticのmodel_dump()を活用してシリアライズを簡潔化
  - _Requirements: 4.4, 4.5_

- [x] 2.4 OutputFormatterProtocolを定義する
  - **RED**: format(result: TableAccessResult) -> strのシグネチャを持つことを検証
  - **GREEN**: Protocolクラスを定義する
  - **REFACTORING**: 各フォーマッターがProtocolを満たすことを型チェックで確認
  - _Requirements: 4.1_

### Task 3: データソースProtocolの定義（インターフェース定義・テスト容易性: 高）

- [x] 3.1 TableAccessDataSourceProtocolを定義する
  - **RED**: fetch_table_access()メソッドのシグネチャテストを書く（Protocol準拠確認）
  - **RED**: 引数（project_id, filter_config, progress_callback）の型を検証するテストを書く
  - **RED**: 戻り値がlist[TableAccessCount]であることを検証するテストを書く
  - **GREEN**: typing.Protocolを使用してTableAccessDataSourceを定義する
  - **GREEN**: メソッドのdocstringに例外仕様を記載する
  - **REFACTORING**: 共通の型エイリアス（ProgressCallback）を定義
  - _Requirements: 1.1, 1.2, 2.1, 2.2_

### Task 4: 集計ユースケースの実装（アダプターをモック可能・テスト容易性: 中〜高）

- [x] 4.1 結果マージロジックを実装する
  - **RED**: 2つのTableAccessCountリストをマージするテストを書く
  - **RED**: 同一テーブル（project, dataset, table一致）を識別するテストを書く
  - **RED**: 重複テーブルは最大値を採用することを検証するテストを書く
  - **RED**: 結果が参照回数の降順でソートされることを検証するテストを書く
  - **GREEN**: merge_results()関数を実装する
  - **REFACTORING**: 集計ロジックをitertools/collectionsを活用して簡潔化
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 4.2 TableAccessCounterユースケースを実装する
  - **RED**: DataSourceOption.INFO_SCHEMA指定時、info_schemaアダプターのみ呼ばれるテストを書く
  - **RED**: DataSourceOption.AUDIT_LOG指定時、audit_logアダプターのみ呼ばれるテストを書く
  - **RED**: DataSourceOption.BOTH指定時、両アダプターが呼ばれるテストを書く
  - **RED**: 片方のデータソースでエラーが発生しても、もう一方の結果を返すテストを書く（部分成功）
  - **GREEN**: TableAccessCounterクラスを実装し、アダプターをDIで受け取る
  - **REFACTORING**: 並行取得のためのasyncio対応を検討
  - _Requirements: 3.4, 3.5, 6.5_

- [x] 4.3 フィルタリング適用ロジックを実装する
  - **RED**: min_count指定時、閾値未満の結果を除外するテストを書く
  - **RED**: FilterConfigがアダプターに正しく渡されることを検証するテストを書く
  - **RED**: 期間が180日を超える場合、warningsに警告が追加されるテストを書く
  - **GREEN**: apply_filters()メソッドを実装する
  - **REFACTORING**: フィルタ条件をチェイン可能な形式にリファクタ
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

### Task 5: INFORMATION_SCHEMAアダプターの実装（BigQueryモック必要・テスト容易性: 中）

- [x] 5.1 SQLクエリ生成ロジックを実装する
  - **RED**: 基本クエリがJOBS_BY_PROJECTとUNNEST(referenced_tables)を含むテストを書く
  - **RED**: 期間フィルタ（creation_time）がWHERE句に反映されるテストを書く
  - **RED**: データセットフィルタがWHERE句に反映されるテストを書く
  - **RED**: テーブルパターン（正規表現）がREGEXP_CONTAINS句に反映されるテストを書く
  - **GREEN**: build_query()メソッドを実装する
  - **REFACTORING**: SQLテンプレートを定数として分離
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 5.2 クエリ結果のパースロジックを実装する
  - **RED**: BigQueryの行データをTableAccessCountに変換するテストを書く（モックデータ使用）
  - **RED**: 集計（GROUP BY）が正しく行われることを検証するテストを書く
  - **RED**: 進捗コールバックが呼び出されることを検証するテストを書く
  - **GREEN**: parse_results()メソッドを実装する
  - **REFACTORING**: 行変換ロジックをプライベートメソッドに抽出
  - _Requirements: 1.2, 1.3_

- [x] 5.3 InfoSchemaAdapterクラスを実装する
  - **RED**: fetch_table_access()がTableAccessDataSourceProtocolを満たすテストを書く
  - **RED**: BigQuery Clientを使用してクエリを実行することを検証するテスト（モック）を書く
  - **GREEN**: InfoSchemaAdapterクラスを実装し、BigQuery Clientを受け取る
  - **REFACTORING**: クライアント生成をファクトリメソッドに分離
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 5.4 INFORMATION_SCHEMAのエラーハンドリングを実装する
  - **RED**: 403エラー時にPermissionDeniedErrorを送出するテストを書く
  - **RED**: エラーメッセージにroles/bigquery.resourceViewerが含まれることを検証するテストを書く
  - **RED**: タイムアウト時にQueryTimeoutErrorを送出するテストを書く
  - **GREEN**: 例外ハンドリングロジックを実装する
  - **REFACTORING**: エラー変換ロジックをデコレータ化
  - _Requirements: 1.5, 6.1, 6.3_

### Task 6: Cloud Audit Logsアダプターの実装（Cloud Loggingモック必要・テスト容易性: 中）

- [x] 6.1 google-cloud-loggingライブラリを追加する
  - **RED**: importが成功することを検証するテストを書く
  - **GREEN**: pyproject.tomlにgoogle-cloud-logging>=3.11.0を追加する
  - **GREEN**: uv lockを実行して依存関係を更新する
  - **REFACTORING**: 不要な依存がないか確認
  - _Requirements: 2.1_

- [x] 6.2 ログフィルタ生成ロジックを実装する
  - **RED**: resource.type="bigquery_dataset"が含まれるテストを書く
  - **RED**: protoPayload.methodName="tableDataRead"が含まれるテストを書く
  - **RED**: timestamp範囲フィルタが正しく生成されるテストを書く
  - **GREEN**: build_filter()メソッドを実装する
  - **REFACTORING**: フィルタ文字列のエスケープ処理を共通化
  - _Requirements: 2.1, 2.2_

- [x] 6.3 ログエントリのパースロジックを実装する
  - **RED**: protoPayload.resourceNameからproject/dataset/tableを抽出するテストを書く
  - **RED**: パース失敗時にスキップして継続することを検証するテストを書く
  - **RED**: 集計（テーブル単位のカウント）が正しく行われるテストを書く
  - **GREEN**: parse_log_entry()メソッドを実装する
  - **REFACTORING**: 正規表現パターンを定数化
  - _Requirements: 2.2, 2.3_

- [x] 6.4 AuditLogAdapterクラスを実装する
  - **RED**: fetch_table_access()がTableAccessDataSourceProtocolを満たすテストを書く
  - **RED**: ページネーションが正しく処理されることを検証するテスト（モック）を書く
  - **RED**: 進捗コールバックが各ページ処理後に呼び出されることを検証するテストを書く
  - **GREEN**: AuditLogAdapterクラスを実装し、LoggingClientを受け取る
  - **REFACTORING**: ページネーション処理をジェネレータに変換
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 6.5 Audit Logのエラーハンドリングを実装する
  - **RED**: 403エラー時にPermissionDeniedErrorを送出するテストを書く
  - **RED**: ログが0件の場合にAuditLogNotEnabledErrorの可能性を警告するテストを書く
  - **RED**: レート制限時にバックオフリトライすることを検証するテストを書く
  - **GREEN**: 例外ハンドリングとリトライロジックを実装する
  - **REFACTORING**: リトライロジックをtenacityライブラリに置き換え検討
  - _Requirements: 2.5, 2.6, 6.1_

### Task 7: 共通エラーハンドリングと進捗表示（テスト容易性: 中）

- [x] 7.1 進捗表示機能を実装する
  - **RED**: ProgressCallbackが処理済み件数を受け取るテストを書く
  - **RED**: 複数データソース処理時に各ソースの進捗が報告されるテストを書く
  - **GREEN**: ProgressReporterクラスを実装する
  - **REFACTORING**: 既存のProgressCallbackパターンとの整合性を確認
  - _Requirements: 6.4_

- [x] 7.2 共通エラーハンドリングを実装する
  - **RED**: BigQuery API接続エラー時のメッセージテストを書く
  - **RED**: 認証エラー時にgcloud auth application-default loginを案内するテストを書く
  - **RED**: 予期しないエラー時にログファイルパスを案内するテストを書く
  - **GREEN**: handle_api_error()関数を実装する
  - **REFACTORING**: エラーメッセージをi18n対応可能な構造に
  - _Requirements: 6.1, 6.2, 6.5_

## Out of Scope

- 統合テスト（INFORMATION_SCHEMA統合テスト、Audit Log統合テスト、エンドツーエンドテスト）は本実装のスコープ外とする
