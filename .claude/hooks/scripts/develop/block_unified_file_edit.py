#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
block_unified_file_edit.py
developモード時に統合ファイルへのEdit/Writeを禁止するhook
"""
import sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import log_hook_execution, debug_log, get_tool_data_from_stdin, get_path_from_config, get_hook_toggle, log_hook_error, load_json5

except ImportError as e:
    error_msg = f"Failed to import hook_utils: {e}"
    # stdoutとstderrに出力のみ（ファイル書き込みはしない）
    print(f"[HOOK ERROR] {error_msg}")
    print(f"[HOOK ERROR] Script: {__file__}")
    print(f"[HOOK ERROR] sys.path: {sys.path}")
    sys.stderr.write(f"[HOOK ERROR] {error_msg}\n")
    sys.stderr.write(f"[HOOK ERROR] Script: {__file__}\n")
    sys.exit(1)

def get_unified_files():
    """file_split_config.jsonから統合ファイルのリストを取得"""
    try:
        config_path = get_path_from_config("file_split_config")
        config = load_json5(config_path)

        unified_files = list(config.get("targets", {}).keys())
        return unified_files
    except Exception as e:
        debug_log(f"Failed to load unified files: {e}")
        return []

def main():
    try:
        # developトグルがOFFの場合はスキップ
        if not get_hook_toggle("develop"):
            # debug_log("develop toggle is off. hook was canceled.")
            return

        # ツールデータを取得
        tool_data = get_tool_data_from_stdin()
        # debug_log(f"tool_data: {tool_data}")

        if not tool_data:
            debug_log("No tool data received")
            return

        tool_name = tool_data.get("tool_name", "")
        tool_input = tool_data.get("tool_input", {})

        # Edit または Write ツールのみチェック
        if tool_name not in ["Edit", "Write"]:
            return
    
        file_path = tool_input.get("file_path", "")

        if not file_path:
            log_hook_execution()
            debug_log("No file_path found in tool data")
            return

        # 統合ファイルのリストを取得
        unified_files = get_unified_files()

        if not unified_files:
            debug_log("No unified files found in configuration")
            return

        # file_pathを正規化して比較
        file_path_normalized = Path(file_path).as_posix()

        for unified_file in unified_files:
            unified_file_normalized = Path(unified_file).as_posix()

            # パスが一致するかチェック（絶対パス/相対パス両方に対応）
            if (file_path_normalized == unified_file_normalized or
                file_path_normalized.endswith(unified_file_normalized)):

                log_hook_execution()
                debug_log("started.")
                debug_log(f"Blocked {tool_name} to unified file: {file_path}")
                sys.stderr.write(f"[エラー] Develop modeが有効です: {unified_file} への {tool_name} は禁止されています。\n")
                sys.stderr.write("`splited_files/` 内のファイルを編集してください。\n")
                sys.exit(2)

        # 統合ファイルではない場合は許可（ログなし）


    except Exception as e:
        error_msg = f"Unexpected error in main(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise

if __name__ == "__main__":
    main()
