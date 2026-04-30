# API リファレンス

mcp-pipeline は MCP プロトコル経由で4つのツールを公開しています。  
すべてのツールのレスポンスには、LLM が次に何をすべきかを示す `next_action` フィールドが含まれます。

---

## `create_pipeline`

パイプラインとすべてのタスクを1回の呼び出しで一括登録します。

### パラメーター

| 名前 | 型 | 必須 | 説明 |
|-----|---|------|------|
| `name` | `string` | Yes | パイプラインの名前（例: `"設計→コード生成フロー"`） |
| `tasks` | `list[dict]` | Yes | タスクオブジェクトの順序付きリスト（下記参照） |
| `description` | `string` | No | パイプラインの説明（省略可） |

**タスクオブジェクトのフィールド:**

| フィールド | 型 | 説明 |
|----------|---|------|
| `order` | `int` | タスク番号（1始まり） |
| `title` | `string` | 短い表示タイトル（例: `"設計書作成"`） |
| `prompt` | `string` | このタスクで LLM が実行すべき具体的な指示 |

### レスポンス

```json
{
  "pipeline_id": "pipeline-7e2a1d2a",
  "name": "設計→コード生成フロー",
  "total_tasks": 3,
  "status": "ready",
  "tasks_summary": [
    {"order": 1, "title": "設計書作成"},
    {"order": 2, "title": "コード生成"},
    {"order": 3, "title": "テスト作成"}
  ],
  "next_action": "..."
}
```

### 注意事項

- 同じパイプラインに対してこのツールを呼ぶのは **1回だけ** にしてください。
- レスポンス受信後、`start_task` を呼ぶ前にパイプライン全体像をユーザーに説明してください。

---

## `start_task`

指定したタスクを開始します。タスクのステータスを `in_progress` に更新し、prompt を返します。

### パラメーター

| 名前 | 型 | 必須 | 説明 |
|-----|---|------|------|
| `pipeline_id` | `string` | Yes | `create_pipeline` が返した `pipeline_id` |
| `task_order` | `int` | Yes | 開始するタスクの番号（1始まり） |

### レスポンス

```json
{
  "task_id": "task-31e122e0",
  "order": 1,
  "title": "設計書作成",
  "prompt": "以下の要件をもとに設計書を作成してください...",
  "progress": {
    "current": 1,
    "total": 3,
    "completed": 0,
    "percent": 0
  },
  "next_action": "..."
}
```

タスク2以降では、前タスクの出力が `previous_task_output` として追加されます:

```json
{
  "task_id": "task-a4f3b1c2",
  "order": 2,
  "title": "コード生成",
  "prompt": "...",
  "progress": {"current": 2, "total": 3, "completed": 1, "percent": 33},
  "previous_task_output": {
    "order": 1,
    "title": "設計書作成",
    "output": "タスク1の実行結果テキスト..."
  },
  "next_action": "..."
}
```

### エラーレスポンス

```json
{
  "error": "pipeline_id 'pipeline-xxxx' が見つかりません。",
  "next_action": "get_status を呼んで利用可能なパイプラインを確認してください。"
}
```

### 注意事項

- 返却された `task_id` を保存しておいてください。`complete_task` の呼び出し時に必要です。
- `previous_task_output` が含まれる場合は、前タスクの結果を踏まえてタスクを実行してください。
- `prompt` フィールドの指示に従ってタスクを実行してください。

---

## `complete_task`

タスクを完了にし、実行結果を記録します。次のタスク情報を返します。

### パラメーター

| 名前 | 型 | 必須 | 説明 |
|-----|---|------|------|
| `pipeline_id` | `string` | Yes | パイプライン識別子 |
| `task_id` | `string` | Yes | `start_task` が返した `task_id` |
| `output` | `string` | No | タスクの実行結果（次タスクへ引き継がれる） |

### レスポンス（まだ続きがある場合）

```json
{
  "completed_task": {"order": 1, "title": "設計書作成"},
  "progress": {
    "current": 1,
    "total": 3,
    "completed": 1,
    "percent": 33
  },
  "next_task": {"order": 2, "title": "コード生成"},
  "all_completed": false,
  "next_action": "..."
}
```

### レスポンス（全タスク完了時）

```json
{
  "completed_task": {"order": 3, "title": "テスト作成"},
  "progress": {"current": 3, "total": 3, "completed": 3, "percent": 100},
  "next_task": null,
  "all_completed": true,
  "next_action": "全3タスク完了です！パイプライン「...」が終了しました。"
}
```

### 注意事項

- `output` には生成した設計書・コード・レビュー内容など、タスクの実行結果を渡してください。
- `output` は次のタスクの `previous_task_output` として自動的に引き継がれます。

---

## `get_status`

進捗を取得します。`pipeline_id` を省略すると全パイプラインの一覧、指定すると詳細を返します。

### パラメーター

| 名前 | 型 | 必須 | 説明 |
|-----|---|------|------|
| `pipeline_id` | `string` | No | 省略時は全パイプラインの概要一覧を返す |

### レスポンス — 全パイプライン一覧（`pipeline_id` 省略時）

```json
{
  "pipelines": [
    {
      "pipeline_id": "pipeline-7e2a1d2a",
      "name": "設計→コード生成フロー",
      "progress": "1/3",
      "percent": 33,
      "current_task": "コード生成"
    }
  ],
  "next_action": "..."
}
```

### レスポンス — 特定パイプラインの詳細（`pipeline_id` 指定時）

```json
{
  "pipeline_id": "pipeline-7e2a1d2a",
  "name": "設計→コード生成フロー",
  "description": "要件定義からテストまでの一貫フロー",
  "tasks": [
    {"order": 1, "task_id": "task-31e122e0", "title": "設計書作成", "status": "completed"},
    {"order": 2, "task_id": "task-a4f3b1c2", "title": "コード生成", "status": "in_progress"},
    {"order": 3, "task_id": "task-c66204b8", "title": "テスト作成", "status": "pending"}
  ],
  "progress": {"total": 3, "completed": 1, "percent": 33},
  "next_action": "..."
}
```

### タスクのステータス

| ステータス | 意味 |
|-----------|------|
| `pending` | 未開始 |
| `in_progress` | 実行中 |
| `completed` | 完了 |
