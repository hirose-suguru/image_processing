#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
show_dev_structure.py
開発に関わるファイルのディレクトリ構造を表示
change_key_v4/ プロジェクトの構造を表示する
"""
import sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import log_hook_execution, get_project_root, get_obsidian_config, debug_log, print_tree, log_hook_error

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
    try:
        log_hook_execution()
        debug_log("started.")

        project_root = get_project_root()
        debug_log(f"Project root: {project_root}")

        # obsidian vault_pathから開発ディレクトリを取得
        try:
            obs_config = get_obsidian_config()
            vault_path = obs_config.get("vault_path", "")

            if not vault_path:
                debug_log("ERROR: vault_path is not configured")
                print("[show_dev_structure] ERROR: vault_path is not configured", file=sys.stderr)
                return

            # vault_path (例: "change_key_v4/ahk_v4_obsidian") から親ディレクトリを取得
            dev_dir = (project_root / vault_path).parent
            debug_log(f"Development directory: {dev_dir}")
        except (KeyError, Exception) as e:
            debug_log(f"ERROR: Failed to get obsidian config: {e}")
            print(f"[show_dev_structure] ERROR: Failed to get obsidian config: {e}", file=sys.stderr)
            return

        if dev_dir.exists():
            print()
            print("=" * 20)
            print(f"開発プロジェクト構造 ({dev_dir.name}/):")
            print("=" * 20)
            print(f"{dev_dir.name}/")
            print_tree(
                dev_dir,
                max_depth=4,
                exclude_dirs=["__pycache__", ".git", ".obsidian", "splited_files", "icons", "Clippings", "_meta", "_templates", "ahk_v4_obsidian"]
            )
            print()
            print("=" * 20)
            print()
        else:
            debug_log(f"WARNING: {dev_dir.name}/ does not exist at {dev_dir}")
            print()
            print("=" * 20)
            print(f"開発プロジェクト構造 ({dev_dir.name}/):")
            print("=" * 20)
            print(f"{dev_dir.name}/ ディレクトリは存在しません")
            print("=" * 20)
            print()

        debug_log("finished.")


    except Exception as e:
        error_msg = f"Unexpected error in main(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise

if __name__ == "__main__":
    main()
