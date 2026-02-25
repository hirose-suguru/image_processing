#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
postu_fix_hook_utils.py
Edit実行後にhook_utilsの間違った関数呼び出しを検出・自動修正
"""
import sys
from pathlib import Path
import re

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import log_hook_execution, debug_log, log_hook_error

except ImportError as e:
    error_msg = f"Failed to import hook_utils: {e}"
    # stdoutとstderrに出力のみ（ファイル書き込みはしない）
    print(f"[HOOK ERROR] {error_msg}")
    print(f"[HOOK ERROR] Script: {__file__}")
    print(f"[HOOK ERROR] sys.path: {sys.path}")
    sys.stderr.write(f"[HOOK ERROR] {error_msg}\n")
    sys.stderr.write(f"[HOOK ERROR] Script: {__file__}\n")
    sys.exit(1)

# 正しい関数名 → ありそうな間違いのリスト
CORRECT_TO_WRONG = {
    "get_project_root": [
        "get_project_dir",
        "get_project_directory",
        "get_root_dir",
        "get_root_directory",
        "project_root",
    ],
    "get_obsidian_config": [
        "get_obs_config",
        "get_obsidian_conf",
    ],
    "get_obsidian_path": [
        "get_obs_path",
        "obsidian_path",
    ],
    "log_hook_execution": [
        "log_execution",
        "hook_log",
        "log_hook",
    ],
    "debug_log": [
        "write_debug",
        "log_debug",
        "debug_write",
    ],
    "get_counter": [
        "get_count",
        "counter",
    ],
    "increment_counter": [
        "inc_counter",
        "incr_counter",
    ],
    "get_user_message_from_stdin": [
        "user_message_from_stdin",
        "get_user_prompt",
        "get_stdin_message",
        "get_user_message",
    ],
    "detect_keywords": [
        "check_keywords",
        "find_keywords",
    ],
    "detect_trigger": [
        "check_trigger",
        "find_trigger",
    ],
    "get_tool_data_from_stdin": [
        "tool_data_from_stdin",
        "get_stdin_data",
        "get_tool_data",
    ],
    "get_path_from_config": [
        "get_path",
        "config_path",
        "get_config_path",
    ],
    "set_hook_toggle": [
        "set_hook_enabled",
        "set_enabled",
        "enable_hook",
        "toggle_hook",
    ],
    "get_hook_toggle": [
        "get_hook_enabled",
        "get_enabled",
        "hook_toggle",
    ],
}

# 逆引き辞書を生成（間違い → 正しい）
WRONG_TO_CORRECT = {}
for correct, wrongs in CORRECT_TO_WRONG.items():
    for wrong in wrongs:
        WRONG_TO_CORRECT[wrong] = correct


def fix_incorrect_calls(file_path: str) -> list:
    """
    ファイル内の間違った関数呼び出しを検出し、自動修正する

    Args:
        file_path: チェック対象ファイルのパス

    Returns:
        修正された間違いのリスト [(行番号, 間違った関数名, 正しい関数名)]
    """
    fixes = []

    try:
        path = Path(file_path)
        if not path.exists():
            debug_log(f"File not found: {file_path}")
            return fixes

        # Pythonファイルのみチェック
        if path.suffix != ".py":
            debug_log(f"Not a Python file: {file_path}")
            return fixes

        # このファイル自体は除外（自己修正を防ぐ）
        if path.name == "postu_fix_hook_utils.py":
            debug_log("Skipping self (postu_fix_hook_utils.py)")
            return fixes

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        lines = content.splitlines()

        # 各間違いを検出して修正
        for wrong_name, correct_name in WRONG_TO_CORRECT.items():
            # 関数呼び出しパターン: wrong_name( （空白を含む場合も対応）
            call_pattern = rf'\b{re.escape(wrong_name)}\s*\('
            # importパターン: from hook_utils import ... wrong_name
            import_pattern = rf'(from\s+hook_utils\s+import\s+[^)]*)\b{re.escape(wrong_name)}\b'

            # 行ごとにチェックして修正箇所を記録
            for i, line in enumerate(lines, 1):
                if re.search(call_pattern, line) or re.search(import_pattern, line):
                    fixes.append((i, wrong_name, correct_name))
                    debug_log(f"Line {i}: Fixed '{wrong_name}' → '{correct_name}'")

            # 関数呼び出しの置換（ wrong_name( → correct_name( ）
            content = re.sub(
                rf'\b{re.escape(wrong_name)}(\s*\()',
                rf'{correct_name}\1',
                content
            )
            # importの置換
            content = re.sub(
                rf'(from\s+hook_utils\s+import\s+[^)]*)\b{re.escape(wrong_name)}\b',
                rf'\1{correct_name}',
                content
            )

        # 変更があった場合のみファイルを書き込み
        if content != original_content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            debug_log(f"File updated: {file_path}")

    except Exception as e:
        debug_log(f"Error fixing file: {e}")

    return fixes


def main(hook_data: dict):
    """
    メイン処理：Editツール実行後に間違った関数呼び出しをチェック

    Args:
        hook_data: PostToolUseのフックデータ
    """
    try:
        tool_name = hook_data.get("tool_name", "")
        tool_input = hook_data.get("tool_input", {})

        # Editツールの場合のみ処理
        if tool_name != "Edit":
            debug_log(f"Tool is not Edit ({tool_name}), skipping")
            return

        file_path = tool_input.get("file_path", "")
        if not file_path:
            debug_log("No file_path in tool_input")
            return

        log_hook_execution()

        # 間違った関数呼び出しを自動修正
        fixes = fix_incorrect_calls(file_path)

        if fixes:
            debug_log("started.")
            # 重複を除去
            unique_fixes = list(set(fixes))
            unique_fixes.sort(key=lambda x: x[0])  # 行番号でソート

            print("✅ hook_utils関数名の間違いを自動修正しました:")
            print("")

            for line_num, wrong_name, correct_name in unique_fixes:
                print(f"  行{line_num}: '{wrong_name}' → '{correct_name}'")

            print("")
            print(f"正しい関数名に修正済みです。")
            debug_log(f"Fixed {len(unique_fixes)} incorrect function calls")
        else:
            return

        debug_log("finished.")



    except Exception as e:
        error_msg = f"Unexpected error in main(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise

if __name__ == "__main__":
    # テスト用
    import json
    test_data = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": __file__
        }
    }
    main(test_data)
