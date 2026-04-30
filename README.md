# mcp-pipeline

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

### LLM ワークフローを、確実に完走させる。

> LLM は賢い。しかし、放っておくと不安定になる。  
> ステップを飛ばす。順番を守らない。文脈を見失う。  
>
> 必要なのは「より賢くすること」ではなく、**「正しく制御すること」** 。

## ポジショニング

このプロジェクトは**エージェントフレームワークではありません**。

LLM 実行の**制御レイヤー**です。

| | アプローチ | 結果 |
|--|----------|--------|
| エージェントフレームワーク | LLM が何をするかを決める | 柔軟だが予測不能 |
| **mcp-pipeline** | サーバーが何をするかを強制する | 制御可能で再現性がある |

向いている用途：
- バッチ処理
- ビジネスワークフロー
- 再現性が必要なパイプライン

## 概要

**mcp-pipeline** は [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) を使ったタスクパイプライン実行制御サーバーです。

「設計書作成 → レビュー → コード生成 → テスト作成」のような一連のタスクをテキストで定義し、LLM に1タスクずつ実行させることで、手順のスキップや順番の乱れを防ぎます。

他の MCP サーバー（Filesystem・GitHub・Web Search など）と組み合わせることで、LLM を使った本格的なバッチ処理基盤として機能します。

### 解決する問題

```
❌ 従来のプロンプト
「設計書を作成して、レビューして、コードを書いて、テストも書いて」
→ LLMが設計書をスキップしていきなりコードを書き始めることがある

✅ mcp-pipeline
タスクを1つずつサーバーから渡すことで、LLMは「今このタスクだけ」に集中できる
→ 全タスクが確実に、定義した順番通りに実行される
```

### 主な特徴

- 🔗 **確実な順序実行**: タスクを1つずつ渡し、完了するまで次に進まない
- 📝 **プロンプト内蔵**: 各タスクに実行指示（prompt）を持たせ、LLMが何をすべきか明確
- 🔄 **output の連鎖**: 前タスクの実行結果を次タスクに自動で渡し、文脈を引き継ぐ
- 💾 **永続ストレージ**: JSON ベースの保存で、会話が途切れても途中から再開可能
- 🧭 **next_action パターン**: 全ツールのレスポンスに次の操作指示を含め、LLMを迷子にさせない

## アーキテクチャ

```
mcp-server/
├── src/
│   ├── core/                          # 再利用可能な基盤（next_action パターン）
│   │   ├── models/
│   │   │   ├── next_action_response.py  # NextActionResponse
│   │   │   ├── workflow_item.py         # WorkflowItem / ItemStatus
│   │   │   └── utils.py                 # generate_id
│   │   ├── next_action_base.py          # NextActionBase
│   │   ├── workflow.py                  # WorkflowBase
│   │   └── json_storage.py             # JsonStorage
│   ├── tools/                         # ドメイン固有の実装
│   │   ├── pipelines.py               # create_pipeline
│   │   ├── tasks.py                   # start_task, complete_task
│   │   └── status.py                  # get_status
│   ├── main.py                        # MCP サーバーのエントリポイント
│   └── storage.py                     # JsonStorage のアプリ固有ラッパー
└── tests/
    ├── conftest.py
    ├── test_pipelines.py
    ├── test_tasks.py
    └── test_status.py
```

## core — 再利用可能な基盤

`src/core/` は next_action パターンの実装基盤です。  
mcp-pipeline のドメインロジックに依存せず、**別の MCP サーバーにそのまま持ち込んで使えます**。

### クラス構成

| クラス | ファイル | 役割 |
|--------|---------|------|
| `NextActionResponse` | `models/next_action_response.py` | `next_action` の存在を型で保証するレスポンスモデル |
| `WorkflowItem` | `models/workflow_item.py` | id・order・title・status・timestamps を持つアイテム基本モデル |
| `ItemStatus` | `models/workflow_item.py` | `pending` / `in_progress` / `completed` の状態列挙型 |
| `generate_id` | `models/utils.py` | プレフィックス付きユニークID生成（例: `"task-3f2a1b4c"`） |
| `NextActionBase` | `next_action_base.py` | `_ok` / `_error` / `_done` の3パターンでレスポンスを統一する基底クラス |
| `WorkflowBase` | `workflow.py` | `_start_item` / `_complete_item` でアイテムのライフサイクルを管理する基底クラス |
| `JsonStorage` | `json_storage.py` | JSON ファイルへの読み書きを提供するシンプルなストレージ |

