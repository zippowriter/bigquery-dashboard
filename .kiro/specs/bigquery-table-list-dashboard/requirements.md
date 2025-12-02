# Requirements Document

## Project Description (Input)
対象プロジェクトのBigQueryテーブルをデータセットと一緒にテーブル名を取得し、その一覧情報をpandas.DataFrameとして保持し、Dashboardのトップページに表形式で表示する。グラフ化にはplotlyを用いること。複雑なロジックや、やりすぎななクラス設計は行わず、必要最低限のコード量で実装すること。

## Introduction
本ドキュメントは、BigQueryテーブル一覧ダッシュボード機能の要件を定義する。
対象プロジェクト内のBigQueryテーブル情報を取得し、データセット名とテーブル名を一覧表示するダッシュボード機能を実現する。

## Requirements

### Requirement 1: BigQueryテーブル情報の取得
**Objective:** As a データ基盤管理者, I want 対象プロジェクトのBigQueryテーブル一覧を取得したい, so that テーブルの存在状況を把握できる

#### Acceptance Criteria
1. When ダッシュボードアプリケーションが起動した時, the Dashboard shall 対象GCPプロジェクトのBigQueryテーブル一覧を取得する
2. The Dashboard shall 各テーブルについてデータセット名とテーブル名を取得する
3. The Dashboard shall 取得したテーブル情報をpandas.DataFrameとして保持する
4. If BigQuery APIへの接続に失敗した場合, then the Dashboard shall エラーメッセージを表示する

### Requirement 2: テーブル一覧の表形式表示
**Objective:** As a データ基盤管理者, I want テーブル一覧を表形式で確認したい, so that テーブル情報を一目で把握できる

#### Acceptance Criteria
1. The Dashboard shall トップページにテーブル一覧を表形式で表示する
2. The Dashboard shall 表にデータセット名カラムを含める
3. The Dashboard shall 表にテーブル名カラムを含める
4. When テーブル情報が0件の場合, the Dashboard shall テーブルが存在しない旨のメッセージを表示する

### Requirement 3: Plotlyによる表コンポーネント
**Objective:** As a 開発者, I want Plotlyを使用して表を描画したい, so that Dashエコシステムと統合された一貫性のある表示ができる

#### Acceptance Criteria
1. The Dashboard shall Plotlyのテーブルコンポーネントを使用してテーブル一覧を描画する
2. The Dashboard shall pandas.DataFrameからPlotlyテーブルへの変換を行う

### Requirement 4: シンプルな実装構造
**Objective:** As a 開発者, I want 必要最低限のコード量で実装したい, so that 保守性が高くシンプルなコードベースを維持できる

#### Acceptance Criteria
1. The Dashboard shall 既存のレイヤードアーキテクチャ（config, layout, app, server）に従って実装する
2. The Dashboard shall 複雑なクラス設計を避け、関数ベースの実装とする
3. The Dashboard shall BigQueryクライアント処理を単一モジュールに集約する
