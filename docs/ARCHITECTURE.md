# アーキテクチャガイド

## 概要

mcp-pipeline は [FastMCP](https://github.com/jlowin/fastmcp) を使って構築した
[Model Context Protocol (MCP)](https://modelcontextprotocol.io/) サーバーです。  
LLM が4つのツールを通じてタスクパイプラインを管理し、タスクを1つずつ確実に実行できるようにします。

```
MCP クライアント（Claude Desktop / VS Code）
          │  MCP プロトコル
          ▼
   src/main.py  ──  FastMCP サーバー "mcp-pipeline"
          │
    ┌─────┼──────────────────┐
    │     │                  │
pipelines tasks           status
    │     │                  │
    └─────┴──────────────────┘
          │
     storage.py
          │
   pipeline_data.json  （JSON ファイル）
```

## レイヤー構成

```
mcp-server/src/
├── core/                          # 再利用可能な基盤（ドメイン非依存）
│   ├── models/
│   │   ├── next_action_response.py  # NextActionResponse
│   │   ├── workflow_item.py         # WorkflowItem / ItemStatus
│   │   └── utils.py                 # generate_id
│   ├── next_action_base.py          # NextActionBase
│   ├── workflow.py                  # WorkflowBase
│   └── json_storage.py             # JsonStorage
├── tools/                         # ドメイン固有の実装
│   ├── pipelines.py               # create_pipeline
│   ├── tasks.py                   # start_task, complete_task
│   └── status.py                  # get_status
├── main.py                        # MCP サーバーエントリポイント
└── storage.py                     # JsonStorage のアプリ固有ラッパー
```

## 設計パターン

### next_action によるLLMガイダンス

このサーバーの核となる設計は、**すべてのツール呼び出しが `next_action` を返す**ことで、
LLMを正しいフローへ自動的に誘導する仕組みです。

**目的：**
- LLMが「次に何をするべきか」を自然言語で明示的に受け取る
- 迷子になったり不正な操作をする余地を排除する
- プロンプトの複雑さを大幅に削減する

**具体例：**

| ツール呼び出し | 返される next_action の例 |
|---|---|
| `create_pipeline()` | "パイプライン概要をユーザーに説明してください。準備ができたら `start_task` を呼んでください。" |
| `start_task()` | "prompt に従ってタスクを実行してください。完了したら `complete_task` を呼んでください。" |
| `complete_task()` | "タスクが完了しました。次のタスクがあれば `start_task` を呼んでください。" |
| `get_status()` | "再開するには `start_task` を呼んでください。" |

### output の連鎖

各タスクの `complete_task` に渡した `output` は、次の `start_task` のレスポンスで
`previous_task_output` として自動的に返却されます。

```
complete_task(output="タスク1の結果")
    │
    ▼
start_task(task_order=2)
    │  → previous_task_output: {output: "タスク1の結果"}
    ▼
LLM が前タスクの結果を踏まえてタスク2を実行
```

これにより、LLM に前後の文脈を明示的に引き渡し、一貫性のある実行を実現します。

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

### レスポンスの3パターン

```python
class NextActionBase:
    def _ok(self, data: dict, next_action: str) -> dict:
        """正常レスポンス（続きがある）"""

    def _error(self, error: str, next_action: str) -> dict:
        """エラーレスポンス（復帰手順を伝える）"""

    def _done(self, data: dict, next_action: str) -> dict:
        """完了レスポンス（タスクを終えた）"""
```

## 各レイヤーの説明

### MCP サーバー（`src/main.py`）

- `FastMCP` を `name` と `instructions` とともに初期化する
- 4つのツールをツール説明（`description`）とともに登録する
- 各ツール関数は `tools/` パッケージへの薄いラッパー

### ツール（`src/tools/`）

各ファイルが1つの論理ドメインを担当します。

| ファイル | 責務 |
|---------|------|
| `pipelines.py` | パイプラインとすべてのタスクを1回の呼び出しで一括登録 |
| `tasks.py` | タスクの開始（`in_progress`）と完了（`completed`）、output の記録と引き継ぎ |
| `status.py` | 特定パイプラインの進捗確認、または全パイプラインの一覧取得 |

### ストレージ（`src/storage.py`）

単一の JSON ファイル（`pipeline_data.json`）に対する最小限の読み書き層として実装しています。  
外部依存が不要でセットアップが簡潔なため、実験・開発フェーズに適しています。

#### スキーマ構造

```json
{
  "pipelines": {
    "<pipeline_id>": {
      "pipeline_id": "pipeline-abc123",
      "name": "パイプライン名",
      "description": "説明",
      "created_at": "ISO-8601",
      "tasks": {
        "<task_id>": {
          "task_id": "task-def456",
          "order": 1,
          "title": "タスクタイトル",
          "prompt": "このタスクで実行すべき指示",
          "status": "pending | in_progress | completed",
          "output": "実行結果 | null",
          "started_at": "ISO-8601 | null",
          "completed_at": "ISO-8601 | null"
        }
      }
    }
  }
}
```

## ツール呼び出しフロー

### 新規パイプラインの実行

```
ユーザー: "以下のタスクを順番に実行して"
  │
  ▼
LLM が create_pipeline(name, tasks) を呼び出す
  │  → pipeline_id + tasks_summary + next_action を返す
  ▼
LLM がパイプラインの全体像をユーザーに説明する
  │
  ▼
LLM が start_task(pipeline_id, task_order=1) を呼び出す
  │  → prompt + next_action を返す
  ▼
LLM が prompt に従ってタスクを実行する
  │
  ▼
LLM が complete_task(pipeline_id, task_id, output=...) を呼び出す
  │  → next_task + next_action を返す
  ▼
（all_completed=true になるまで start_task / complete_task を繰り返す）
```

### 既存パイプラインの再開

```
ユーザー: "続きから"
  │
  ▼
LLM が get_status() を呼び出す          ← 引数なし：全パイプラインの一覧を取得
  │  → パイプライン一覧を返す
  ▼
LLM が get_status(pipeline_id=...) を呼び出す  ← 特定パイプラインの詳細を取得
  │  → 現在のタスク状態を返す
  ▼
LLM が start_task(pipeline_id, task_order=...) を呼び出す
```

## 設計上の判断

### なぜタスクを一括登録するのか

LLM に `add_task` を複数回呼ばせるとトークンを無駄に消費し、レイテンシも増加します。  
`create_pipeline` を1回呼ぶだけで全タスクをアトミックに登録できるため、シンプルかつ高速です。

### なぜすべてのレスポンスに `next_action` を含めるのか

LLM に複雑なマルチステップの順序を指示するのは難しく、エラーが起きやすいです。  
サーバーが `next_action` を通じて明示的に何をすべきかを制御することで、
ステートマシンとして動作し、ツールの誤った順序での呼び出しを防ぎます。

### なぜ JSON ファイルストレージなのか

実験・開発フェーズでは、シンプルさを優先して JSON ファイルを採用しています。  
外部依存（データベースなど）が不要でセットアップが簡潔です。  
将来的に本番環境対応が必要になった場合は、`storage.py` を置き換えるだけで済みます。
