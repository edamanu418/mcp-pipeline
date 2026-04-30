import uuid


def generate_id(prefix: str) -> str:
    """プレフィックス付きのユニークIDを生成する。

    Args:
        prefix: IDのプレフィックス（例: "pipeline", "task"）
    """
    return f"{prefix}-{uuid.uuid4().hex[:8]}"
