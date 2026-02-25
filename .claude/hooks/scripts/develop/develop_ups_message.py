#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
develop_ups_message.py
Developモード有効化時のメッセージ表示
"""
import sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import log_hook_execution, debug_log, get_path_from_config, log_hook_error, load_json5

except ImportError as e:
    error_msg = f"Failed to import hook_utils: {e}"
    # stdoutとstderrに出力のみ（ファイル書き込みはしない）
    print(f"[HOOK ERROR] {error_msg}")
    print(f"[HOOK ERROR] Script: {__file__}")
    print(f"[HOOK ERROR] sys.path: {sys.path}")
    sys.stderr.write(f"[HOOK ERROR] {error_msg}\n")
    sys.stderr.write(f"[HOOK ERROR] Script: {__file__}\n")
    sys.exit(1)

def get_split_target_files():
    """file_split_config.jsonから分割ファイルのリストを取得"""
    try:
        config_path = get_path_from_config("file_split_config")
        config = load_json5(config_path)

        target_files = []
        for unified_file, info in config.get("targets", {}).items():
            sections = info.get("sections", {})
            for section_name, split_file in sections.items():
                target_files.append(split_file)

        return target_files
    except Exception as e:
        debug_log(f"Failed to load split target files: {e}")
        return []

def main():
    """Developモード有効化時のメッセージ表示"""
    try:
        log_hook_execution()
        debug_log("started.")

        print("\n=== Develop Mode Activated ===")
        print("統合ファイルへの Edit/Write は禁止されています。")
        print("splited_files/ の以下のファイルのみ編集可能です：")

        target_files = get_split_target_files()
        if target_files:
            for file in target_files:
                print(f"  - {file}")

            print("\nprogress.md を確認して、`splited_files/` にあるファイルのうち現在のタスクで扱う必要があるファイルを確認してください。")
        else:
            print("  (file_split_config.json からファイルを取得できませんでした)")

        debug_log("finished.")


    except Exception as e:
        error_msg = f"Unexpected error in main(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise

if __name__ == "__main__":
    main()
