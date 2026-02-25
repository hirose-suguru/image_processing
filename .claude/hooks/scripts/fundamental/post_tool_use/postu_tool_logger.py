#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
postu_tool_logger.py
PostToolUse hookで実行されるツール使用ログ記録スクリプト
"""
import sys
import json
import os
import re
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from hook_utils import log_hook_execution, debug_log, get_path_from_config, get_tool_data_from_stdin

#ファイルの読み込み
tool_history_file = get_path_from_config("tool_history_file")

# ディレクトリが存在しない場合は作成
tool_history_file.parent.mkdir(parents=True, exist_ok=True)

def format_tool_input(tool_input: dict, max_length: int = 1000) -> list:
    """
    ツール入力をフォーマット
    Args:
        tool_input: ツール入力データ
        max_length: 最大文字数

    Returns:
        フォーマット済みログ行のリスト
    """
    if not tool_input:
        return []

    lines = ["Tool Input:"]
    input_json = json.dumps(tool_input, ensure_ascii=False)
    if len(input_json) > max_length:
        input_json = input_json[:max_length] + "..."
    lines.append(f"  {input_json}")
    return lines

def format_tool_response(tool_response: dict, max_length: int = 500) -> list:
    """
    ツールレスポンスをフォーマット
    Args:
        tool_response: ツールレスポンスデータ
        max_length: 最大文字数

    Returns:
        フォーマット済みログ行のリスト
    """
    if not tool_response:
        return []

    lines = ["Tool Response:"]

    # Bashコマンドのstdoutを処理
    if "stdout" in tool_response:
        output = tool_response["stdout"]
        # 連続する空行を1つにまとめる（可読性向上）
        output = re.sub(r'\n\n+', '\n\n', output)
        # 文字数制限
        if len(output) > max_length:
            output = output[:max_length] + "..."
        lines.append(f"  Output: {output}")

    # 終了コードを処理
    if "exit_code" in tool_response:
        lines.append(f"  Exit Code: {tool_response['exit_code']}")

    # stdoutがない場合はJSON形式で記録
    if "stdout" not in tool_response:
        response_json = json.dumps(tool_response, ensure_ascii=False)
        if len(response_json) > max_length:
            response_json = response_json[:max_length] + "..."
        lines.append(f"  {response_json}")

    return lines

def build_log_entry(hook_data: dict) -> str:
    """
    ツール実行データからログエントリを構築
    Args:
        hook_data: stdinから取得したツール実行データ

    Returns:
        フォーマット済みログエントリ
    """
    tool_name = hook_data.get("tool_name", "Unknown")
    tool_input = hook_data.get("tool_input", {})
    tool_response = hook_data.get("tool_response", {})
    cwd = hook_data.get("cwd", "")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_lines = [
        f"[{timestamp}] Tool: {tool_name}",
        f"作業ディレクトリ: {cwd}",
    ]

    # ツール入力を追加
    log_lines.extend(format_tool_input(tool_input))

    # ツールレスポンスを追加
    log_lines.extend(format_tool_response(tool_response))

    log_lines.append("")  # 区切り用の空行

    return "\n".join(log_lines)

def write_log(log_entry: str, tool_history_file: Path):
    """
    ログエントリをファイルに書き込み
    Args:
        log_entry: ログエントリ
        log_file: ログファイルのパス
    """
    try:

        # ログファイルに追記（UTF-8, BOMなし）
        with open(tool_history_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

        #debug_log(f"ログ記録完了: {tool_history_file}")

    except Exception as e:
        debug_log(f"ログファイル書き込みエラー: {str(e)}")
        print(f"ログファイルの書き込みに失敗しました: {e}", file=sys.stderr)

def main(hook_data: dict = None):
    """
    ツールログ記録のメイン処理

    Args:
        hook_data: ツール実行データ（省略時はstdinから取得）
                  - post_tool_use_package.pyから呼ばれる場合: hook_dataを渡す（データ再利用）
                  - スタンドアロン実行の場合: Noneのままでstdinから読み込む
    """
    # hook_dataが渡されていない場合はstdinから取得
    if hook_data is None:
        log_hook_execution()
        hook_data = get_tool_data_from_stdin()
        if not hook_data:
            debug_log("ツールデータの取得に失敗したため終了")
            return

    # ログエントリを構築
    log_entry = build_log_entry(hook_data)

    # ログファイルに書き込み
    write_log(log_entry, tool_history_file)

if __name__ == "__main__":
    main()  # hook_data=Noneなのでstdinから読み込む
