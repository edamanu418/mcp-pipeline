import json
from pathlib import Path
from typing import Any


class JsonStorage:
    """JSON ファイルベースのシンプルなストレージ。

    Attributes:
        file_path: 保存先のファイルパス。
        root_key: データのルートキー（例: "pipelines", "plans"）。
    """

    def __init__(self, file_path: Path | str, root_key: str) -> None:
        self.file_path = Path(file_path)
        self._root_key = root_key

    def load(self) -> dict[str, Any]:
        """JSONファイルからデータを読み込む。ファイルが存在しない場合は空のデータを返す。"""
        if self.file_path.exists():
            return json.loads(self.file_path.read_text(encoding="utf-8"))
        return {self._root_key: {}}

    def save(self, data: dict[str, Any]) -> None:
        """データをJSONファイルに保存する。"""
        self.file_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
