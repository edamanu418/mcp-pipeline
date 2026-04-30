from src.tools.pipelines import create_pipeline
from src.storage import load

SAMPLE_TASKS = [
    {"order": 1, "title": "タスク1", "prompt": "プロンプト1"},
    {"order": 2, "title": "タスク2", "prompt": "プロンプト2"},
]


def test_create_pipeline_returns_expected_fields(tmp_store):
    result = create_pipeline("テストパイプライン", SAMPLE_TASKS)

    assert result["name"] == "テストパイプライン"
    assert result["total_tasks"] == 2
    assert result["status"] == "ready"
    assert "pipeline_id" in result
    assert "next_action" in result


def test_create_pipeline_tasks_summary_is_ordered(tmp_store):
    result = create_pipeline("テストパイプライン", SAMPLE_TASKS)

    orders = [t["order"] for t in result["tasks_summary"]]
    assert orders == sorted(orders)


def test_create_pipeline_persists_to_store(tmp_store):
    result = create_pipeline("テストパイプライン", SAMPLE_TASKS)

    data = load()
    pipeline = data["pipelines"][result["pipeline_id"]]
    assert pipeline["name"] == "テストパイプライン"
    assert len(pipeline["tasks"]) == 2


def test_create_pipeline_with_description(tmp_store):
    result = create_pipeline("テストパイプライン", SAMPLE_TASKS, description="説明文")

    data = load()
    pipeline = data["pipelines"][result["pipeline_id"]]
    assert pipeline["description"] == "説明文"
