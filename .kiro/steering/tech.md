# 技術スタック

## アーキテクチャ

レイヤードアーキテクチャを採用したCLIツール。BigQuery Client Libraryを使用してメタデータを取得・集計する。

**レイヤー構成**:
- **Domain層**: Pydanticモデルによるドメインオブジェクト、カスタム例外
- **Application層**: ユースケースの実装（DatasetLoaderなど）
- **Infrastructure層**: BigQuery APIとの連携（BQClientAdapter）

## コア技術

- **言語**: Python 3.13
- **パッケージ管理**: uv
- **BigQuery連携**: Google Cloud BigQuery Client Library
- **Cloud Logging連携**: Google Cloud Logging Client Library（Audit Log取得用）

## 主要ライブラリ

- `google-cloud-bigquery`: BigQuery APIクライアント
- `google-cloud-logging`: Cloud Logging APIクライアント（Audit Log取得）
- `pydantic`: ドメインモデル定義とバリデーション
- `pytest`: テストフレームワーク
- `ruff`: リンター/フォーマッター
- `pyright`: 型チェッカー

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

### ドキュメント
- **Docstring**: 各モジュール、クラス、メソッドにはDocstringをGoogle Styleで記述する
- **ドキュメント言語**: プロダクトコード、テストコードのdocstring（モジュール、クラス、メソッド）は日本語で記述する

## 開発環境

### 必要ツール
- Python 3.14+
- uv (パッケージマネージャー)
- Google Cloud SDK (認証用)

### 主要コマンド
```bash
# 実行: uv run python main.py --project <PROJECT_ID>
# テスト: uv run task test
# 単体テスト: uv run task test-unit
# 統合テスト: uv run task test-integration
# リント: uv run task lint
# 型チェック: uv run task type-check
# フォーマット: uv run task format
# 依存追加: uv add <package>
```

## 技術的な設計判断

- **uv採用**: 高速な依存解決と仮想環境管理のため
- **レイヤードアーキテクチャ**: 責務の分離とテスト容易性の確保
- **Pydanticモデル**: 型安全なドメインオブジェクトとバリデーション
- **アダプターパターン**: BigQuery SDKの抽象化とモック可能な設計
- **INFORMATION_SCHEMA + auditlog併用**: 単一ソースでは取得できない情報を補完するため
- **Protocol**: 依存性逆転のためのProtocolパターン（TypedProtocol使用）
- **進捗・エラーハンドリング**: コールバックベースの進捗報告と集中エラーハンドリング

---
_updated_at: 2025-12-02_
_変更: Python版を3.13に修正、google-cloud-loggingを追加、実装済み機能の反映_
_標準とパターンを文書化。全依存関係のリストではない_
