# 変更履歴

このプロジェクトのすべての重要な変更はこのファイルに記録されます。

フォーマットは [Keep a Changelog](https://keepachangelog.com/ja/1.0.0/) に基づき、
バージョン管理は [セマンティック バージョニング](https://semver.org/lang/ja/) に従います。

## [未リリース]

## [0.1.0] - 2026-04-30

### 追加
- 初回リリース
- `create_pipeline` — パイプラインと全タスクを一括登録
- `start_task` — 指定タスクを開始し prompt と前タスク output を返す
- `complete_task` — タスクを完了にし実行結果を記録
- `get_status` — パイプラインの進捗確認（全一覧 / 特定詳細）
- `core/` — next_action パターン・WorkflowBase・JsonStorage の再利用可能基盤

[未リリース]: https://github.com/edamanu418/mcp-pipeline/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/edamanu418/mcp-pipeline/releases/tag/v0.1.0
