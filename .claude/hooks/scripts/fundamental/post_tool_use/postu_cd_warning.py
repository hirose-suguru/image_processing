#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
postu_cd_warning.py
PostToolUse hookでcdコマンドの使用を検出し警告を出力
"""
import sys
import re
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from hook_utils import log_hook_execution, debug_log, log_hook_error, get_tool_data_from_stdin

except ImportError as e:
    error_msg = f"Failed to import hook_utils: {e}"
    print(f"[HOOK ERROR] {error_msg}")
    print(f"[HOOK ERROR] Script: {__file__}")
    print(f"[HOOK ERROR] sys.path: {sys.path}")
    sys.stderr.write(f"[HOOK ERROR] {error_msg}\n")
    sys.stderr.write(f"[HOOK ERROR] Script: {__file__}\n")
    sys.exit(1)


def detect_cd_command(command: str) -> bool:
    """
    コマンド文字列からcdコマンドの使用を検出

    検出パターン:
    - cd /path
    - cd ..
    - cd ~
    - cd /path && other_command
    - cd /path; other_command
    - other_command && cd /path

    Args:
        command: 実行されたコマンド文字列

    Returns:
        cdコマンドが含まれている場合True
    """
    if not command:
        return False

    # cdコマンドを検出する正規表現パターン
    # - 行頭またはセミコロン/&&/||の後にcd
    # - cdの後にスペースまたは行末
    cd_patterns = [
        r'^\s*cd\s',           # 行頭のcd
        r'^\s*cd$',            # cdのみ
        r'&&\s*cd\s',          # && cd
        r'&&\s*cd$',           # && cd（末尾）
        r'\|\|\s*cd\s',        # || cd
        r'\|\|\s*cd$',         # || cd（末尾）
        r';\s*cd\s',           # ; cd
        r';\s*cd$',            # ; cd（末尾）
    ]

    for pattern in cd_patterns:
        if re.search(pattern, command):
            debug_log(f"Detected cd command with pattern: {pattern}")
            return True

    return False


def execute(tool_data: dict):
    """
    cdコマンド検出のロジック本体

    Args:
        tool_data: ツール実行データ
    """
    try:
        log_hook_execution()

        # Bashツールであることを確認
        tool_name = tool_data.get("tool_name", "")
        if tool_name != "Bash":
            debug_log(f"Not a Bash tool ({tool_name}), skipping cd_warning")
            return

        # コマンドを取得
        tool_input = tool_data.get("tool_input", {})
        command = tool_input.get("command", "")

        if not command:
            debug_log("No command found")
            return

        # cdコマンドを検出
        if detect_cd_command(command):
            print("⚠️ cdコマンドは禁止です。hookで毎回project_dirにdirが戻るようになっています。")
            debug_log(f"CD command warning issued for: {command}")

    except Exception as e:
        error_msg = f"Unexpected error in execute(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise


def main():
    """スタンドアロン実行用エントリーポイント"""
    tool_data = get_tool_data_from_stdin()
    if not tool_data:
        debug_log("ツールデータの取得に失敗したため終了")
        return
    execute(tool_data)


if __name__ == "__main__":
    main()
