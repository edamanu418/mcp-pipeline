import pytest
from unittest.mock import patch
import src.storage as storage


@pytest.fixture
def tmp_store(tmp_path):
    """DATA_FILE をテスト用の一時ファイルに差し替える。テスト終了後は自動削除される。"""
    with patch.object(storage, "DATA_FILE", tmp_path / "pipeline_test_data.json"):
        yield
