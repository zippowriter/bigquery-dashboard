# Research & Design Decisions

## Summary
- **Feature**: `dash-dashboard-init`
- **Discovery Scope**: New Feature (グリーンフィールド開発)
- **Key Findings**:
  - Dash 3.3.0が最新の安定版であり、Python 3.8以上をサポート
  - `debug=True`でホットリロードが自動有効化される
  - Flaskベースのため、既存のPython Webパターンが適用可能

## Research Log

### Dash フレームワーク最新バージョンと互換性
- **Context**: 要件で指定されたDashフレームワークの最新状態を確認
- **Sources Consulted**:
  - [PyPI - dash](https://pypi.org/project/dash/)
  - [Dash Documentation](https://dash.plotly.com/)
  - [Dash Layout Guide](https://dash.plotly.com/layout)
- **Findings**:
  - 最新バージョン: 3.3.0 (2025年11月12日リリース)
  - Python 3.8, 3.9, 3.10, 3.11, 3.12をサポート
  - 主要依存関係: Plotly.js, React, Flask
  - ライセンス: MIT
- **Implications**:
  - プロジェクトはPython 3.13を要求しているが、Dashは3.12までの公式サポート
  - Python 3.13での動作は要検証だが、通常は後方互換性あり
  - Dash 2.x系を使用する選択肢も検討可能

### Dash アプリケーション初期化パターン
- **Context**: 基本的なDashアプリケーションの構成方法を調査
- **Sources Consulted**:
  - [Dash Layout Documentation](https://dash.plotly.com/layout)
  - [Dash Dev Tools](https://dash.plotly.com/devtools)
- **Findings**:
  - 基本パターン:
    ```python
    from dash import Dash, html, dcc
    app = Dash()
    app.layout = html.Div([...])
    app.run(debug=True)
    ```
  - デフォルトポート: 8050
  - デフォルトホスト: 127.0.0.1
  - `debug=True`で開発ツールが有効化される
- **Implications**:
  - シンプルな初期化パターンで要件を満たせる
  - 将来のマルチページ対応には`use_pages=True`が有効

### デバッグモードとホットリロード
- **Context**: 開発モードでの自動リロード機能を確認
- **Sources Consulted**:
  - [Dash Dev Tools](https://dash.plotly.com/devtools)
  - [Stack Overflow - Hot reload issues](https://stackoverflow.com/questions/62378947/hot-reload-in-dash-does-not-automatically-update)
- **Findings**:
  - `debug=True`でホットリロードが自動有効化
  - ソースコード変更時にブラウザが自動更新
  - エラー発生時はブラウザ上にエラー詳細を表示
  - 注意: Jupyter環境では`use_reloader=False`が必要な場合あり
- **Implications**:
  - 要件4のデバッグモード対応は標準機能で実現可能
  - 追加実装は不要

### HTML コンポーネントとスタイリング
- **Context**: レイアウト構成に使用するコンポーネントを確認
- **Sources Consulted**:
  - [Dash Layout Documentation](https://dash.plotly.com/layout)
- **Findings**:
  - `dash.html`で標準HTMLタグをPythonクラスとして使用
  - スタイルはdictionary形式で指定（CSSプロパティはcamelCase）
  - `className`属性でCSSクラスを指定
  - `children`は第一位置引数として省略可能
- **Implications**:
  - 基本レイアウト(要件3)はhtml.Div, html.H1等で実装

### Python 型ヒントのベストプラクティス
- **Context**: プロジェクトでpyrightを使用しているため、型安全性を確認
- **Sources Consulted**:
  - [Python typing documentation](https://docs.python.org/3/library/typing.html)
  - [Meta - Typed Python in 2024](https://engineering.fb.com/2024/12/09/developer-tools/typed-python-2024-survey-meta/)
- **Findings**:
  - Python 3.9+ではネイティブコレクション型が使用可能（`list[str]`形式）
  - Dashのコンポーネントは動的型が多いが、Pydanticで境界を保護可能
  - pyrightはリアルタイムフィードバックを提供
- **Implications**:
  - 設定値やインターフェースにはPydanticモデルを活用
  - Dashコンポーネント自体の型付けは限定的に対応

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| Single Module | 1つのapp.pyファイルに全機能を実装 | シンプル、初期段階に最適 | 拡張性に制限 | 初期化フェーズに適切 |
| Multi-Page Structure | pages/フォルダでページを分離 | 将来の拡張が容易 | 初期オーバーヘッド | 今回のスコープ外 |
| Package Structure | src/パッケージ構成 | 既存のpyproject.tomlに適合 | 初期設定が複雑 | 推奨アプローチ |

**選択**: Package Structure
- 既存の`pyproject.toml`で`src/bq_table_reference`パッケージが定義済み
- 今後のBigQuery機能拡張との統合を考慮

## Design Decisions

### Decision: エントリーポイントファイルの配置
- **Context**: 要件5でエントリーポイント(app.pyまたはmain.py)を持つことが求められている
- **Alternatives Considered**:
  1. プロジェクトルートにapp.py
  2. src/配下にパッケージ構成
- **Selected Approach**: プロジェクトルートに`app.py`を配置し、将来的にsrc/からインポート
- **Rationale**:
  - Dash標準のプロジェクト構成に準拠
  - シンプルな起動コマンド(`python app.py`)
  - 既存のpyproject.toml構成との共存が可能
- **Trade-offs**:
  - プロジェクトルートにファイルが増加
  - 将来的にリファクタリングの可能性
- **Follow-up**: 機能拡張時にsrc/への移行を検討

### Decision: Dashバージョンの選択
- **Context**: 最新のDash 3.3.0を使用するか、安定したDash 2.x系を使用するか
- **Alternatives Considered**:
  1. Dash 3.x系（最新）
  2. Dash 2.18.x系（安定版）
- **Selected Approach**: Dash 2.18.x系を使用
- **Rationale**:
  - Python 3.13との互換性が確認しやすい
  - 2.x系は広く使用され、ドキュメントが豊富
  - 将来的に3.x系への移行も容易
- **Trade-offs**:
  - 最新機能の一部が利用不可
- **Follow-up**: Python 3.13での動作確認後、バージョンアップを検討

### Decision: 依存関係管理
- **Context**: 要件5でuvパッケージマネージャーでの依存関係管理が求められている
- **Selected Approach**: pyproject.tomlのdependenciesにdashを追加
- **Rationale**:
  - 既存のpyproject.toml構成を維持
  - uvコマンドで一貫した依存関係管理
- **Trade-offs**: なし

## Risks & Mitigations
- **Risk 1**: Python 3.13とDashの互換性問題
  - Mitigation: 起動時のテストで動作確認、問題発生時はPython 3.12へのダウングレードを検討
- **Risk 2**: ポート8050が既に使用されている場合
  - Mitigation: 起動時のエラーメッセージで明確に通知、ポート設定オプションを提供
- **Risk 3**: 将来の機能拡張時のアーキテクチャ変更
  - Mitigation: 初期設計でモジュール分離を考慮したディレクトリ構成を採用

## References
- [Dash Documentation & User Guide](https://dash.plotly.com/) - 公式ドキュメント
- [PyPI - dash](https://pypi.org/project/dash/) - パッケージ情報
- [Dash Layout Documentation](https://dash.plotly.com/layout) - レイアウト構成
- [Dash Dev Tools](https://dash.plotly.com/devtools) - 開発ツール
- [Plotly Community Forum - Best Practices](https://community.plotly.com/t/best-practices-in-dash/85078) - ベストプラクティス
