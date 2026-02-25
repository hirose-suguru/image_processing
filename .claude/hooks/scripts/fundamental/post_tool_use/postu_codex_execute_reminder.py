#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
postu_codex_execute_reminder.py
WebSearchやContext7使用後にcodex-executeスキルの使用を促すリマインダー
"""
import sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import debug_log, log_hook_execution, get_tool_data_from_stdin, log_hook_error

except ImportError as e:
    error_msg = f"Failed to import hook_utils: {e}"
    print(f"[HOOK ERROR] {error_msg}")
    print(f"[HOOK ERROR] Script: {__file__}")
    print(f"[HOOK ERROR] sys.path: {sys.path}")
    sys.stderr.write(f"[HOOK ERROR] {error_msg}\n")
    sys.stderr.write(f"[HOOK ERROR] Script: {__file__}\n")
    sys.exit(1)

# 対象となるツール名のリスト
TARGET_TOOLS = [
    "WebSearch",
    "mcp__context7__resolve-library-id",
    "mcp__context7__query-docs",
]


def show_reminder(tool_name: str):
    """codex-executeスキル使用を促すリマインダーを表示"""
    if tool_name == "WebSearch":
        tool_type = "Web検索"
    elif tool_name.startswith("mcp__context7__"):
        tool_type = "context7 MCP"
    else:
        tool_type = tool_name

    message = f"[Reminder] {tool_type}はcodex-executeスキルで実行できます。次回からは `/codex-execute` の使用を検討してください。"
    print(f"\n{message}")
    debug_log(f"Codex-execute reminder displayed for {tool_name}")


def execute(hook_data: dict):
    """
    ロジックの本体

    Args:
        hook_data: フックデータ（tool_name, tool_input等）
    """
    try:
        log_hook_execution()
        debug_log("started.")

        tool_name = hook_data.get("tool_name", "")

        if tool_name in TARGET_TOOLS:
            debug_log(f"Target tool detected: {tool_name}")
            show_reminder(tool_name)
        else:
            debug_log(f"Not a target tool: {tool_name}")

        debug_log("finished.")

    except Exception as e:
        error_msg = f"Unexpected error in execute(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise


def main():
    """スタンドアロン実行用"""
    hook_data = get_tool_data_from_stdin()
    if not hook_data:
        debug_log("ツールデータの取得に失敗したため終了")
        return
    execute(hook_data)


if __name__ == "__main__":
    main()
