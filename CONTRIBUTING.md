# mcp-pipeline への貢献ガイド

コントリビューションに興味を持っていただきありがとうございます！  
このドキュメントでは、プロジェクトへの貢献方法を説明します。

## 目次

- [行動規範](#行動規範)
- [はじめに](#はじめに)
- [開発環境のセットアップ](#開発環境のセットアップ)
- [貢献の方法](#貢献の方法)
- [プルリクエストの手順](#プルリクエストの手順)
- [コーディング規約](#コーディング規約)

## 行動規範

すべてのやり取りにおいて、相互尊重と建設的な姿勢を大切にしてください。  
経験レベルや背景を問わず、あらゆる貢献者を歓迎します。

## はじめに

1. GitHub 上でリポジトリをフォークする
2. ローカルにクローンする:
   ```bash
   git clone https://github.com/edamanu418/mcp-pipeline.git
   cd mcp-pipeline
   ```
3. upstream リモートを追加する:
   ```bash
   git remote add upstream https://github.com/edamanu418/mcp-pipeline.git
   ```

## 開発環境のセットアップ

### 必要条件

- Python 3.10 以上

### pip を使う場合

```bash
cd mcp-server
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -e ".[dev]"
```

### 動作確認

```bash
python -m src.main
```

エラーなくサーバーが起動すれば OK です。

## 貢献の方法

### バグを報告する

Issue を開く際は [Bug Report テンプレート](.github/ISSUE_TEMPLATE/bug_report.md) を使用してください。  
以下の情報を含めてください:

- 再現手順
- 期待される動作と実際の動作
- Python バージョンと OS
- 関連するログやエラーメッセージ

### 機能を提案する

[Feature Request テンプレート](.github/ISSUE_TEMPLATE/feature_request.md) を使用してください。  
以下を記載してください:

- 解決したい問題
- 提案する解決策
- 検討した代替案

### コードを貢献する

1. 既存の [Issue](https://github.com/edamanu418/mcp-pipeline/issues) を確認するか、変更内容について新しい Issue で議論する
2. `main` ブランチからフィーチャーブランチを作成する:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. [コーディング規約](#コーディング規約) に従って変更を加える
4. 必要に応じてテストを追加・更新する
5. テストスイートを実行する:
   ```bash
   cd mcp-server
   python -m pytest tests/
   ```
6. わかりやすいコミットメッセージでコミットする
7. プッシュしてプルリクエストを開く

## プルリクエストの手順

1. `main` ブランチとの差分が最新であることを確認する
2. PR テンプレートに必要事項を記入する
3. 関連する Issue をリンクする（例: `Closes #123`）
4. メンテナーにレビューを依頼する
5. レビューのフィードバックに速やかに対応する
6. PR はスカッシュマージで取り込みます

## コーディング規約

### スタイル

- Python コードは [PEP 8](https://pep8.org/) に従う
- `ruff` でリントを実行する:
  ```bash
  ruff check mcp-server/src/
  ```
- 最大行長: 160 文字

### 型ヒント

- すべての公開関数に型ヒントを付ける
- `mypy` で型チェックを実行する:
  ```bash
  mypy mcp-server/src/
  ```

### コミットメッセージ

命令形で簡潔に記述してください:

- `complete_task にタイムスタンプを追加`
- `task_order のオフバイワンエラーを修正`
- `WorkflowBase をテストしやすい構造にリファクタリング`

### 新しいツールを追加する場合

`mcp-server/src/tools/` の既存パターンに従ってください:

1. `mcp-server/src/tools/your_tool.py` を作成する
2. `WorkflowBase` を継承したクラスで関数と `TOOL_DESCRIPTION` 定数を定義する
3. `mcp-server/src/tools/__init__.py` からエクスポートする
4. `mcp-server/src/main.py` にツールを登録する

### `core/` を変更する場合

`src/core/` はドメインに依存しない再利用可能な基盤です。  
変更する場合は mcp-pipeline 固有のロジックを混入させないよう注意してください。

## 質問がある場合

Issue に収まらない質問は [Discussions](https://github.com/edamanu418/mcp-pipeline/discussions) でどうぞ。
