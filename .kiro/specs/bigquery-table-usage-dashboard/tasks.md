## Tasks

- [x] 1. INFORMATION_SCHEMAからテーブル利用統計を取得する機能を実装
  - [x] 1.1 (P) BigQueryのJOBS_BY_PROJECTビューからテーブル参照情報を集計するクエリを実装
    - INFORMATION_SCHEMA.JOBS_BY_PROJECTからreferenced_tablesをUNNESTして集計
    - 各テーブルごとの参照回数（クエリジョブ数）を算出
    - 各テーブルごとのユニーク参照ユーザー数をCOUNT DISTINCTで算出
    - project_idとregionをパラメータとして受け取る
    - 結果をDataFrame形式（dataset_id, table_id, reference_count, unique_users）で返却
    - project_idが空文字の場合はValueErrorを発生
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 1.2 テーブル利用統計取得の単体テストを作成
    - 空結果時のDataFrameスキーマ検証（4カラム構成の確認）
    - project_id空文字時のValueError発生検証
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. テーブル一覧と利用統計のデータ結合機能を実装
  - [x] 2.1 (P) 既存テーブル一覧と利用統計をLEFT JOINで結合する関数を実装
    - テーブル一覧DataFrame（dataset_id, table_id）を左側基準として結合
    - 結合キーは（dataset_id, table_id）の組み合わせ
    - 利用実績がないテーブルはreference_count=0、unique_users=0で補完
    - 結合後も全テーブルを保持し、未使用テーブルを含める
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 2.2 データ結合の単体テストを作成
    - 欠損値の0補完確認
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 3. Dash DataTableによる表形式表示機能を実装
  - [x] 3.1 (P) 利用統計DataFrameからDash DataTableコンポーネントを生成する関数を実装
    - DataFrameからDataTableを生成
    - データセットID、テーブルID、参照回数、参照ユーザー数を列として表示
    - 列ヘッダーに日本語名を設定（データセットID、テーブルID、参照回数、参照ユーザー数）
    - ネイティブソート機能を有効化（sort_action="native"、sort_mode="multi"）
    - 参照回数0件の行に条件付きスタイル（薄い赤の背景色）を適用
    - ヘッダーにスタイル設定（背景色、太字）
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 DataTable生成の単体テストを作成
    - DataTableカラム設定の確認
    - 条件付きスタイル設定の確認（reference_count=0のフィルタクエリ）
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4. ダッシュボードレイアウトに利用統計を統合
  - [x] 4.1 build_layout関数を拡張して利用統計を統合表示
    - テーブル一覧取得、利用統計取得、データ結合、DataTable生成の一連の処理を実行
    - 既存のgo.Table表示をDataTable表示に置き換え
    - GoogleAPIError発生時はエラーメッセージを表示
    - project_idがNoneの場合はテーブル表示をスキップ（既存動作維持）
    - _Requirements: 1.4, 4.2_

  - [x] 4.2 レイアウト統合の単体テストを作成
    - 正常時のDataTable生成確認
    - project_id=None時の動作確認
    - _Requirements: 1.4, 4.2_

- [x] 5. 設定とサーバー起動の確認
  - [x] 5.1 環境変数からBigQueryプロジェクトIDとリージョン設定を読み込む機能を確認
    - 既存のAppConfigでプロジェクトID設定が利用可能であることを確認
    - リージョン設定が必要な場合は追加
    - 設定されたポートでHTTPサーバーが起動することを確認
    - _Requirements: 4.1, 4.3_

- [x] 6. エンドツーエンド動作確認
  - [x] 6.1 アプリケーション起動からダッシュボード表示までの統合確認
    - アプリケーション起動時にテーブル一覧と利用統計を取得
    - ブラウザでダッシュボードURLにアクセスしてテーブル利用状況ダッシュボードを表示
    - 列ヘッダークリックでソート切り替えが動作することを確認
    - 参照回数0件のテーブルが視覚的に識別可能であることを確認
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2_