### next_action パターン

すべてのツールレスポンスに `next_action` フィールドを含めることで、LLM が次に呼ぶべきツールを迷わず判断できます。

```python
# _ok  : 正常レスポンス（続きがある）
# _error: エラーレスポンス（復帰手順を伝える）
# _done : 完了レスポンス（タスクを終えた）

class MyTools(WorkflowBase):
    def my_tool(self, ...):
        target, error = self._start_item(items, order)
        if error:
            return self._error(error, "get_status で確認してください")
        return self._ok({"result": ...}, "next_tool を呼んでください")
```

### 新しい MCP サーバーを作る

`WorkflowBase` を継承するだけで next_action パターンとアイテムライフサイクルが使えます。

```python
from src.core import WorkflowBase, JsonStorage, generate_id, ItemStatus

storage = JsonStorage("my_data.json", "sessions")

class MyWorkflowTools(WorkflowBase):

    def create_session(self, name: str, steps: list) -> dict:
        session_id = generate_id("session")
        # ... ストレージに保存 ...
        return self._ok(
            {"session_id": session_id},
            f"start_step(session_id='{session_id}', order=1) を呼んでください"
        )

    def start_step(self, session_id: str, order: int) -> dict:
        data = storage.load()
        items = data["sessions"][session_id]["steps"]
        target, error = self._start_item(items, order)
        if error:
            return self._error(error, "get_status で確認してください")
        storage.save(data)
        return self._ok({"content": target["content"]}, "完了したら complete_step を呼んでください")
```

## インストール

### 必要条件

- Python 3.10 以上

### クイックスタート

```bash
# リポジトリをクローン
git clone https://github.com/edamanu418/mcp-pipeline.git
cd mcp-pipeline/mcp-server

# 仮想環境を作成して依存関係をインストール
python -m venv .venv
.venv/Scripts/pip install -e .        # Windows
# .venv/bin/pip install -e .          # macOS / Linux

# サーバーを起動（動作確認用）
.venv/Scripts/python -m src.main      # Windows
# .venv/bin/python -m src.main        # macOS / Linux
```

### Claude Desktop での設定

`claude_desktop_config.json` に以下を追加してください:

