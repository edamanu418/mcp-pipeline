from dataclasses import dataclass, field
from typing import Any


@dataclass
class NextActionResponse:
    """next_action パターンの基本モデル。
    next_action の存在を保証しつつ、任意のデータを保持する。

    Attributes:
        next_action: LLM への次の操作指示。必ず存在することが保証される。
        data: レスポンスに含める任意のドメインデータ。
        error: エラー内容。エラー時のみ設定する。
    """

    next_action: str
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {**self.data, "next_action": self.next_action}
        if self.error:
            result["error"] = self.error
        return result
