#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
post_tool_use_package.py
PostToolUse hookで実行される全スクリプトを統合実行
"""
import sys
from pathlib import Path
import json

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import log_hook_execution, debug_log, log_hook_error, log_python_env

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
    """PostToolUseの全処理を順次実行"""
    try:
        log_hook_execution()

        # stdinからデータを読み取り（1回のみ）
        try:
            input_data = sys.stdin.read()
            if input_data.strip():
                hook_data = json.loads(input_data)
            else:
                hook_data = {}
                debug_log("No hook data (empty stdin)")
        except json.JSONDecodeError as e:
            debug_log(f"JSON decode error: {e}")
            hook_data = {}
        except Exception as e:
            debug_log(f"Unexpected error reading stdin: {e}")
            hook_data = {}

        tool_name = hook_data.get("tool_name", "")
        tool_input = hook_data.get("tool_input", {})
        debug_log(f"Tool name: {tool_name}")

        # Bashツールの場合のみmkdir/touchチェック実行（matcher="Bash"相当）
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            if command and ("mkdir" in command or "touch" in command):
                sys.path.insert(0, str(Path(__file__).parent))
                from post_tool_use import post_mkdir_check
                # mkdir/touchコマンドの場合のみ検証実行
                if "mkdir" in command:
                    post_mkdir_check.verify_mkdir_execution(command)
                elif "touch" in command:
                    post_mkdir_check.verify_touch_execution(command)

        # 全ツールでログ記録（matcher="*"相当）
        if hook_data:
            # postu_tool_loggerを実行（全ツール）
            try:
                from post_tool_use import postu_tool_logger
                postu_tool_logger.main(hook_data)
            except Exception as e:
                debug_log(f"Error in postu_tool_logger: {e}")

            # postu_bash_loggerを実行（Bashのみ）
            if tool_name == "Bash":
                try:
                    from post_tool_use import postu_bash_logger
                    postu_bash_logger.main(hook_data)
                except Exception as e:
                    debug_log(f"Error in postu_bash_logger: {e}")

            # postu_cd_warningを実行（Bashのみ）
            if tool_name == "Bash":
                try:
                    from post_tool_use import postu_cd_warning
                    postu_cd_warning.execute(hook_data)
                except Exception as e:
                    debug_log(f"Error in postu_cd_warning: {e}")

            # postu_context7_reminderを実行（Context7ツールのみ）
            if tool_name.startswith("mcp__context7__"):
                try:
                    from post_tool_use import postu_context7_reminder
                    postu_context7_reminder.main(hook_data)
                except Exception as e:
                    debug_log(f"Error in postu_context7_reminder: {e}")

            # postu_codex_execute_reminderを実行（WebSearch, Context7ツール）
            if tool_name == "WebSearch" or tool_name.startswith("mcp__context7__"):
                try:
                    from post_tool_use import postu_codex_execute_reminder
                    postu_codex_execute_reminder.execute(hook_data)
                except Exception as e:
                    debug_log(f"Error in postu_codex_execute_reminder: {e}")

            # postu_fix_hook_utilsを実行（Editのみ）
            if tool_name == "Edit":
                try:
                    from post_tool_use import postu_fix_hook_utils
                    postu_fix_hook_utils.main(hook_data)
                except Exception as e:
                    debug_log(f"Error in postu_fix_hook_utils: {e}")

            # postu_file_not_found_suggest は PreToolUse に移行済み
            # (pretu_file_not_found_suggest.py)
        else:
            debug_log("No hook_data, skipping loggers")

        # debug_log("finished.")


    except Exception as e:
        error_msg = f"Unexpected error in main(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise

if __name__ == "__main__":
    main()
