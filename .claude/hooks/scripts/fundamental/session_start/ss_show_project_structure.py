#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
show_project_structure.py
SessionStart hookで実行されるスクリプト
fundamental_hook_config.json5で指定されたディレクトリ構造を表示
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from hook_utils import log_hook_execution, get_project_root, get_obsidian_config, debug_log, print_tree, get_path_from_config, load_json5

def load_config() -> dict:
    default = {
        "enabled": True,
        "dirs": [
            {
                "paths": [".claude/hooks"],
                "max_depth": 3,
                "exclude_dirs": ["__pycache__", ".git"]
            }
        ]
    }
    try:
        config_path = get_path_from_config("fundamental_hook_config")
        all_config = load_json5(config_path)
        config = all_config.get("show_project_structure", default)
        return config
    except Exception as e:
        debug_log(f"Failed to load fundamental_hook_config: {e}, using default")
        config = default
        return config

def main():
    log_hook_execution()

    config = load_config()
    if not config.get("enabled", True):
        #debug_log("show_project_structure is disabled.")
        return

    project_root = get_project_root()
    debug_log(f"Project root: {project_root}")

    # 設定されたディレクトリを表示
    for entry in config.get("dirs", []):
        max_depth = entry.get("max_depth", 3)
        exclude_dirs = entry.get("exclude_dirs", ["__pycache__", ".git"])

        for path_str in entry.get("paths", []):
            target = project_root / path_str
            if target.exists():
                debug_log(f"{target} exists, displaying structure")
                print()
                print(f"{path_str}/ ディレクトリ構造:")
                print(f"{path_str}/")
                print_tree(target, max_depth=max_depth, exclude_dirs=exclude_dirs)
                print()
            else:
                debug_log(f"{target} does not exist!")

    # obsidian/ の構造を表示
    try:
        obs_config = get_obsidian_config()
        debug_log(f"Obsidian config: {obs_config}")
        vault_path = obs_config.get("vault_path", "")
        debug_log(f"Vault path from config: {vault_path}")

        if vault_path:
            obsidian_dir = project_root / vault_path
            debug_log(f"Checking obsidian vault at: {obsidian_dir}")
            if obsidian_dir.exists():
                debug_log("Obsidian vault exists, displaying structure")
                print(f"obsidian/ ディレクトリ構造 ({vault_path}):")
                print(f"{vault_path}/")
                print_tree(obsidian_dir, max_depth=4, exclude_dirs=["__pycache__", ".git", ".obsidian"])
                print()
            else:
                print(f"obsidian/ ディレクトリ構造 ({vault_path}):")
                print(f"{vault_path}/ ディレクトリは存在しません")
                print()
        else:
            debug_log("finished.")
            #print("obsidian/ ディレクトリ構造:")
            #print("vault_pathが設定されていません")
            #print()
    except KeyError as e:
        debug_log(f"KeyError when getting obsidian config: {e}")
        #print("obsidian/ ディレクトリ構造:")
        #print("Obsidian設定が存在しません")
        #print()

    debug_log("finished.")

if __name__ == "__main__":
    main()
