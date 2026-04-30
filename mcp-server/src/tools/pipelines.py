from datetime import datetime
from typing import TypedDict, cast

from ..core import ItemStatus, WorkflowBase
from ..core.models.utils import generate_id
from ..storage import load, save


class TaskInput(TypedDict):
    order: int
    title: str
    prompt: str


class PipelineTools(WorkflowBase):

    def create_pipeline(self, name: str, tasks: list[TaskInput], description: str = "") -> dict:
        data = load()

        pipeline_id = generate_id("pipeline")
        now = datetime.now().isoformat()

        normalized_tasks = {}
        for t in tasks:
            task_id = generate_id("task")
            normalized_tasks[task_id] = {
                "task_id": task_id,
                "order": t["order"],
                "title": t["title"],
                "prompt": t["prompt"],
                "status": ItemStatus.PENDING,
                "output": None,
                "started_at": None,
                "completed_at": None,
            }

        data["pipelines"][pipeline_id] = {
            "pipeline_id": pipeline_id,
            "name": name,
            "description": description,
            "created_at": now,
            "tasks": normalized_tasks,
        }
        save(data)

        total = len(normalized_tasks)

        return self._ok(
            {
                "pipeline_id": pipeline_id,
                "name": name,
                "total_tasks": total,
                "status": "ready",
                "tasks_summary": [
                    {"order": t["order"], "title": t["title"]}
                    for t in sorted(normalized_tasks.values(), key=lambda x: cast(int, x["order"]))
                ],
            },
            f"パイプラインを登録しました！\n"
            f"まず、上記のパイプライン概要（全{total}タスク）をユーザーに説明してください。\n"
            f"ユーザーが準備できたら、start_task(pipeline_id='{pipeline_id}', task_order=1) でタスク1を開始してください。",
        )


_tools = PipelineTools()
create_pipeline = _tools.create_pipeline


TOOL_DESCRIPTION = """
【いつ使うか】
ユーザーが「●●というパイプラインを作成して」「以下のタスクを順番に実行して」と言ったとき、最初に1回だけ呼ぶ。
パイプラインと全タスクをまとめて登録する。

【返却後の処理】
このツールの返却値には pipeline_id, name, total_tasks, tasks_summary が含まれます。
★重要★ 返却後は、この情報をもとにパイプラインの全体像（名前・タスク数・各タスクのタイトル一覧）をユーザーに説明してください。
ユーザーが「開始」と言ったら、その後に start_task を呼んでください。

【パラメータ】
- name: パイプラインの名前（例: "設計→コード生成フロー"）
- description: パイプラインの説明（省略可）
- tasks: タスクのリスト。各タスクに order, title, prompt を含める
  - order: タスクの順番（1始まりの整数）
  - title: タスクのタイトル（例: "設計書作成"）
  - prompt: このタスクでLLMが実行すべき指示内容（具体的なプロンプト）
"""
