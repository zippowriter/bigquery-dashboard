# BigQuery table reference

## 概要
このプロジェクトはBigQueryのテーブル参照回数をAPI経由で取得するプログラムです。
INFORMATION_SCHEMA.JOBSビュー、auditlogsの2経路から参照数を計算します。

## TODO
BigQueryのINFORMATION_SCHEMA.JOBSとauditlogから各テーブルが何回参照されているかを計算する。
この時、BigQueryの対象のプロジェクト、データセットに存在する全てのテーブルの参照回数を記録する。

### BigQueryクライアントと通信可能にする
- [ ] BigQueryクライアントを作成する
- [ ] 通信可能状態を確認する

### SQLクエリを文字列で作成する
- [ ] SQLクエリを文字列で作成する
- [ ] SQLクエリの構文エラーがない状態を作る

### INFORMATION_SCHEMA.JOBSからテーブル参照データを取得する
- [ ] INFORMATION_SCHEMA.JOBSをSQLクエリで取得する

### auditlogからテーブル参照データを取得する
- [ ] auditlogをSQLクエリで取得する

### 対象のプロジェクトのデータセットを取得する
- [ ] プロジェクトを指定することができるようにする
- [ ] 開発環境のデータセットを取得できるようにする

### 全データセットのテーブルを取得する
- [ ] 単一データセットのテーブルを取得する
- [ ] 全データセットのテーブルを取得し構造化データに変換する