**Windows** (`%APPDATA%\Claude\claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "mcp-pipeline": {
      "command": "C:\\path\\to\\mcp-pipeline\\mcp-server\\.venv\\Scripts\\python.exe",
      "args": ["-m", "src.main"],
      "env": {
        "PYTHONPATH": "C:\\path\\to\\mcp-pipeline\\mcp-server"
      }
    }
  }
}
```

**macOS / Linux** (`~/Library/Application Support/Claude/claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "mcp-pipeline": {
      "command": "/path/to/mcp-pipeline/mcp-server/.venv/bin/python",
      "args": ["-m", "src.main"],
      "env": {
        "PYTHONPATH": "/path/to/mcp-pipeline/mcp-server"
      }
    }
  }
}
```

> Claude Desktop は `cwd` を無視するため、`PYTHONPATH` で `src` パッケージのパスを明示してください。

## ツール一覧

| ツール | シグネチャ | 役割 |
|--------|-----------|------|
| `create_pipeline` | `(name, tasks, description="")` | パイプラインと全タスクを一括登録 |
| `start_task` | `(pipeline_id, task_order)` | 指定タスクを開始し、prompt と進捗を返す |
| `complete_task` | `(pipeline_id, task_id, output="")` | タスクを完了にし、実行結果を記録 |
| `get_status` | `(pipeline_id="")` | 進捗確認（全一覧 or 特定パイプラインの詳細） |

各ツールのレスポンスには `next_action` フィールドが含まれており、LLM が次に何を呼ぶべきかを明示します。

## 使い方

Claude Desktop（または MCP 対応クライアント）に以下のように伝えるだけでパイプラインが起動します。

```
mcp-pipelineを使って以下を実行してください。

【パイプライン名】
カフェのコンセプト考案

【タスク一覧】
1. コンセプト案を3つ考える
   - 独自性のあるカフェのコンセプトを3つ、各2〜3行で提案してください

2. ベストを1つ選んで深掘りする
   - タスク1の3案から最も独自性の高いものを選び、ターゲット・内装・メニューの方向性を説明してください

3. キャッチコピーを作る
   - タスク2で選んだコンセプトに合うキャッチコピーを3案作ってください
```

## デモ

上記プロンプトの実際の実行結果です。

---

**► create_pipeline**

3タスクを登録し、概要を表示。

```
📋 カフェのコンセプト考案（全3タスク）を登録しました。順番に実行していきます！
```

---

**► start_task（タスク1）→ complete_task**

```
💡 コンセプト3案

案A｜「余白カフェ」
何も予定のない時間を"贅沢"として提供するカフェ。Wi-Fiなし・BGMなし・会話禁止
エリアあり。スマホから離れて「ただ存在する」ことを楽しむための空間。

案B｜「発酵カフェ」
コーヒー・紅茶・食べ物すべてに発酵のプロセスを取り入れたカフェ。コンブチャ・ケ
フィア・塩麴スイーツなど、腸活・健康志向の客層に刺さるメニューが特徴。

案C｜「台本カフェ」
来店時に"その日の役"が書かれた台本を渡され、見知らぬ客同士がゆるく即興劇を楽し
めるカフェ。会話のきっかけをデザインした、孤独解消×エンタメ体験型の空間。
```

---

**► start_task（タスク2）→ complete_task** ← タスク1の output を自動参照

```
🏆 選出：案C「台本カフェ」
理由：体験そのものが商品になっており、他に類を見ない唯一無二性があるため。

👥 ターゲット顧客
20〜35歳の「一人でも入れるが誰かとつながりたい」層。会社や友人グループ以外の
ゆるいコミュニティを求めている人、演劇・ゲームが好きな人、ひとり旅中の旅行者など。

🪑 内装の方向性
昭和初期の喫茶店を思わせる小劇場風の内装。赤いビロードのソファ、木製の仕切り、
薄暗い間接照明。各席に「舞台」を演出する小道具（手紙・地図・小物など）が置かれる。

☕ メニューの方向性
登場人物の名前を冠したドリンクで統一。「探偵ブラック（深煎りコーヒー）」
「令嬢のアフタヌーンティー（紅茶セット）」「旅人のスパイスチャイ」など。
```

---

**► start_task（タスク3）→ complete_task** ← タスク2の output を自動参照

```
✍️ キャッチコピー3案

案①「今日だけ、あなたは別の誰かになれる。」
  → "非日常への扉"を開く言葉。日常に疲れた人の心に刺さるコピー。

案②「見知らぬあなたと、同じ台本を読んでいた。」
  → 偶然の出会いと共有体験の"不思議さ"を詩的に表現。SNS拡散を意識した一文。

案③「コーヒー一杯で、物語が始まる。」
  → シンプルで覚えやすく、看板・ロゴ・SNSにも使いやすい汎用性の高いコピー。
```

---

```
🎉 パイプライン「カフェのコンセプト考案」、全3タスク完了！
```

ポイントは **タスク2がタスク1の3案を、タスク3がタスク2の選出結果を自動で参照している** ことです。  
タスクの `prompt` を変えるだけで、あらゆるワークフローに応用できます。

## ユースケース

| 用途 | タスク例 |
|------|---------|
| **コード生成** | 要件整理 → 設計 → 実装 → テスト作成 |
| **文章作成** | リサーチ → アウトライン → 執筆 → 校正 |
| **コードレビュー** | 動作確認 → セキュリティ → パフォーマンス → 改善提案 |
| **議事録処理** | 整理 → アクション抽出 → 担当割り振り → メール文面作成 |
| **他MCP連携** | Filesystem で読み込み → 分析 → GitHub に結果投稿 |

> mcp-pipeline は **制御層** です。  
> 「何ができるか」は他の MCP サーバーが担い、「何をどの順番でやるか」を mcp-pipeline が強制します。

## 開発

```bash
cd mcp-server

# 開発用依存関係をインストール
pip install -e ".[dev]"

# テストの実行
pytest tests/ -v

# リント
ruff check src/

# 型チェック
mypy src/
```

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。詳細は [LICENSE](LICENSE) をご覧ください。

## 謝辞

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP](https://github.com/jlowin/fastmcp)
