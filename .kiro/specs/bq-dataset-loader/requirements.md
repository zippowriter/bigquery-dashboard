# Requirements Document

## Introduction

本ドキュメントは、BigQueryデータセットローダー機能の要件を定義する。この機能は、BigQueryのデータセット情報を取得し、Pythonのオンメモリデータ構造に保存することで、後続の分析処理（テーブル参照回数の集計など）の基盤となる。

## Requirements

### Requirement 1: データセット一覧取得

**Objective:** データエンジニアとして、指定したプロジェクト内のデータセット一覧を取得したい。これにより、分析対象となるデータセットを把握できる。

#### Acceptance Criteria

1. When プロジェクトIDが指定される, the DatasetLoader shall BigQuery APIを呼び出してプロジェクト内の全データセット一覧を取得する
2. When データセット一覧の取得が完了する, the DatasetLoader shall 各データセットのID、フルパス（project.dataset形式）、作成日時、最終更新日時を含むデータ構造を返す
3. If BigQuery APIへのアクセス権限がない, then the DatasetLoader shall 権限エラーを明示的に通知する
4. If ネットワークエラーが発生する, then the DatasetLoader shall 適切なエラーメッセージとともに例外を発生させる

### Requirement 2: テーブル一覧取得

**Objective:** データエンジニアとして、指定したデータセット内のテーブル一覧を取得したい。これにより、各データセットに含まれるテーブルを把握できる。

#### Acceptance Criteria

1. When データセットIDが指定される, the DatasetLoader shall 指定データセット内の全テーブル一覧を取得する
2. When テーブル一覧の取得が完了する, the DatasetLoader shall 各テーブルのID、フルパス（project.dataset.table形式）、テーブル種別（TABLE/VIEW/MATERIALIZED_VIEW等）を含むデータ構造を返す
3. If 指定されたデータセットが存在しない, then the DatasetLoader shall NotFoundエラーを発生させる
4. While テーブル数が多い場合, the DatasetLoader shall ページネーションを適切に処理して全テーブルを取得する

### Requirement 3: オンメモリデータ構造

**Objective:** 開発者として、取得したデータセット・テーブル情報を効率的に参照できるデータ構造に保存したい。これにより、後続の分析処理が高速に実行できる。

#### Acceptance Criteria

1. The DatasetLoader shall 取得したデータセット一覧をPythonのデータクラスまたは辞書形式でオンメモリに保持する
2. The DatasetLoader shall 取得したテーブル一覧を親データセットとの関連を維持した形でオンメモリに保持する
3. When データセットIDで検索する, the DatasetLoader shall O(1)の計算量で該当データセットの情報を返す
4. When テーブルのフルパスで検索する, the DatasetLoader shall 該当テーブルの情報を効率的に返す

### Requirement 4: 一括ロード機能

**Objective:** データエンジニアとして、プロジェクト内の全データセットと全テーブル情報を一括で取得したい。これにより、初期化処理を簡潔に記述できる。

#### Acceptance Criteria

1. When プロジェクトIDが指定される, the DatasetLoader shall プロジェクト内の全データセットと、各データセット内の全テーブルを一括で取得する
2. While 一括ロード処理中, the DatasetLoader shall 進捗状況を把握できる仕組みを提供する（ログ出力またはコールバック）
3. If いずれかのデータセットでエラーが発生する, then the DatasetLoader shall エラーをログに記録しつつ、他のデータセットの処理を継続する
4. When 一括ロードが完了する, the DatasetLoader shall 取得成功件数と失敗件数のサマリを返す

### Requirement 5: BigQuery認証

**Objective:** 運用担当者として、既存のGoogle Cloud認証情報を利用してBigQueryに接続したい。これにより、追加の認証設定なしで利用を開始できる。

#### Acceptance Criteria

1. The DatasetLoader shall Google Cloud SDKのデフォルト認証情報（ADC: Application Default Credentials）を使用してBigQueryに接続する
2. Where サービスアカウントキーファイルのパスが環境変数で指定されている, the DatasetLoader shall 指定されたサービスアカウントで認証する
3. If 有効な認証情報が見つからない, then the DatasetLoader shall 認証エラーを明示的に通知し、解決方法を示すメッセージを含める
