#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
split_file.py - Split unified file into multiple files based on markers
Triggered by: user_prompt_submit
"""
import sys
from pathlib import Path
import json
import os
import re

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import log_hook_execution, debug_log, get_path_from_config, get_hook_path_config_path, log_hook_error, load_json5, save_json5

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
            print(f"[split_file] Error: Config file is empty: {config_path}", file=sys.stderr)
            return None
        return config
    except FileNotFoundError:
        print(f"[split_file] Error: Config file not found: {config_path}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"[split_file] Error: Invalid JSON in config: {e}", file=sys.stderr)
        return None

def save_file_split_config(config_path, config):
    """Save file split configuration"""
    try:
        save_json5(config_path, config)
        return True
    except Exception as e:
        print(f"[split_file] Error: Failed to save config: {e}", file=sys.stderr)
        return False

def get_marker_pattern(config, file_ext):
    """Get marker patterns for file extension"""
    markers = config.get("markers", {}).get(file_ext)
    if not markers:
        return None, None

    # {name}部分を一時プレースホルダーに置換（正規表現エスケープ前）
    temp_start = markers["start"].replace("{name}", "___PLACEHOLDER___")
    temp_end = markers["end"].replace("{name}", "___PLACEHOLDER___")

    # 正規表現の特殊文字をエスケープ
    start_pattern = re.escape(temp_start)
    end_pattern = re.escape(temp_end)

    # プレースホルダーをキャプチャグループに置換（セクション名を抽出）
    start_pattern = start_pattern.replace("___PLACEHOLDER___", r"(\w+)")
    end_pattern = end_pattern.replace("___PLACEHOLDER___", r"(\w+)")

    return start_pattern, end_pattern

def extract_markers(file_path, config):
    """Extract all markers from unified file"""
    # debug_log(f"Extracting markers from: {file_path}")
    file_ext = Path(file_path).suffix
    start_pattern, end_pattern = get_marker_pattern(config, file_ext)

    if not start_pattern or not end_pattern:
        debug_log(f"No marker pattern for {file_ext}")
        print(f"[split_file] Warning: No marker pattern for {file_ext}", file=sys.stderr)
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # debug_log(f"Read {len(content)} characters from {file_path}")
    except FileNotFoundError:
        debug_log(f"File not found: {file_path}")
        print(f"[split_file] Warning: File not found: {file_path}", file=sys.stderr)
        return {}
    except Exception as e:
        debug_log(f"Failed to read {file_path}: {e}")
        print(f"[split_file] Error: Failed to read {file_path}: {e}", file=sys.stderr)
        return {}

    sections = {}
    lines = content.split('\n')
    current_section = None
    section_content = []
    seen_sections = set()

    for i, line in enumerate(lines, 1):
        # 開始マーカーをチェック
        start_match = re.search(start_pattern, line)
        if start_match:
            section_name = start_match.group(1)

            # 重複セクションをチェック
            if section_name in seen_sections:
                debug_log(f"Duplicate section '{section_name}' at line {i}")
                print(f"[split_file] Warning: Duplicate section '{section_name}' at line {i}, skipping", file=sys.stderr)
                continue

            if current_section:
                debug_log(f"Nested or unclosed section '{current_section}' at line {i}")
                print(f"[split_file] Error: Nested or unclosed section '{current_section}' at line {i}", file=sys.stderr)
                return {}

            current_section = section_name
            section_content = []
            seen_sections.add(section_name)
            continue

        # 終了マーカーをチェック
        end_match = re.search(end_pattern, line)
        if end_match:
            section_name = end_match.group(1)

            if not current_section:
                debug_log(f"End marker without start at line {i}")
                print(f"[split_file] Error: End marker without start at line {i}", file=sys.stderr)
                return {}

            if section_name != current_section:
                debug_log(f"Mismatched markers '{current_section}' vs '{section_name}' at line {i}")
                print(f"[split_file] Error: Mismatched markers '{current_section}' vs '{section_name}' at line {i}", file=sys.stderr)
                return {}

            # セクション内容を保存
            sections[current_section] = '\n'.join(section_content)
            # debug_log(f"Extracted section '{section_name}' (start: {start_line}, end: {i}, lines: {len(section_content)})")
            current_section = None
            section_content = []
            continue

        # セクション内の場合は内容を収集
        if current_section:
            section_content.append(line)

    if current_section:
        debug_log(f"Unclosed section: {current_section}")
        print(f"[split_file] Error: Unclosed section '{current_section}'", file=sys.stderr)
        return {}

    # debug_log(f"Extracted {len(sections)} sections: {list(sections.keys())}")
    return sections

def split_file(unified_path, sections, output_dir, config):
    """Split unified file into multiple files"""
    # debug_log(f"Splitting file: {unified_path}")
    file_ext = Path(unified_path).suffix

    # 出力ディレクトリを作成
    os.makedirs(output_dir, exist_ok=True)
    # debug_log(f"Created/verified output directory: {output_dir}")

    # 統合ファイルからセクションを抽出
    extracted_sections = extract_markers(unified_path, config)

    if not extracted_sections:
        debug_log(f"No sections found in {unified_path}")
        print(f"[split_file] No sections found in {unified_path}", file=sys.stderr)
        return False

    # 抽出したセクションで設定を更新
    updated_sections = {}
    for section_name in extracted_sections.keys():
        output_file = sections.get(section_name, f"{section_name}{file_ext}")
        updated_sections[section_name] = output_file
        # debug_log(f"Section '{section_name}' -> {output_file}")

    # 分割ファイルを書き込み
    for section_name, content in extracted_sections.items():
        output_file = updated_sections[section_name]
        output_path = os.path.join(output_dir, output_file)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            # debug_log(f"Wrote {len(content)} chars to {output_path}")
        except Exception as e:
            debug_log(f"Failed to write {output_path}: {e}")
            print(f"[split_file] Error: Failed to write {output_path}: {e}", file=sys.stderr)
            return False

    # debug_log(f"Successfully split into {len(updated_sections)} files")
    return updated_sections

def main():
    try:
        log_hook_execution()
        debug_log("started.")
        try:
            # get_path_from_configを使ってfile_split_configのパスを取得
            try:
                config_path = get_path_from_config("file_split_config")
                # debug_log(f"Config path: {config_path}")
            except KeyError as e:
                debug_log(f"Error: {e}")
                print(f"[split_file] Error: file_split_config not found in hook_path_config.json", file=sys.stderr)
                return

            # hook_path_config.jsonからsplited_files_dirを取得
            try:
                hook_config_path = get_hook_path_config_path()
                hook_config = load_json5(hook_config_path)
                splited_files_dir = hook_config.get("splited_files_dir", "splited_files")
                # debug_log(f"Split files directory: {splited_files_dir}")
            except Exception as e:
                debug_log(f"Failed to load hook_path_config.json: {e}")
                splited_files_dir = "splited_files"

            # ファイル分割設定を読み込み
            config = load_file_split_config(config_path)
            if not config:
                debug_log("Failed to load file_split_config.json")
                return

            targets = config.get("targets", {})
            if not targets:
                debug_log("No targets configured in file_split_config.json")
                print("[split_file] No targets configured", file=sys.stderr)
                return

            # debug_log(f"Processing {len(targets)} target(s)")

            # 各ターゲットを処理
            config_updated = False
            for unified_path, target_config in targets.items():
                # debug_log(f"Processing target: {unified_path}")
                sections = target_config.get("sections", {})

                # 出力ディレクトリを決定（統合ファイルからの相対パス）
                unified_dir = os.path.dirname(unified_path)
                if unified_dir:
                    output_dir = os.path.join(unified_dir, splited_files_dir)
                else:
                    output_dir = splited_files_dir

                # debug_log(f"Output directory: {output_dir}")

                # ファイルを分割して更新されたセクションを取得
                updated_sections = split_file(unified_path, sections, output_dir, config)

                if updated_sections and updated_sections != sections:
                    # 新しいセクションで設定を更新
                    target_config["sections"] = updated_sections
                    config_updated = True
                    debug_log(f"Found {len(updated_sections)} sections in {unified_path}")
                    print(f"[split_file] Found {len(updated_sections)} sections")
                elif updated_sections:
                    pass  # debug_log(f"No changes detected in {unified_path}")
                else:
                    debug_log(f"No sections found in {unified_path}")

            # 必要に応じて更新された設定を保存
            if config_updated:
                if save_file_split_config(config_path, config):
                    debug_log("Config file updated successfully")
                    print(f"[split_file] Config updated")
                else:
                    debug_log("Failed to save config file")
                    print(f"[split_file] Failed to save config", file=sys.stderr)
            # else:
            #     debug_log("No config updates needed")

            debug_log("splitting file was successful.")

        except Exception as e:
            debug_log(f"Unexpected error: {e}")
            print(f"[split_file] Unexpected error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()


    except Exception as e:
        error_msg = f"Unexpected error in main(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise

if __name__ == "__main__":
    main()
