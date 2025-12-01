# 技術スタック

## アーキテクチャ

シンプルなCLIツールアーキテクチャ。BigQuery APIを直接呼び出し、SQLクエリでメタデータを取得・集計する。

## コア技術

- **言語**: Python 3.14+
- **パッケージ管理**: uv
- **BigQuery連携**: Google Cloud BigQuery Client Library (予定)

## 主要ライブラリ

- `google-cloud-bigquery`: BigQuery APIクライアント (導入予定)
- `pytest`: テストフレームワーク

## 開発標準

### 型安全性
- Python型ヒントを積極的に使用
- 主要な関数・メソッドには型アノテーションを付与
- `Optional`や`Union`は使用せず、`|`演算子で代用する
  - 例: `Optional[str]` → `str | None`
  - 例: `Union[str, int]` → `str | int`
- `Any`型は使用禁止（型安全性を損なうため）

### ドメインモデル
- 全てのドメインモデルはPydanticの`BaseModel`を継承して実装する
- イミュータブルなモデルには`frozen=True`を設定する

### コード品質
- Pythonの標準的なコーディング規約(PEP 8)に準拠
- 明確な関数・変数命名
- **静的解析必須**: 全てのコード（テストコード含む）に対して以下を実行
  - `ruff check`: リントチェック
  - `pyright`: 型チェック
- **静的解析エラー回避のルール**:
  - `# type: ignore`や`# noqa`などの静的解析エラー回避コメントは原則禁止
  - TDDサイクル（RED→GREEN→REFACTOR）のREFACTORフェーズでのみ検討可
  - REFACTORフェーズで他に解決策がない場合に限り、理由をコメントで明記した上で使用可

### テスト
- pytestによる単体テスト
- `tests/`ディレクトリにテストコードを配置
- テストコードにもruffとpyrightのチェックを必ず適用する

## 開発環境

### 必要ツール
- Python 3.14+
- uv (パッケージマネージャー)
- Google Cloud SDK (認証用)

### 主要コマンド
```bash
# 実行: uv run python main.py
# テスト: uv run pytest
# 依存追加: uv add <package>
```

## 技術的な設計判断

- **uv採用**: 高速な依存解決と仮想環境管理のため
- **INFORMATION_SCHEMA + auditlog併用**: 単一ソースでは取得できない情報を補完するため
- **シンプルなエントリーポイント**: main.pyを起点とした単純な構造で開始

---
_標準とパターンを文書化。全依存関係のリストではない_
