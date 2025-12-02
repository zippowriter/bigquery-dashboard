# Requirements Document

## Introduction

BigQueryのINFORMATION_SCHEMA.JOBS_BY_PROJECTビューを活用し、各テーブルの参照回数と参照ユーザー数を分析するダッシュボード機能。既存実装でアプリ起動時に取得済みのテーブル一覧データと利用状況データを結合し、Dashフレームワークで表形式の可視化を提供する。データ基盤管理者やデータエンジニアが、テーブルの利用パターンを把握し、未使用テーブルの特定やデータ資産管理の意思決定を支援する。

## Requirements

### Requirement 1: テーブル利用状況データ取得

**Objective:** As a データ基盤管理者, I want BigQueryのJOBS_BY_PROJECTビューからテーブル参照情報を取得したい, so that 各テーブルの利用状況を定量的に把握できる

#### Acceptance Criteria

1. When ダッシュボードがデータを取得するとき, the BigQuery Client shall INFORMATION_SCHEMA.JOBS_BY_PROJECTビューからクエリジョブ情報を取得する
2. When クエリジョブ情報を集計するとき, the BigQuery Client shall 各テーブルごとの参照回数を算出する
3. When クエリジョブ情報を集計するとき, the BigQuery Client shall 各テーブルごとのユニーク参照ユーザー数を算出する
4. If BigQuery APIへの接続に失敗した場合, then the Dashboard shall エラーメッセージを表示する

### Requirement 2: データ結合

**Objective:** As a データ基盤管理者, I want 既存のテーブル一覧と利用状況を結合した統合データを取得したい, so that 未使用テーブルを含む全テーブルの利用状況を一覧で確認できる

#### Acceptance Criteria

1. When テーブル一覧と利用状況データが取得されたとき, the Dashboard shall 左結合（LEFT JOIN）でデータを結合する
2. When データを結合するとき, the Dashboard shall アプリ起動時に取得済みのテーブル一覧データを基準とする
3. When データを結合するとき, the Dashboard shall 利用実績がないテーブルも結果に含める
4. The Dashboard shall 結合後のデータに参照回数0件のテーブルを表示する

### Requirement 3: ダッシュボード表示

**Objective:** As a データ基盤管理者, I want テーブル利用状況を表形式で確認したい, so that 直感的にテーブルの利用パターンを把握できる

#### Acceptance Criteria

1. When ダッシュボードを表示するとき, the Dashboard shall テーブル一覧と利用状況を表形式（DataTable）で表示する
2. The Dashboard shall テーブルID、データセットID、参照回数、参照ユーザー数を列として表示する
3. When ユーザーが列ヘッダーをクリックしたとき, the Dashboard shall その列で昇順・降順ソートを切り替える
4. While データを表示しているとき, the Dashboard shall 参照回数が0件のテーブルを視覚的に識別可能にする

### Requirement 4: アプリケーション起動

**Objective:** As a 開発者, I want アプリケーションを起動してダッシュボードにアクセスしたい, so that ローカル環境でテーブル利用状況を確認できる

#### Acceptance Criteria

1. When アプリケーションを起動したとき, the Dashboard shall 設定されたポートでHTTPサーバーを起動する
2. When ブラウザでダッシュボードURLにアクセスしたとき, the Dashboard shall テーブル利用状況ダッシュボードを表示する
3. The Dashboard shall 環境変数またはデフォルト設定からBigQueryプロジェクトIDを読み込む
