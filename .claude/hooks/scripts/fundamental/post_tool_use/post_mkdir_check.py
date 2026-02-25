#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
post_filesystem_verify.py
mkdir/touch実行後の検証を行うPostToolUse hook
"""
import sys
import json
import shlex
from pathlib import Path

# 1階層上のhook_utils.pyをインポート
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import log_hook_execution, debug_log, log_hook_error
except ImportError as e:
    error_msg = f"Failed to import hook_utils: {e}"
    print(f"[HOOK ERROR] {error_msg}")
    print(f"[HOOK ERROR] Script: {__file__}")
    print(f"[HOOK ERROR] sys.path: {sys.path}")
    sys.stderr.write(f"[HOOK ERROR] {error_msg}\n")
    sys.stderr.write(f"[HOOK ERROR] Script: {__file__}\n")
    sys.exit(1)

def extract_paths_from_command(command: str, base_command: str) -> list:
    """
    コマンドからパスを抽出（オプションを除く）

    Args:
        command: 実行されたコマンド文字列
        base_command: ベースコマンド名 ("mkdir" or "touch")

    Returns:
        抽出されたパスのリスト
    """
    try:
        # shlex.split()でコマンドを安全に分割
        parts = shlex.split(command)
    except ValueError:
        # クォートが閉じていない等のエラー時は単純なsplit
        parts = command.split()

    paths = []
    skip_next = False

    for i, part in enumerate(parts):
        if skip_next:
            skip_next = False
            continue

        # ベースコマンド自体はスキップ
        if part == base_command:
            continue

        # オプション（-で始まる）をスキップ
        if part.startswith('-'):
            # -pなどの後に引数が続く場合があるが、
            # mkdir/touchでは通常オプションの後に引数は不要
            continue

        # それ以外はパスとして扱う
        paths.append(part)

    return paths

def verify_mkdir_execution(command: str):
    """
    mkdir実行後の検証を行う

    Args:
        command: 実行されたコマンド

    Returns:
        dict: 検証結果のメッセージ（任意）
    """
    paths = extract_paths_from_command(command, "mkdir")

    if not paths:
        debug_log("mkdir: No paths found in command")
        return {}

    for path_str in paths:
        path_obj = Path(path_str)
        exists = path_obj.exists() and path_obj.is_dir()
        status = "created" if exists else "not_created"
        debug_log(f"mkdir: {path_str} -- {status}")

    return {}

def verify_touch_execution(command: str):
    """
    touch実行後の検証を行う

    Args:
        command: 実行されたコマンド

    Returns:
        dict: 検証結果のメッセージ（任意）
    """
    paths = extract_paths_from_command(command, "touch")

    if not paths:
        debug_log("touch: No paths found in command")
        return {}

    for path_str in paths:
        path_obj = Path(path_str)
        exists = path_obj.exists() and path_obj.is_file()
        status = "created" if exists else "not_created"
        debug_log(f"touch: {path_str} -- {status}")

    return {}

def main():
    try:
        # hook実行ログを記録
        log_hook_execution()
        debug_log("started.")

        # 標準入力からJSONを読み取り
        input_data = sys.stdin.read()

        if not input_data.strip():
            # 入力が空の場合は何もしない
            debug_log("No input data received.")
            print(json.dumps({}))
            debug_log("finished.")
            return

        # JSONをパース
        hook_data = json.loads(input_data)
        tool_input = hook_data.get("tool_input", {})
        command = tool_input.get("command", "")

        if not command:
            debug_log("No command found in tool_input")
            print(json.dumps({}))
            debug_log("finished.")
            return

        # コマンドに応じて検証実行
        result = {}
        if "mkdir" in command:
            result = verify_mkdir_execution(command)
        elif "touch" in command:
            result = verify_touch_execution(command)

        # 結果を出力（PostToolUseでは特に出力不要）
        output = {"hookSpecificOutput": result}
        print(json.dumps(output, ensure_ascii=False))

        debug_log("finished.")

    except json.JSONDecodeError as e:
        # JSONパースエラー
        error_msg = f"JSON decode error: {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        print(json.dumps({}))

    except Exception as e:
        # その他のエラー
        error_msg = f"Unexpected error in main(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        print(json.dumps({}))
        raise


if __name__ == "__main__":
    main()
