# Product Overview

BigQuery テーブル利用状況分析ツール。組織内の BigQuery テーブルの参照状況を可視化し、未使用・低利用テーブルの特定を支援する。

## Core Capabilities

- **テーブル一覧取得**: 複数プロジェクトからテーブルメタデータを収集
- **参照回数分析**: JOBS ログからテーブル参照回数・ユニークユーザー数を集計
- **テーブルリネージ情報取得**: Lineage APIからリネージ情報を収集
- **利用状況可視化**: Streamlit ダッシュボードによる視覚的な分析

## Target Use Cases

- データ基盤チームによる未使用テーブルの棚卸し
- ストレージコスト最適化のための削除候補テーブル特定
- データオーナーへの利用状況レポーティング

## Value Proposition

BigQuery の INFORMATION_SCHEMA と JOBS ログを組み合わせ、テーブルの「存在」と「利用実態」、「依存状況」のギャップを明確化。データガバナンスの意思決定を支援する。

---
_Focus on patterns and purpose, not exhaustive feature lists_
