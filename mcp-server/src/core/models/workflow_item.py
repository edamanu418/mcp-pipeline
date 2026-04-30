from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ItemStatus(str, Enum):
    """ワークフローアイテムの進捗状態。"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class WorkflowItem:
    """順序付き作業アイテムの基本モデル。
    Task（mcp-pipeline）や Step（Miyagi）の共通基盤。

    Attributes:
        item_id: アイテムの一意なID。
        order: 実行順序（1始まり）。
        title: アイテムのタイトル。
        status: 現在の進捗状態。
        created_at: 作成日時（ISO形式）。
        started_at: 開始日時（ISO形式）。未開始の場合は None。
        completed_at: 完了日時（ISO形式）。未完了の場合は None。
    """

    item_id: str
    order: int
    title: str
    status: ItemStatus = ItemStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: str | None = None
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "order": self.order,
            "title": self.title,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }
