from src.tools.pipelines import create_pipeline
from src.tools.tasks import complete_task, start_task
from src.storage import load
from src.core import ItemStatus

SAMPLE_TASKS = [
    {"order": 1, "title": "タスク1", "prompt": "プロンプト1"},
    {"order": 2, "title": "タスク2", "prompt": "プロンプト2"},
]


def test_start_task_success(tmp_store):
    pipeline = create_pipeline("テストパイプライン", SAMPLE_TASKS)
    result = start_task(pipeline["pipeline_id"], 1)

    assert result["order"] == 1
    assert result["title"] == "タスク1"
    assert result["prompt"] == "プロンプト1"
    assert result["progress"]["total"] == 2
    assert "task_id" in result
    assert "next_action" in result


def test_start_task_updates_status(tmp_store):
    pipeline = create_pipeline("テストパイプライン", SAMPLE_TASKS)
    task_result = start_task(pipeline["pipeline_id"], 1)

    data = load()
    task = data["pipelines"][pipeline["pipeline_id"]]["tasks"][task_result["task_id"]]
    assert task["status"] == ItemStatus.IN_PROGRESS


def test_start_task_invalid_pipeline_returns_error(tmp_store):
    result = start_task("pipeline-nonexistent", 1)

    assert "error" in result
    assert "next_action" in result


def test_start_task_invalid_order_returns_error(tmp_store):
    pipeline = create_pipeline("テストパイプライン", SAMPLE_TASKS)
    result = start_task(pipeline["pipeline_id"], 99)

    assert "error" in result
    assert "next_action" in result


def test_start_task_includes_previous_output(tmp_store):
    pipeline = create_pipeline("テストパイプライン", SAMPLE_TASKS)
    pipeline_id = pipeline["pipeline_id"]
    task1 = start_task(pipeline_id, 1)
    complete_task(pipeline_id, task1["task_id"], output="タスク1の結果")

    result = start_task(pipeline_id, 2)

    assert "previous_task_output" in result
    assert result["previous_task_output"]["output"] == "タスク1の結果"


def test_start_task_no_previous_output_when_first(tmp_store):
    pipeline = create_pipeline("テストパイプライン", SAMPLE_TASKS)
    result = start_task(pipeline["pipeline_id"], 1)

    assert "previous_task_output" not in result


def test_complete_task_invalid_pipeline_returns_error(tmp_store):
    result = complete_task("pipeline-nonexistent", "task-1")

    assert "error" in result
    assert "next_action" in result


def test_complete_task_invalid_task_id_returns_error(tmp_store):
    pipeline = create_pipeline("テストパイプライン", SAMPLE_TASKS)
    result = complete_task(pipeline["pipeline_id"], "task-nonexistent")

    assert "error" in result
    assert "next_action" in result


def test_complete_task_has_next_task(tmp_store):
    pipeline = create_pipeline("テストパイプライン", SAMPLE_TASKS)
    pipeline_id = pipeline["pipeline_id"]
    task1 = start_task(pipeline_id, 1)
    result = complete_task(pipeline_id, task1["task_id"])

    assert result["all_completed"] is False
    assert result["next_task"]["order"] == 2
    assert result["progress"]["completed"] == 1


def test_complete_task_all_done(tmp_store):
    pipeline = create_pipeline("テストパイプライン", SAMPLE_TASKS)
    pipeline_id = pipeline["pipeline_id"]
    task1 = start_task(pipeline_id, 1)
    complete_task(pipeline_id, task1["task_id"])
    task2 = start_task(pipeline_id, 2)
    result = complete_task(pipeline_id, task2["task_id"])

    assert result["all_completed"] is True
    assert result["next_task"] is None
    assert result["progress"]["percent"] == 100


def test_complete_task_stores_output(tmp_store):
    pipeline = create_pipeline("テストパイプライン", SAMPLE_TASKS)
    pipeline_id = pipeline["pipeline_id"]
    task1 = start_task(pipeline_id, 1)
    complete_task(pipeline_id, task1["task_id"], output="生成された成果物")

    data = load()
    task = data["pipelines"][pipeline_id]["tasks"][task1["task_id"]]
    assert task["output"] == "生成された成果物"
