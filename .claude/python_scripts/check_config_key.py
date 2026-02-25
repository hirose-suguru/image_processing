#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_config_key.py
hook_path_config.json5 に指定されたキーが存在するかをチェックするユーティリティ

使用例:
    python .claude/python_scripts/check_config_key.py log_file
    python .claude/python_scripts/check_config_key.py timestamps_file debug_file
"""
import sys
from pathlib import Path

# hook_utils.pyをインポート
hooks_scripts_path = Path(__file__).parent.parent / "hooks" / "scripts"
sys.path.insert(0, str(hooks_scripts_path))
from hook_utils import load_json5, get_hook_path_config_path

def check_keys(keys: list) -> dict:
    """
    指定されたキーがhook_path_config.json5に存在するかチェック

    Args:
        keys: チェックするキーのリスト

    Returns:
        {key: exists} の辞書
    """
    config_path = get_hook_path_config_path()
    config = load_json5(config_path)

    results = {}
    for key in keys:
        results[key] = key in config

    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python check_config_key.py <key1> [key2] [key3] ...")
        print("\nExample:")
        print("  python .claude/python_scripts/check_config_key.py log_file")
        print("  python .claude/python_scripts/check_config_key.py timestamps_file debug_file")
        sys.exit(1)

    keys = sys.argv[1:]
    results = check_keys(keys)

    print("\n=== hook_path_config.json5 Key Check ===")
    for key, exists in results.items():
        status = "✓ EXISTS" if exists else "✗ NOT FOUND"
        print(f"{status}: {key}")

    # すべてのキーが存在しない場合は終了コード1を返す
    if not any(results.values()):
        sys.exit(1)

if __name__ == "__main__":
    main()
