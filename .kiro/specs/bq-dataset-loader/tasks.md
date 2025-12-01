# Implementation Plan

## Task Format Template

Use whichever pattern fits the work breakdown:

### Major task only
- [ ] {{NUMBER}}. {{TASK_DESCRIPTION}}{{PARALLEL_MARK}}
  - {{DETAIL_ITEM_1}} *(Include details only when needed. If the task stands alone, omit bullet items.)*
  - _Requirements: {{REQUIREMENT_IDS}}_

### Major + Sub-task structure
- [ ] {{MAJOR_NUMBER}}. {{MAJOR_TASK_SUMMARY}}
- [ ] {{MAJOR_NUMBER}}.{{SUB_NUMBER}} {{SUB_TASK_DESCRIPTION}}{{SUB_PARALLEL_MARK}}
  - {{DETAIL_ITEM_1}}
  - {{DETAIL_ITEM_2}}
  - _Requirements: {{REQUIREMENT_IDS}}_ *(IDs only; do not add descriptions or parentheses.)*

> **Parallel marker**: Append ` (P)` only to tasks that can be executed in parallel. Omit the marker when running in `--sequential` mode.
>
> **Optional test coverage**: When a sub-task is deferrable test work tied to acceptance criteria, mark the checkbox as `- [ ]*` and explain the referenced requirements in the detail bullets.

---

- [ ] 1. プロジェクト構造とパッケージ基盤の構築
- [x] 1.1 (P) src レイアウトとパッケージディレクトリ構造を作成する
  - src/bq_table_reference/ をルートとしたパッケージ構造を作成する
  - domain、infrastructure、application の各レイヤーディレクトリと __init__.py を配置する
  - pyproject.toml にパッケージ設定と google-cloud-bigquery 依存を追加する
  - _Requirements: 5.1_

- [x] 1.2 (P) テストディレクトリ構造と pytest 設定を構築する
  - tests/unit/ と tests/integration/ のディレクトリ構造を作成する
  - conftest.py に共通フィクスチャの雛形を配置する
  - pytest の基本設定を pyproject.toml に追加する
  - _Requirements: 1.1, 2.1_

- [ ] 2. ドメインモデルの実装
- [ ] 2.1 (P) データセット情報を表現するイミュータブルなデータ構造を実装する
  - RED: データセットID、プロジェクト、フルパス、作成日時、更新日時、ロケーションの保持を検証するテストを書く
  - GREEN: frozen dataclass として DatasetInfo を実装し、全テストをパスさせる
  - REFACTOR: 各フィールドの型とオプショナル設定を整理する
  - _Requirements: 1.2, 3.1_

- [ ] 2.2 (P) テーブル情報を表現するイミュータブルなデータ構造を実装する
  - RED: テーブルID、データセットID、プロジェクト、フルパス、テーブル種別の保持を検証するテストを書く
  - GREEN: frozen dataclass として TableInfo を実装し、全テストをパスさせる
  - REFACTOR: テーブル種別の Literal 型定義を追加し、型安全性を確保する
  - _Requirements: 2.2, 3.2_

- [ ] 2.3 (P) 一括ロード結果を表現するデータ構造を実装する
  - RED: 成功件数、失敗件数、テーブル総数、エラー辞書の保持を検証するテストを書く
  - GREEN: LoadResult dataclass を実装し、全テストをパスさせる
  - REFACTOR: デフォルト値とファクトリ関数を整理する
  - _Requirements: 4.4_

- [ ] 2.4 (P) カスタム例外クラス階層を実装する
  - RED: 各例外クラスのインスタンス化、継承関係、メッセージ取得を検証するテストを書く
  - GREEN: DatasetLoaderError をベースに AuthenticationError、PermissionDeniedError、DatasetNotFoundError、NetworkError を実装する
  - REFACTOR: 各例外に解決方法のガイダンスメッセージを追加する
  - _Requirements: 1.3, 1.4, 2.3, 5.3_

