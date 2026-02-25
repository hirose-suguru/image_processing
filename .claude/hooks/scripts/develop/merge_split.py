#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_split.py - Merge split files back into unified file
Triggered by: stop
"""
import sys
from pathlib import Path
import json
import os
import re

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import log_hook_execution, debug_log, get_path_from_config, get_hook_path_config_path, get_hook_toggle, log_hook_error, load_json5

except ImportError as e:
    error_msg = f"Failed to import hook_utils: {e}"
    # stdoutとstderrに出力のみ（ファイル書き込みはしない）
    print(f"[HOOK ERROR] {error_msg}")
    print(f"[HOOK ERROR] Script: {__file__}")
    print(f"[HOOK ERROR] sys.path: {sys.path}")
    sys.stderr.write(f"[HOOK ERROR] {error_msg}\n")
    sys.stderr.write(f"[HOOK ERROR] Script: {__file__}\n")
    sys.exit(1)

def load_file_split_config(config_path):
    """Load file split configuration"""
    try:
        config = load_json5(config_path)
        if not config:
            print(f"[merge_split] Error: Config file is empty: {config_path}", file=sys.stderr)
            return None
        return config
    except FileNotFoundError:
        print(f"[merge_split] Error: Config file not found: {config_path}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"[merge_split] Error: Invalid JSON in config: {e}", file=sys.stderr)
        return None

def get_marker_pattern(config, file_ext):
    """Get marker patterns for file extension"""
    markers = config.get("markers", {}).get(file_ext)
    if not markers:
        return None, None

    start_template = markers["start"]
    end_template = markers["end"]

    return start_template, end_template

def merge_file(unified_path, sections, input_dir, config):
    """Merge split files into unified file"""
    debug_log(f"Merging file: {unified_path}")
    file_ext = Path(unified_path).suffix
    start_template, end_template = get_marker_pattern(config, file_ext)

    if not start_template or not end_template:
        debug_log(f"No marker pattern for {file_ext}")
        print(f"[merge_split] Warning: No marker pattern for {file_ext}", file=sys.stderr)
        return False

    # Read unified file
    try:
        with open(unified_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        debug_log(f"Unified file not found: {unified_path}")
        print(f"[merge_split] Error: Unified file not found: {unified_path}", file=sys.stderr)
        return False
    except Exception as e:
        debug_log(f"Failed to read unified file: {e}")
        print(f"[merge_split] Error: Failed to read {unified_path}: {e}", file=sys.stderr)
        return False

    # Process each section
    merged_content = content
    merge_count = 0
    for section_name, split_file in sections.items():
        split_path = os.path.join(input_dir, split_file)
        # debug_log(f"Processing section '{section_name}' from {split_path}")

        # Read split file
        try:
            with open(split_path, 'r', encoding='utf-8') as f:
                section_content = f.read()
        except FileNotFoundError:
            print(f"[merge_split] Warning: Split file not found: {split_path}, skipping", file=sys.stderr)
            debug_log(f"Split file not found: {split_path}, skipping")
            continue
        except Exception as e:
            print(f"[merge_split] Error: Failed to read {split_path}: {e}", file=sys.stderr)
            debug_log(f"Failed to read split file: {e}")
            continue

        # マーカー文字列を生成（テンプレートの{name}をセクション名に置換）
        start_marker = start_template.replace("{name}", section_name)
        end_marker = end_template.replace("{name}", section_name)
        # debug_log(f"Start marker: {start_marker}")
        # debug_log(f"End marker: {end_marker}")

        # 正規表現パターンを作成してマーカー区間をマッチング
        # パターン: 開始マーカー + 任意の内容（非貪欲） + 終了マーカー
        pattern = re.escape(start_marker) + r'.*?' + re.escape(end_marker)

        # 置換用文字列を作成（マーカー + 改行 + 分割ファイルの内容 + 改行 + マーカー）
        replacement = start_marker + '\n' + section_content + '\n' + end_marker

        # バックスラッシュをエスケープ
        # re.subn()でバックスラッシュが特殊文字として解釈されるのを防ぐ
        replacement = replacement.replace('\\', r'\\')

        # マーカー間の内容を置換（最初の1箇所のみ、複数行マッチング有効）
        new_content, count = re.subn(pattern, replacement, merged_content, count=1, flags=re.DOTALL)

        if count == 0:
            debug_log(f"Markers not found for section '{section_name}'")
            print(f"[merge_split] Warning: Markers not found for '{section_name}'", file=sys.stderr)
        else:
            merged_content = new_content
            merge_count += 1

    # Write merged content back
    try:
        with open(unified_path, 'w', encoding='utf-8') as f:
            f.write(merged_content)
        return True
    except Exception as e:
        debug_log(f"Failed to write unified file: {e}")
        print(f"[merge_split] Error: Failed to write {unified_path}: {e}", file=sys.stderr)
        return False

def main():
    try:
        # "develop" トグルがOFFの場合はスキップ（静かに）
        if not get_hook_toggle("develop"):
            # debug_log("develop toggle is off. hook was canceled.")
            return

        # "develop"トグルがOnの場合の処理
        log_hook_execution()
        debug_log("started.")

        try:
            # Get file_split_config path using get_path_from_config
            try:
                config_path = get_path_from_config("file_split_config")
                debug_log(f"Config path: {config_path}")
            except KeyError as e:
                debug_log(f"Error: {e}")
                print(f"[merge_split] Error: file_split_config not found in hook_path_config.json", file=sys.stderr)
                return

            # Get splited_files_dir from hook_path_config.json
            try:
                hook_config_path = get_hook_path_config_path()
                hook_config = load_json5(hook_config_path)
                splited_files_dir = hook_config.get("splited_files_dir", "splited_files")
            except Exception as e:
                debug_log(f"Failed to load hook_path_config.json: {e}")
                splited_files_dir = "splited_files"

            # Load configuration
            config = load_file_split_config(config_path)
            if not config:
                debug_log("Failed to load config")
                return

            targets = config.get("targets", {})
            if not targets:
                debug_log("No targets configured")
                print("[merge_split] No targets configured", file=sys.stderr)
                return

            # Process each target
            success_count = 0
            for unified_path, target_config in targets.items():
                debug_log(f"Processing target: {unified_path}")
                sections = target_config.get("sections", {})

                if not sections:
                    debug_log(f"No sections for {unified_path}")
                    print(f"[merge_split] No sections for {unified_path}", file=sys.stderr)
                    continue

                # Determine input directory (relative to unified file)
                unified_dir = os.path.dirname(unified_path)
                if unified_dir:
                    input_dir = os.path.join(unified_dir, splited_files_dir)
                else:
                    input_dir = splited_files_dir

                debug_log(f"Input directory: {input_dir}")

                # Merge files
                if merge_file(unified_path, sections, input_dir, config):
                    success_count += 1

            debug_log("merging file was successful.")
            debug_log("finished.")

        except Exception as e:
            debug_log(f"Unexpected error: {e}")
            print(f"[merge_split] Unexpected error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()


    except Exception as e:
        error_msg = f"Unexpected error in main(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise

if __name__ == "__main__":
    main()
