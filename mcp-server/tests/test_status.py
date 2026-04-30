from src.tools.pipelines import create_pipeline
from src.tools.tasks import complete_task, start_task
from src.tools.status import get_status

SAMPLE_TASKS = [
    {"order": 1, "title": "タスク1", "prompt": "プロンプト1"},
    {"order": 2, "title": "タスク2", "prompt": "プロンプト2"},
]


def test_get_status_no_pipelines(tmp_store):
    result = get_status()

    assert result["pipelines"] == []
    assert "next_action" in result


def test_get_status_all_pipelines(tmp_store):
    create_pipeline("パイプライン1", SAMPLE_TASKS)
    create_pipeline("パイプライン2", SAMPLE_TASKS)
    result = get_status()

    assert len(result["pipelines"]) == 2
    assert "next_action" in result


def test_get_status_specific_pipeline(tmp_store):
    pipeline = create_pipeline("テストパイプライン", SAMPLE_TASKS)
    result = get_status(pipeline["pipeline_id"])

    assert result["pipeline_id"] == pipeline["pipeline_id"]
    assert result["name"] == "テストパイプライン"
    assert len(result["tasks"]) == 2
    assert "next_action" in result


def test_get_status_invalid_pipeline_returns_error(tmp_store):
    result = get_status("pipeline-nonexistent")

    assert "error" in result
    assert "next_action" in result


def test_get_status_shows_in_progress_task(tmp_store):
    pipeline = create_pipeline("テストパイプライン", SAMPLE_TASKS)
    pipeline_id = pipeline["pipeline_id"]
    start_task(pipeline_id, 1)

    result = get_status(pipeline_id)
    in_progress = [t for t in result["tasks"] if t["status"] == "in_progress"]
    assert len(in_progress) == 1


def test_get_status_all_completed(tmp_store):
    pipeline = create_pipeline("テストパイプライン", SAMPLE_TASKS)
    pipeline_id = pipeline["pipeline_id"]
    t1 = start_task(pipeline_id, 1)
    complete_task(pipeline_id, t1["task_id"])
    t2 = start_task(pipeline_id, 2)
    complete_task(pipeline_id, t2["task_id"])

    result = get_status(pipeline_id)
    assert result["progress"]["percent"] == 100
