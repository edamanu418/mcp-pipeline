"""
mcp-pipeline
============
タスクを一つずつ確実に順番に実行するMCPサーバー。
next_action パターンでLLMをガイドし、パイプラインの各タスクを確実に実行する。
"""

from fastmcp import FastMCP

from .tools import (
    COMPLETE_TASK_DESCRIPTION,
    PIPELINE_TOOL_DESCRIPTION,
    START_TASK_DESCRIPTION,
    STATUS_TOOL_DESCRIPTION,
    complete_task as _complete_task,
    create_pipeline as _create_pipeline,
    get_status as _get_status,
    start_task as _start_task,
)
from .tools.pipelines import TaskInput

mcp = FastMCP(
    name="mcp-pipeline",
    instructions="""
あなたはタスクパイプラインを管理するサーバです。
ユーザーが「以下のタスクを順番に実行して」「●●というパイプラインを作って」と言ったら、以下の流れで動作してください:

【新規パイプラインの場合】
1. LLMがタスク一覧を設計する（ユーザー指示から title と prompt を作成）
2. create_pipeline でパイプラインと全タスクを一括登録する
3. 返却されたパイプライン情報をもとに、タスク一覧をユーザーに説明する
4. ユーザーが準備できたら、start_task でタスク1を開始し、prompt に従って実行する
5. タスク実行後は complete_task でタスクを完了にし、output に実行結果を渡す
6. 4〜5を全タスク完了まで繰り返す

【既存パイプラインを続ける場合】
- get_status でパイプラインの進捗を確認する
- 中断していたタスクから start_task で再開する

重要: 全ツールのレスポンスに next_action が含まれます。必ずその指示に従ってください。
start_task を呼ぶ前に必ずパイプラインの概要をユーザーに説明してください。
previous_task_output が含まれている場合は、前タスクの結果を踏まえてタスクを実行してください。
""",
)


@mcp.tool(description=PIPELINE_TOOL_DESCRIPTION)
def create_pipeline(name: str, tasks: list[TaskInput], description: str = "") -> dict:
    """パイプラインと全タスクを一括登録する"""
    return _create_pipeline(name, tasks, description)


@mcp.tool(description=START_TASK_DESCRIPTION)
def start_task(pipeline_id: str, task_order: int) -> dict:
    """指定タスクを開始し、プロンプトと進捗を返す"""
    return _start_task(pipeline_id, task_order)


@mcp.tool(description=COMPLETE_TASK_DESCRIPTION)
def complete_task(pipeline_id: str, task_id: str, output: str = "") -> dict:
    """タスクを完了にし、次のタスク情報を返す"""
    return _complete_task(pipeline_id, task_id, output)


@mcp.tool(description=STATUS_TOOL_DESCRIPTION)
def get_status(pipeline_id: str = "") -> dict:
    """進捗確認。pipeline_id省略で全パイプライン一覧、指定で詳細を返す"""
    return _get_status(pipeline_id)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", default="stdio", choices=["stdio", "http", "sse", "streamable-http"])
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)
