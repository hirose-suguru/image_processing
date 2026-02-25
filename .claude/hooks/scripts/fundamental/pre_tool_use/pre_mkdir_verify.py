#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pre_mkdir_verify.py
mkdir実行前のチェックを行うPreToolUse hook
"""
import sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import (
        log_hook_execution,
        debug_log,
        log_hook_error,
        stop_tool_use
    )

except ImportError as e:
    error_msg = f"Failed to import hook_utils: {e}"
    print(f"[HOOK ERROR] {error_msg}")
    print(f"[HOOK ERROR] Script: {__file__}")
    print(f"[HOOK ERROR] sys.path: {sys.path}")
    sys.stderr.write(f"[HOOK ERROR] {error_msg}\n")
    sys.stderr.write(f"[HOOK ERROR] Script: {__file__}\n")
    sys.exit(1)

def check_mkdir_command(tool_input):
    """
    mkdirコマンドのチェックを実行

    Note:
        ブロック時は stop_tool_use() で終了
    """
    # Bashコマンドを取得
    command = tool_input.get("command", "").strip()

    # mkdirコマンドでない場合は許可（何もしない）
    # コマンドの先頭がmkdirで始まるかチェック（ファイルパスに含まれるmkdirを誤検知しない）
    command_parts = command.split()
    if not command_parts or command_parts[0] != "mkdir":
        return

    # (1) mkdir -p 以外は拒否
    if "-p" not in command and "--parents" not in command:
        debug_log("denied: mkdir command requires -p option")
        stop_tool_use(
            "[ERROR] mkdir command requires -p option.\n"
            "Reason: Prevent conflicts with existing directories and safely create parent directories.\n"
            "Correct example: mkdir -p path/to/directory"
        )

    # ディレクトリパスを抽出（簡易的な実装）
    # "mkdir -p some/path" から "some/path" を抽出
    parts = command.split()
    target_path = None
    for i, part in enumerate(parts):
        if part in ["-p", "--parents"]:
            if i + 1 < len(parts):
                target_path = parts[i + 1]
                break

    if not target_path:
        # パスが見つからない場合は許可（チェック不可）
        debug_log("allowed: mkdir -p option specified but no path found")
        return

    # (i) 作成前チェック: ディレクトリが既に存在するか
    path_obj = Path(target_path)

    # (命名規則チェック) "test"が含まれるディレクトリ名を拒否
    # 全てのパス要素をチェック（A/B/test のような場合も検出）
    all_parts = path_obj.parts

    for part in all_parts:
        part_lower = part.lower()

        if "test" in part_lower:
            debug_log(f"denied: path contains 'test': {target_path}")
            stop_tool_use(
                f"[ERROR] Cannot create directory containing 'test' in path.\n"
                f"Specified path: {target_path}\n"
                f"Problematic part: {part}\n"
                f"Please use existing test directory structure for test files."
            )

    # (2) 既存ディレクトリの検知と内容確認
    if path_obj.exists():
        if path_obj.is_dir():
            # ディレクトリが既に存在する場合はエラーで停止
            debug_log(f"denied: directory already exists: {target_path}")

            try:
                contents = list(path_obj.iterdir())
                file_count = sum(1 for item in contents if item.is_file())
                dir_count = sum(1 for item in contents if item.is_dir())

                error_lines = [
                    f"[ERROR] ディレクトリ '{target_path}' は既に存在します。",
                    f"  内容: {file_count}個のファイル, {dir_count}個のサブディレクトリ"
                ]

                if contents:
                    error_lines.append("  主な内容:")
                    for item in contents[:5]:  # 最大5件表示
                        item_type = "[DIR]" if item.is_dir() else "[FILE]"
                        error_lines.append(f"    {item_type} {item.name}")
                    if len(contents) > 5:
                        error_lines.append(f"    ... 他 {len(contents) - 5} 件")
                else:
                    error_lines.append("  （空のディレクトリ）")

                stop_tool_use("\n".join(error_lines))
            except PermissionError:
                stop_tool_use(f"[ERROR] ディレクトリ '{target_path}' は既に存在します。")
        else:
            # ファイルが存在する場合はエラー
            debug_log(f"denied: path exists as file: {target_path}")
            stop_tool_use(
                f"[ERROR] '{target_path}' は既にファイルとして存在します。\n"
                f"ディレクトリを作成できません。"
            )

    # 許可（何も出力しない）
    debug_log(f"allowed: mkdir -p {target_path}")


def execute(tool_data: dict):
    """
    mkdirコマンドの検証を実行（パッケージから呼び出される）

    Args:
        tool_data: パッケージから渡されたツールデータ

    Note:
        ブロック時は stop_tool_use() で終了
    """
    try:
        log_hook_execution()
        #debug_log("started.")

        if not tool_data:
            debug_log("No tool data received, allowing by default")
            return

        # Bashツール以外はスキップ
        tool_name = tool_data.get("tool_name", "")
        if tool_name != "Bash":
            return

        tool_input = tool_data.get("tool_input", {})

        # チェック実行（ブロック時はstop_tool_useで終了）
        check_mkdir_command(tool_input)

        #debug_log("finished.")

    except Exception as e:
        error_msg = f"Unexpected error in execute(): {e}"
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
