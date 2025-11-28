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

- [ ] 1. ドメインモデルの実装
- [ ] 1.1 (P) データセット情報を表現するイミュータブルなデータ構造を実装する
  - RED: データセットID、プロジェクト、フルパス、作成日時、更新日時の保持を検証するテストを書く（失敗を確認）
  - GREEN: frozen dataclass として DatasetInfo を実装し、全テストをパスさせる
  - REFACTOR: ロケーション情報のオプショナルフィールドを追加し、インターフェースを整理する
  - _Requirements: 1.2, 3.1_

- [ ] 1.2 (P) テーブル情報を表現するイミュータブルなデータ構造を実装する
  - RED: テーブルID、データセットID、プロジェクト、フルパス、テーブル種別の保持を検証するテストを書く
  - GREEN: frozen dataclass として TableInfo を実装し、全テストをパスさせる
  - REFACTOR: テーブル種別の Literal 型定義を追加し、型安全性を確保する
  - _Requirements: 2.2, 3.2_

- [ ] 1.3 (P) 一括ロード結果を表現するデータ構造を実装する
  - RED: 成功件数、失敗件数、テーブル総数、エラー辞書の保持を検証するテストを書く
  - GREEN: LoadResult dataclass を実装し、全テストをパスさせる
  - REFACTOR: デフォルト値とファクトリ関数を整理し、使いやすいインターフェースにする
  - _Requirements: 4.4_

- [ ] 1.4 (P) カスタム例外クラス階層を実装する
  - RED: 各例外クラスのインスタンス化、継承関係、メッセージ取得を検証するテストを書く
  - GREEN: DatasetLoaderError をベースに AuthenticationError、PermissionDeniedError、DatasetNotFoundError、NetworkError を実装する
  - REFACTOR: 各例外に解決方法のガイダンスメッセージを追加する
  - _Requirements: 1.3, 1.4, 2.3, 5.3_

- [ ] 2. BigQuery クライアントアダプターの実装
- [ ] 2.1 アダプターの初期化と認証処理を実装する
  - RED: アダプターの初期化、認証情報の取得、認証失敗時の例外変換を検証するモックテストを書く
  - GREEN: BQClientAdapter のコンストラクタと認証処理を実装し、全テストをパスさせる
  - REFACTOR: コンテキストマネージャー対応とリソースクリーンアップ処理を追加する
  - 依存: タスク 1.4（例外クラス）の完了が必要
  - _Requirements: 5.1, 5.2, 5.3_

- [ ] 2.2 データセット一覧取得機能を実装する
  - RED: データセット一覧取得、SDK オブジェクトから DatasetInfo への変換を検証するモックテストを書く
  - GREEN: list_datasets メソッドを実装し、全テストをパスさせる
  - REFACTOR: 権限エラー、ネットワークエラーの例外変換処理を追加する
  - 依存: タスク 2.1（アダプター初期化）の完了が必要
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 2.3 テーブル一覧取得機能を実装する
  - RED: テーブル一覧取得、SDK オブジェクトから TableInfo への変換を検証するモックテストを書く
  - GREEN: list_tables メソッドを実装し、全テストをパスさせる
  - REFACTOR: NotFound エラー処理、ページネーション対応を確認し、例外変換を追加する
  - 依存: タスク 2.1（アダプター初期化）の完了が必要
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 3. データセットローダーの実装
- [ ] 3.1 ローダーの初期化とオンメモリデータ保持構造を実装する
  - RED: アダプターの受け取り、内部辞書構造の初期化を検証するテストを書く
  - GREEN: DatasetLoader のコンストラクタと内部データ構造を実装し、全テストをパスさせる
  - REFACTOR: アダプターが未指定の場合の新規作成ロジックを追加し、インターフェースを整理する
  - 依存: タスク 2.1（アダプター）の完了が必要
  - _Requirements: 3.1, 3.2_

- [ ] 3.2 一括ロード機能を実装する
  - RED: 全データセット・全テーブルの取得、辞書への登録、エラー継続処理を検証するモックテストを書く
  - GREEN: load_all メソッドを実装し、全テストをパスさせる
  - REFACTOR: 進捗コールバック対応、LoadResult の生成ロジックを追加し、エラーハンドリングを整理する
  - 依存: タスク 3.1（ローダー初期化）の完了が必要
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 3.3 O(1) 検索機能を実装する
  - RED: データセットID検索、テーブルフルパス検索、データセット別テーブル一覧取得を検証するテストを書く
  - GREEN: get_dataset、get_table、get_tables_by_dataset メソッドと datasets、tables プロパティを実装する
  - REFACTOR: 存在しないキーへの None 返却、計算量 O(1) の動作を確認し、インターフェースを整理する
  - 依存: タスク 3.2（一括ロード）の完了が必要
  - _Requirements: 3.3, 3.4_

- [ ] 4. エントリーポイントとの統合を実装する
  - RED: ローダーのインスタンス化、一括ロード実行、結果表示の一連の流れを検証する統合テストを書く
  - GREEN: サンプル実行コードを作成し、進捗コールバックとサマリー表示を実装する
  - REFACTOR: エラーハンドリングとユーザーフレンドリーな出力形式を整理する
  - 依存: タスク 3.3（検索機能）の完了が必要
  - _Requirements: 4.1, 4.2, 4.4_

- [ ]* 5. 実環境での統合テストを実装する
  - 実際の BigQuery API を使用した統合テスト（テスト用プロジェクト）を作成する
  - ADC 認証が正常に動作することを確認する
  - データセット・テーブルの取得からオンメモリ保持、検索までの一連の流れを検証する
  - 本タスクは実環境でのエンドツーエンド検証のため、MVP後に実施可能
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 3.3, 3.4, 4.1, 5.1_
