#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
import re

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import log_hook_execution, debug_log, get_path_from_config, log_hook_error, load_json5, stop_tool_use

except ImportError as e:
    error_msg = f"Failed to import hook_utils: {e}"
    # stdoutとstderrに出力のみ（ファイル書き込みはしない）
    print(f"[HOOK ERROR] {error_msg}")
    print(f"[HOOK ERROR] Script: {__file__}")
    print(f"[HOOK ERROR] sys.path: {sys.path}")
    sys.stderr.write(f"[HOOK ERROR] {error_msg}\n")
    sys.stderr.write(f"[HOOK ERROR] Script: {__file__}\n")
    sys.exit(1)

def load_banned_commands_config():
    """Load banned commands configuration from JSON"""
    try:
        config_path = get_path_from_config("banned_commands_config")
        return load_json5(config_path)
    except Exception as e:
        debug_log(f"Failed to load banned_commands_config: {e}")
        return None

def execute(tool_data: dict):
    """
    禁止コマンド/操作のチェックを実行

    Args:
        tool_data: パッケージから渡されたツールデータ
    """
    try:
        log_hook_execution()
        #debug_log("started.")

        if not tool_data:
            debug_log("No tool data received")
            return

        # ツール名を取得
        tool_name = tool_data.get("tool_name", "")

        if not tool_name:
            debug_log("No tool_name found in tool data")
            return

        # ツール種別ごとに対象を取得
        target = None
        if tool_name == "Bash":
            target = tool_data.get("tool_input", {}).get("command", "")
        elif tool_name == "Edit":
            target = tool_data.get("tool_input", {}).get("file_path", "")
        elif tool_name == "Write":
            target = tool_data.get("tool_input", {}).get("file_path", "")
        # 他のツールも必要に応じて追加可能

        if not target:
            # 対象がない場合はチェックをスキップ（このツールは監視対象外）
            return

        # Load banned commands configuration
        config = load_banned_commands_config()
        if not config:
            debug_log("Config not loaded, skipping checks")
            return

        banned_patterns = config.get("banned_patterns", [])
        default_message = config.get("default_message", "Operation is not allowed.")

        # Check for banned patterns
        for item in banned_patterns:
            # toolフィールドでフィルタリング
            item_tool = item.get("tool", "")
            if item_tool and item_tool != tool_name:
                continue  # このパターンは別のツール用

            pattern = item.get("pattern", "")
            pattern_type = item.get("type", "string")

            matched = False
            if pattern_type == "regex":
                if re.search(pattern, target, re.IGNORECASE):
                    matched = True
            else:
                if pattern.lower() in target.lower():
                    matched = True

            if matched:
                # Use pattern-specific message, fall back to default
                message = item.get("message", default_message)

                debug_log(f"Banned {tool_name} operation detected: {target}")
                stop_tool_use(message)

        # Operation is allowed
        #debug_log("finished.")


    except Exception as e:
        error_msg = f"Unexpected error in main(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise

def main():
    """スタンドアロン実行用のエントリーポイント"""
    from hook_utils import get_tool_data_from_stdin
    tool_data = get_tool_data_from_stdin()
    execute(tool_data)

if __name__ == "__main__":
    main()
