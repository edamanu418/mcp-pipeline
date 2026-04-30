from ..core import ItemStatus, WorkflowBase
from ..storage import load


class StatusTools(WorkflowBase):

    def get_status(self, pipeline_id: str = "") -> dict:
        data = load()

        if not pipeline_id:
            if not data["pipelines"]:
                return self._ok(
                    {"pipelines": []},
                    "まだパイプラインがありません。create_pipeline でパイプラインを作成してください。",
                )

            summaries = []
            for p in data["pipelines"].values():
                tasks = p["tasks"]
                total = len(tasks)
                completed = sum(1 for t in tasks.values() if t["status"] == ItemStatus.COMPLETED)
                in_progress = next(
                    (t for t in tasks.values() if t["status"] == ItemStatus.IN_PROGRESS), None
                )
                summaries.append(
                    {
                        "pipeline_id": p["pipeline_id"],
                        "name": p["name"],
                        "progress": f"{completed}/{total}",
                        "percent": int(completed / total * 100) if total else 0,
                        "current_task": in_progress["title"] if in_progress else None,
                    }
                )

            return self._ok(
                {"pipelines": summaries},
                "再開するには get_status(pipeline_id='...') で詳細を確認し、start_task を呼んでください。",
            )

        if pipeline_id not in data["pipelines"]:
            return self._error(
                f"pipeline_id '{pipeline_id}' が見つかりません。",
                "get_status()（引数なし）で利用可能なパイプラインを確認してください。",
            )

        pipeline = data["pipelines"][pipeline_id]
        tasks = pipeline["tasks"]
        total = len(tasks)
        completed = sum(1 for t in tasks.values() if t["status"] == ItemStatus.COMPLETED)
        in_progress_task = next(
            (t for t in tasks.values() if t["status"] == ItemStatus.IN_PROGRESS), None
        )
        sorted_tasks = sorted(tasks.values(), key=lambda x: x["order"])

        if in_progress_task:
            next_action = (
                f"タスク{in_progress_task['order']}「{in_progress_task['title']}」が進行中です。"
                f"start_task(pipeline_id='{pipeline_id}', task_order={in_progress_task['order']}) で再開してください。"
            )
        elif completed == total:
            next_action = "全タスク完了済みです！"
        else:
            next_pending = next((t for t in sorted_tasks if t["status"] == ItemStatus.PENDING), None)
            next_action = (
                f"start_task(pipeline_id='{pipeline_id}', task_order={next_pending['order']}) でパイプラインを再開してください。"
                if next_pending
                else "次のタスクが見つかりません。"
            )

        return self._ok(
            {
                "pipeline_id": pipeline_id,
                "name": pipeline["name"],
                "description": pipeline.get("description", ""),
                "tasks": [
                    {"order": t["order"], "task_id": t["task_id"], "title": t["title"], "status": t["status"]}
                    for t in sorted_tasks
                ],
                "progress": {
                    "total": total,
                    "completed": completed,
                    "percent": int(completed / total * 100) if total else 0,
                },
            },
            next_action,
        )


_tools = StatusTools()
get_status = _tools.get_status


TOOL_DESCRIPTION = """
【いつ使うか】
- 会話が途切れた後にパイプラインを再開するとき
- ユーザーが「今どこまで進んだ？」「進捗を教えて」と聞いたとき
- どの pipeline_id を使えばいいか分からなくなったとき
- pipeline_id を省略した場合は全パイプラインの一覧を返す

【LLMへの指示】
- pipeline_id を指定すると特定パイプラインの進捗詳細を返す
- 省略すると登録済み全パイプラインの概要一覧を返す
"""