- [ ] 3. BigQuery クライアントアダプターの実装
- [ ] 3.1 アダプターの初期化と認証処理を実装する
  - RED: アダプターの初期化、ADC 認証情報の取得、認証失敗時の例外変換を検証するモックテストを書く
  - GREEN: BQClientAdapter のコンストラクタと認証処理を実装し、全テストをパスさせる
  - REFACTOR: コンテキストマネージャー対応とリソースクリーンアップ処理を追加する
  - 依存: タスク 2.4（例外クラス）の完了が必要
  - _Requirements: 5.1, 5.2, 5.3_

- [ ] 3.2 データセット一覧取得機能を実装する
  - RED: データセット一覧取得、SDK オブジェクトから DatasetInfo への変換を検証するモックテストを書く
  - GREEN: list_datasets メソッドを実装し、イテレータとして全データセットを返却する
  - REFACTOR: 権限エラー、ネットワークエラーの例外変換処理を追加する
  - 依存: タスク 3.1（アダプター初期化）の完了が必要
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 3.3 テーブル一覧取得機能を実装する
  - RED: テーブル一覧取得、SDK オブジェクトから TableInfo への変換、ページネーション処理を検証するモックテストを書く
  - GREEN: list_tables メソッドを実装し、イテレータとして全テーブルを返却する
  - REFACTOR: NotFound エラー処理、ページネーション対応を確認し、例外変換を追加する
  - 依存: タスク 3.1（アダプター初期化）の完了が必要
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 4. データセットローダーの実装
- [ ] 4.1 ローダーの初期化とオンメモリデータ保持構造を実装する
  - RED: アダプターの受け取り、内部辞書構造の初期化を検証するテストを書く
  - GREEN: DatasetLoader のコンストラクタと内部データ構造（_datasets、_tables、_tables_by_dataset）を実装する
  - REFACTOR: アダプターが未指定の場合の新規作成ロジックを追加する
  - 依存: タスク 3.1（アダプター）の完了が必要
  - _Requirements: 3.1, 3.2_

- [ ] 4.2 一括ロード機能を実装する
  - RED: 全データセット・全テーブルの取得、辞書への登録、エラー継続処理を検証するモックテストを書く
  - GREEN: load_all メソッドを実装し、データセットループでテーブルを取得、エラー時も他の処理を継続する
  - REFACTOR: 進捗コールバック対応、LoadResult の生成ロジックを整理する
  - 依存: タスク 4.1（ローダー初期化）の完了が必要
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 4.3 O(1) 検索機能を実装する
  - RED: データセットID検索、テーブルフルパス検索、データセット別テーブル一覧取得を検証するテストを書く
  - GREEN: get_dataset、get_table、get_tables_by_dataset メソッドと datasets、tables プロパティを実装する
  - REFACTOR: 存在しないキーへの None 返却、計算量 O(1) の動作を確認する
  - 依存: タスク 4.2（一括ロード）の完了が必要
  - _Requirements: 3.3, 3.4_

- [ ] 5. パッケージ公開 API の整備
- [ ] 5.1 パッケージ初期化とエクスポート設定を実装する
  - bq_table_reference/__init__.py で公開 API（DatasetLoader、DatasetInfo、TableInfo、LoadResult、例外クラス群）をエクスポートする
  - __all__ と __version__ を定義し、外部からのインポートを簡潔にする
  - 使用例のドキュメント文字列を追加する
  - 依存: タスク 4.3（検索機能）の完了が必要
  - _Requirements: 3.1, 3.2, 4.1_

- [ ] 6. エントリーポイントとの統合を実装する
  - RED: ローダーのインスタンス化、一括ロード実行、結果表示の一連の流れを検証する統合テストを書く
  - GREEN: main.py からパッケージをインポートし、サンプル実行コードを作成する
  - REFACTOR: 進捗コールバックによる実行状況表示とサマリー出力を整理する
  - 依存: タスク 5.1（パッケージ API）の完了が必要
  - _Requirements: 4.1, 4.2, 4.4_

- [ ]* 7. 実環境での統合テストを実装する
  - 実際の BigQuery API を使用した統合テスト（テスト用プロジェクト）を作成する
  - ADC 認証が正常に動作することを確認する
  - データセット・テーブルの取得からオンメモリ保持、検索までの一連の流れを検証する
  - 本タスクは実環境でのエンドツーエンド検証のため、MVP 後に実施可能
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 3.3, 3.4, 4.1, 5.1_
