from ..core import ItemStatus, WorkflowBase
from ..storage import load, save


class TaskTools(WorkflowBase):

    def start_task(self, pipeline_id: str, task_order: int) -> dict:
        data = load()

        if pipeline_id not in data["pipelines"]:
            return self._error(
                f"pipeline_id '{pipeline_id}' が見つかりません。",
                "get_status を呼んで利用可能なパイプラインを確認してください。",
            )

        pipeline = data["pipelines"][pipeline_id]
        tasks = pipeline["tasks"]

        target, error = self._start_item(tasks, task_order)
        if error:
            return self._error(error, f"get_status(pipeline_id='{pipeline_id}') で正しい task_order を確認してください。")
        assert target is not None

        save(data)

        total = len(tasks)
        completed = sum(1 for t in tasks.values() if t["status"] == ItemStatus.COMPLETED)

        prev_task = next(
            (t for t in sorted(tasks.values(), key=lambda x: x["order"]) if t["order"] == task_order - 1),
            None,
        )

        response_data: dict = {
            "task_id": target["task_id"],
            "order": target["order"],
            "title": target["title"],
            "prompt": target["prompt"],
            "progress": {
                "current": task_order,
                "total": total,
                "completed": completed,
                "percent": int(completed / total * 100),
            },
        }

        if prev_task and prev_task.get("output"):
            response_data["previous_task_output"] = {
                "order": prev_task["order"],
                "title": prev_task["title"],
                "output": prev_task["output"],
            }

        return self._ok(
            response_data,
            f"上記の prompt に従ってタスク{task_order}「{target['title']}」を実行してください。\n"
            f"完了したら complete_task(pipeline_id='{pipeline_id}', task_id='{target['task_id']}', output=...) "
            f"を呼んでください。output には実行結果を文字列で渡してください。",
        )

    def complete_task(self, pipeline_id: str, task_id: str, output: str = "") -> dict:
        data = load()

        if pipeline_id not in data["pipelines"]:
            return self._error(
                f"pipeline_id '{pipeline_id}' が見つかりません。",
                "get_status を呼んで利用可能なパイプラインを確認してください。",
            )

        pipeline = data["pipelines"][pipeline_id]
        tasks = pipeline["tasks"]

        current_task, next_task, error = self._complete_item(tasks, task_id)
        if error:
            return self._error(error, f"get_status(pipeline_id='{pipeline_id}') で正しい task_id を確認してください。")
        assert current_task is not None

        current_task["output"] = output
        save(data)

        total = len(tasks)
        completed = sum(1 for t in tasks.values() if t["status"] == ItemStatus.COMPLETED)
        all_done = completed == total

        if all_done:
            return self._done(
                {
                    "completed_task": {"order": current_task["order"], "title": current_task["title"]},
                    "progress": {"current": current_task["order"], "total": total, "completed": completed, "percent": 100},
                    "next_task": None,
                    "all_completed": True,
                },
                f"全{total}タスク完了です！パイプライン「{pipeline['name']}」が終了しました。ユーザーに完了を報告してください。",
            )

        assert next_task is not None
        return self._done(
            {
                "completed_task": {"order": current_task["order"], "title": current_task["title"]},
                "progress": {
                    "current": current_task["order"],
                    "total": total,
                    "completed": completed,
                    "percent": int(completed / total * 100),
                },
                "next_task": {"order": next_task["order"], "title": next_task["title"]},
                "all_completed": False,
            },
            f"タスク{current_task['order']}が完了しました（{completed}/{total}）。\n"
            f"続けるには start_task(pipeline_id='{pipeline_id}', task_order={next_task['order']}) を呼んでください。",
        )


_tools = TaskTools()
start_task = _tools.start_task
complete_task = _tools.complete_task


START_TASK_DESCRIPTION = """
【いつ使うか】
- ユーザーが「パイプライン開始」「次のタスクへ」と言ったとき
- complete_task の next_action に従って次のタスクを開始するとき

【LLMへの指示】
- pipeline_id: create_pipeline で返却された pipeline_id
- task_order: 開始するタスクの順番（1始まりの整数）
- 返却された prompt に従ってタスクを実行すること
- previous_task_output が含まれている場合は、前タスクの結果を踏まえてタスクを実行すること
"""

COMPLETE_TASK_DESCRIPTION = """
【いつ使うか】
- タスクの実行が完了したとき
- ユーザーが「次へ」「完了」と言ったとき

【LLMへの指示】
- pipeline_id: 対象のパイプラインID
- task_id: 完了させるタスクのID（start_task のレスポンスに含まれる task_id を使うこと）
- output: タスクの実行結果（生成した設計書・コード・レビュー内容など）を文字列で渡すこと
"""
