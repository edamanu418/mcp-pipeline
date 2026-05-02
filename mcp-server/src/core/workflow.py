from datetime import datetime
from typing import Any

from .models.workflow_item import ItemStatus
from .next_action_base import NextActionBase


class WorkflowBase(NextActionBase):
    """next_action パターン + WorkflowItem ライフサイクル管理の基底クラス。
    _start_item / _complete_item でアイテムの状態遷移を提供する。"""

    def _start_item(self, items: dict[str, Any], order: int) -> dict:
        """アイテムを IN_PROGRESS に更新する。

        Args:
            items: アイテムの辞書（item_id をキーとする）。
            order: 開始するアイテムの順番。

        Returns:
            更新済みアイテム。

        Raises:
            ValueError: 指定した order のアイテムが存在しない場合。
        """
        target = next((i for i in items.values() if i["order"] == order), None)
        if not target:
            raise ValueError(f"order={order} が見つかりません。")

        target["status"] = ItemStatus.IN_PROGRESS
        target["started_at"] = datetime.now().isoformat()
        return target

    def _complete_item(self, items: dict[str, Any], item_id: str) -> tuple[dict, dict | None]:
        """アイテムを COMPLETED に更新し、次の pending アイテムを返す。

        Args:
            items: アイテムの辞書（item_id をキーとする）。
            item_id: 完了させるアイテムのID。

        Returns:
            (current_item, next_item) — next_item は次の pending がなければ None。

        Raises:
            ValueError: 指定した item_id のアイテムが存在しない場合。
        """
        if item_id not in items:
            raise ValueError(f"item_id '{item_id}' が見つかりません。")

        current = items[item_id]
        current["status"] = ItemStatus.COMPLETED
        current["completed_at"] = datetime.now().isoformat()

        next_item = next(
            (
                i
                for i in sorted(items.values(), key=lambda x: x["order"])
                if i["order"] > current["order"] and i["status"] == ItemStatus.PENDING
            ),
            None,
        )

        return current, next_item
