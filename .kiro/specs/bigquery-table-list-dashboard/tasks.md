# Implementation Plan

## Tasks

- [x] 1. 設定層にBigQueryプロジェクトID設定を追加する
  - AppConfigにBigQuery対象プロジェクトIDの設定フィールドを追加する
  - 環境変数 `GOOGLE_CLOUD_PROJECT` からデフォルト値を取得する
  - プロジェクトIDが設定されていない場合はOptionalとして扱う
  - _Requirements: 4.1_

- [x] 2. (P) BigQueryテーブル一覧取得機能を実装する
  - 対象プロジェクトの全データセットを取得する
  - 各データセット内の全テーブルを取得する
  - データセット名とテーブル名をpandas.DataFrameとして返却する
  - BigQuery API接続エラー時は適切な例外をスローする
  - _Requirements: 1.1, 1.2, 1.3, 4.3_

- [x] 3. (P) DataFrameからPlotlyテーブルへの変換機能を実装する
  - DataFrameをPlotly go.Table形式のFigureに変換する
  - ヘッダーにデータセット名カラムとテーブル名カラムを含める
  - テーブルの外観を適切にスタイリングする
  - _Requirements: 2.2, 2.3, 3.1, 3.2_

- [x] 4. レイアウト層にテーブル一覧表示機能を統合する
- [x] 4.1 build_layout関数を拡張してテーブル一覧を表示する
  - レイアウト構築時にBigQueryからテーブル一覧を取得する
  - 取得したデータをPlotlyテーブルとしてトップページに表示する
  - dcc.GraphコンポーネントでPlotly Figureを埋め込む
  - _Requirements: 1.1, 2.1, 3.1_

- [x] 4.2 エラー状態と空データ状態のハンドリングを実装する
  - BigQuery API接続エラー時にエラーメッセージを表示する
  - テーブル情報が0件の場合に適切なメッセージを表示する
  - _Requirements: 1.4, 2.4_

- [x] 5. アプリケーション層でプロジェクトID設定を連携する
  - app.pyでconfigからproject_idを取得してlayout構築に渡す
  - project_idがNoneの場合はテーブル表示をスキップする
  - _Requirements: 4.1, 4.2_

- [x] 6. 単体テストを実装する
- [x] 6.1 (P) BigQueryクライアントのテストを実装する
  - fetch_table_list関数がDataFrameを返却することをモックで検証する
  - 返却されるDataFrameが正しいカラム構造を持つことを検証する
  - APIエラー時の例外処理を検証する
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 6.2 (P) Plotlyテーブル変換のテストを実装する
  - create_table_figure関数がgo.Figureを返却することを検証する
  - DataFrameのカラムがテーブルヘッダーに反映されることを検証する
  - _Requirements: 3.1, 3.2_

- [x] 6.3 レイアウト構築のテストを実装する
  - build_layout関数がhtml.Divを返却することを検証する
  - エラー状態時のメッセージ表示を検証する
  - 空データ状態時のメッセージ表示を検証する
  - _Requirements: 1.4, 2.1, 2.4_
