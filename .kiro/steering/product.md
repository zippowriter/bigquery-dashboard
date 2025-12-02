# Product Overview

BigQueryのテーブル利用状況を可視化するダッシュボードアプリケーション。
データ基盤管理者やデータエンジニアが、BigQueryテーブルの参照パターンを把握し、最適化の意思決定を支援する。

## Core Capabilities

- **テーブル利用分析**: BigQueryテーブルの参照頻度・パターンを分析
  - テーブル一覧取得（全データセット横断）
  - 参照回数・ユニークユーザー数の集計（INFORMATION_SCHEMA.JOBS_BY_PROJECT）
- **可視化ダッシュボード**: Dashによるインタラクティブな利用状況表示
  - 未使用テーブルのハイライト表示（参照回数0件）
  - リーフノードテーブルのハイライト表示（下流テーブルなし）
  - ソート可能なDataTable、リアルタイム更新ボタン
- **Google Cloud連携**: BigQuery API・Data Lineage APIとの統合
- **キャッシュ機構**: CSVファイルキャッシュによる起動時間短縮

## Target Use Cases

- BigQueryの全テーブルの利用状況モニタリング
- 未使用テーブルの特定
- テーブルリネージにおけるリーフノードのテーブルの特定

## Value Proposition

BigQueryのINFORMATION_SCHEMAやauditlogsから取得した情報を
直感的なダッシュボードで可視化し、データ資産の管理効率を向上させる。

---
_Focus on patterns and purpose, not exhaustive feature lists_

<!-- updated_at: 2025-12-03 -->
<!-- sync: Added leaf table detection, caching, and Data Lineage API integration -->
