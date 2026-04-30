from typing import Any

from .models.next_action_response import NextActionResponse


class NextActionBase:
    """next_action パターンを使う MCP ツールの基底クラス。
    _ok / _error / _done の3パターンで全レスポンスを統一する。"""

    def _ok(self, data: dict[str, Any], next_action: str) -> dict[str, Any]:
        """正常レスポンス。データと次アクション指示を返す。

        Args:
            data: レスポンスに含めるドメインデータ。
            next_action: LLM への次の操作指示。
        """
        return NextActionResponse(next_action=next_action, data=data).to_dict()

    def _error(self, message: str, recovery: str) -> dict[str, Any]:
        """エラーレスポンス。エラー内容と復帰手順を返す。

        Args:
            message: エラーの内容。
            recovery: エラーからの復帰手順（次に呼ぶツールなど）。
        """
        return NextActionResponse(next_action=recovery, error=message).to_dict()

    def _done(self, data: dict[str, Any], message: str) -> dict[str, Any]:
        """完了レスポンス。最終データと完了メッセージを返す。

        Args:
            data: レスポンスに含めるドメインデータ。
            message: 完了を伝える LLM へのメッセージ。
        """
        return NextActionResponse(next_action=message, data=data).to_dict()
