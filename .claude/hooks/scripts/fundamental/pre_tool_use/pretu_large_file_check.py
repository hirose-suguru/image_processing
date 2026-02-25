#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pretu_large_file_check.py
大きなファイルのRead操作を検出し、Codex委託を推奨するhook
"""

import sys
from typing import Optional
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import log_hook_execution, debug_log, get_path_from_config, log_hook_error, load_json5, stop_tool_use

except ImportError as e:
    error_msg = f"Failed to import hook_utils: {e}"
    print(f"[HOOK ERROR] {error_msg}")
    print(f"[HOOK ERROR] Script: {__file__}")
    print(f"[HOOK ERROR] sys.path: {sys.path}")
    sys.stderr.write(f"[HOOK ERROR] {error_msg}\n")
    sys.stderr.write(f"[HOOK ERROR] Script: {__file__}\n")
    sys.exit(1)


def load_codex_config() -> dict:
    """Codex設定ファイルを読み込む"""
    try:
        config_path = get_path_from_config("codex_config")
        return load_json5(config_path)
    except Exception as e:
        debug_log(f"Failed to load codex_config: {e}")
        return {
            "large_file_threshold": 1000,
            "enabled": True
        }


def get_skip_reason(tool_data: dict) -> Optional[str]:
    """スキップ理由を返す（Noneなら続行）"""
    if not tool_data:
        return "No tool data received"

    tool_name = tool_data.get("tool_name", "")
    if tool_name != "Read":
        return f"Skipping: tool is {tool_name}, not Read"

    # offset または limit が指定されている場合は部分読み込みなのでスキップ
    tool_input = tool_data.get("tool_input", {})
    if tool_input.get("offset") is not None or tool_input.get("limit") is not None:
        return "Skipping: offset or limit specified (partial read)"

    return None


def get_target_file_path(tool_data: dict) -> Optional[Path]:
    """ツール入力から対象ファイルのパスを取得"""
    file_path_str = tool_data.get("tool_input", {}).get("file_path", "")
    if not file_path_str:
        return None
    return Path(file_path_str)


def is_binary_file(file_path: Path) -> bool:
    """バイナリファイル判定"""
    binary_extensions = {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.pdf',
        '.zip', '.tar', '.gz', '.exe', '.dll', '.so', '.dylib',
        '.woff', '.woff2', '.ttf', '.eot', '.mp3', '.mp4', '.wav'
    }
    return file_path.suffix.lower() in binary_extensions


def count_file_lines(file_path: Path) -> int:
    """ファイルの行数をカウント"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except Exception as e:
        debug_log(f"Failed to count lines in {file_path}: {e}")
        return 0


def build_block_message(file_path: Path, line_count: int) -> str:
    """ブロック時のメッセージを生成"""
    return f"""[BLOCKED] 大きなファイルの読み込み\n
{file_path.name}は {line_count} 行あります。\n
コンテキストを節約するため、/codex-execute Skillを使用してください：\n
または、offsetとlimitパラメータを指定して必要な部分のみ読み込んでください。"""


def execute(tool_data: dict):
    """
    大きなファイルのReadを検出してCodex委託を推奨

    Args:
        tool_data: パッケージから渡されたツールデータ

    Note:
        ブロック時は stop_tool_use() で終了するため戻り値なし
    """
    try:
        log_hook_execution()
        # debug_log("started.")

        skip_reason = get_skip_reason(tool_data)
        if skip_reason:
            # debug_log(skip_reason)
            return
 
        # 設定を読み込む
        config = load_codex_config()

        # 機能が無効なら何もしない
        if not config.get("enabled", True):
            # debug_log("Codex delegation is disabled")
            return

        threshold = config.get("large_file_threshold", 1000)

        # ファイルパスを取得
        file_path = get_target_file_path(tool_data)
        if not file_path:
            debug_log("No file_path in tool_input")
            return

        # ファイルが存在しない場合はスキップ（Readツールがエラーを出す）
        if not file_path.exists():
            # debug_log(f"File does not exist: {file_path}")
            return

        # バイナリファイルはスキップ
        if is_binary_file(file_path):
            # debug_log(f"Skipping binary file: {file_path}")
            return

        # 行数をカウント
        line_count = count_file_lines(file_path)
        # debug_log(f"File {file_path.name} has {line_count} lines (threshold: {threshold})")

        # 閾値を超えている場合はブロック
        if line_count > threshold:
            debug_log("started.")
            debug_log(f"BLOCKED: {file_path.name} ({line_count} lines > threshold {threshold})")
            debug_log("finished.")
            stop_tool_use(build_block_message(file_path, line_count))

        # debug_log("finished.")

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
