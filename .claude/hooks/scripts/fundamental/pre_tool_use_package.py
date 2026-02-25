#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pre_tool_use_package.py
PreToolUse hookで実行される全スクリプトを統合実行
"""
import sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import log_hook_execution, debug_log, log_hook_error, get_tool_data_from_stdin

except ImportError as e:
    error_msg = f"Failed to import hook_utils: {e}"
    # stdoutとstderrに出力のみ（ファイル書き込みはしない）
    print(f"[HOOK ERROR] {error_msg}")
    print(f"[HOOK ERROR] Script: {__file__}")
    print(f"[HOOK ERROR] sys.path: {sys.path}")
    sys.stderr.write(f"[HOOK ERROR] {error_msg}\n")
    sys.stderr.write(f"[HOOK ERROR] Script: {__file__}\n")
    sys.exit(1)

def main():
    """PreToolUseの全処理を実行"""
    try:
        log_hook_execution()
        #debug_log("started.")

        # stdinを1回だけ読み取り、各モジュールに渡す
        tool_data = get_tool_data_from_stdin()
        tool_name = tool_data.get('tool_name', 'unknown')
        debug_log(f"Tool data received: {tool_name}")

        sys.path.insert(0, str(Path(__file__).parent))

        # === 共通hook（全ツール対象） ===
        from pre_tool_use import pre_tool_block
        pre_tool_block.execute(tool_data)

        # === ツール別hook ===
        if tool_name == "Bash":
            debug_log("Starting Bash-specific hooks...")
            from pre_tool_use import pre_mkdir_verify
            pre_mkdir_verify.execute(tool_data)

        elif tool_name == "Read":
            debug_log("Starting Read-specific hooks...")
            from pre_tool_use import pretu_large_file_structure
            pretu_large_file_structure.execute(tool_data)

        # 他のツール用hookはここに追加

        #debug_log("finished.")


    except Exception as e:
        error_msg = f"Unexpected error in main(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise

if __name__ == "__main__":
    main()
