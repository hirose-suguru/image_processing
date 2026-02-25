#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
postu_bash_logger.py
PostToolUse hookで実行されるBashコマンド専用ログ記録スクリプト
"""
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from hook_utils import log_hook_execution, debug_log, get_path_from_config, get_tool_data_from_stdin, estimate_tokens, get_project_root, load_json5

def build_bash_log_entry(hook_data: dict) -> str:
    """
    Bashツール実行データからログエントリを構築

    Args:
        hook_data: stdinから取得したツール実行データ

    Returns:
        フォーマット済みログエントリ
    """
    tool_input = hook_data.get("tool_input", {})
    tool_response = hook_data.get("tool_response", {})
    cwd = hook_data.get("cwd", "")

    command = tool_input.get("command", "")
    stdout = tool_response.get("stdout", "")
    stderr = tool_response.get("stderr", "")
    exit_code = tool_response.get("exit_code", 0)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_lines = [
        f"[{timestamp}]",
        f"CWD: {cwd}",
        f"Command: {command}",
    ]

    if stdout:
        log_lines.append(f"Stdout:\n{stdout}")

    if stderr:
        log_lines.append(f"Stderr:\n{stderr}")

    log_lines.append(f"Exit Code: {exit_code}")
    log_lines.append("")  # 区切り用の空行

    return "\n".join(log_lines)

def write_bash_log(log_entry: str, bash_history_file: Path):
    """
    ログエントリをファイルに書き込み

    Args:
        log_entry: ログエントリ
        log_file: ログファイルのパス
    """
    try:
        # ディレクトリが存在しない場合は作成
        bash_history_file.parent.mkdir(parents=True, exist_ok=True)

        # ログファイルに追記（UTF-8, BOMなし）
        with open(bash_history_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

        #debug_log(f"Bashログ記録完了: {bash_history_file}")

    except Exception as e:
        debug_log(f"Bashログファイル書き込みエラー: {str(e)}")

def update_bash_statistics(hook_data: dict):
    """
    Bash統計情報を更新

    Args:
        hook_data: ツール実行データ
    """
    try:
        bash_stats_file = get_path_from_config("bash_statistics_file")
        project_root = get_project_root()
        bash_stats_path = project_root / bash_stats_file

        if not bash_stats_path.exists():
            debug_log("bash_statistics.json5 does not exist, skipping statistics update")
            return

        # 統計ファイルを読み込み
        try:
            stats = load_json5(bash_stats_path)
        except Exception as e:
            debug_log(f"Failed to load bash_statistics.json5: {e}")
            return

        # 現在のセッションIDを取得
        current_session_id = stats.get("current_session_id")
        if not current_session_id:
            debug_log("No current_session_id found, skipping statistics update")
            return

        # コマンド情報を取得
        tool_input = hook_data.get("tool_input", {})
        tool_response = hook_data.get("tool_response", {})
        command = tool_input.get("command", "")
        stdout = tool_response.get("stdout", "")
        stderr = tool_response.get("stderr", "")

        if not command:
            debug_log("No command found, skipping statistics update")
            return

        # トークン数を推定
        input_tokens = estimate_tokens(command)
        output_tokens = estimate_tokens(stdout + stderr)
        total_tokens = input_tokens + output_tokens

        # 現在のセッションを探す
        current_session = None
        for session in stats.get("sessions", []):
            if session.get("session_id") == current_session_id:
                current_session = session
                break

        if not current_session:
            debug_log(f"Current session {current_session_id} not found")
            return

        # セッションのコマンド統計を更新
        if "commands" not in current_session:
            current_session["commands"] = {}

        if command not in current_session["commands"]:
            current_session["commands"][command] = {
                "count": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            }

        cmd_stats = current_session["commands"][command]
        cmd_stats["count"] += 1
        cmd_stats["input_tokens"] += input_tokens
        cmd_stats["output_tokens"] += output_tokens
        cmd_stats["total_tokens"] += total_tokens

        # aggregatedを再計算
        aggregated = {}
        total_executions = 0
        total_tokens_sum = 0

        for session in stats.get("sessions", []):
            for cmd, cmd_data in session.get("commands", {}).items():
                if cmd not in aggregated:
                    aggregated[cmd] = {
                        "total_count": 0,
                        "total_input_tokens": 0,
                        "total_output_tokens": 0,
                        "total_tokens": 0,
                        "avg_tokens_per_execution": 0
                    }

                aggregated[cmd]["total_count"] += cmd_data.get("count", 0)
                aggregated[cmd]["total_input_tokens"] += cmd_data.get("input_tokens", 0)
                aggregated[cmd]["total_output_tokens"] += cmd_data.get("output_tokens", 0)
                aggregated[cmd]["total_tokens"] += cmd_data.get("total_tokens", 0)

                total_executions += cmd_data.get("count", 0)
                total_tokens_sum += cmd_data.get("total_tokens", 0)

        # 平均トークン数を計算
        for cmd, cmd_data in aggregated.items():
            if cmd_data["total_count"] > 0:
                cmd_data["avg_tokens_per_execution"] = int(cmd_data["total_tokens"] / cmd_data["total_count"])

        stats["aggregated"] = aggregated

        # トップ5コマンドを計算（トークン消費量順）
        sorted_commands = sorted(
            aggregated.items(),
            key=lambda x: x[1]["total_tokens"],
            reverse=True
        )
        top_5_commands = [cmd for cmd, _ in sorted_commands[:5]]

        # summaryを更新
        stats["summary"] = {
            "total_sessions": len(stats.get("sessions", [])),
            "total_executions": total_executions,
            "unique_commands": len(aggregated),
            "total_tokens": total_tokens_sum,
            "top_5_commands": top_5_commands
        }

        # last_updatedを更新
        stats["last_updated"] = datetime.now().isoformat()

        # ファイルに書き込み
        with open(bash_stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        debug_log(f"Updated bash statistics: {command} (+{total_tokens} tokens)")

    except Exception as e:
        debug_log(f"Error in update_bash_statistics: {e}")

def main(hook_data: dict = None):
    """
    Bashログ記録のメイン処理

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

    # Bashツールであることを確認
    tool_name = hook_data.get("tool_name", "")
    if tool_name != "Bash":
        debug_log(f"Not a Bash tool ({tool_name}), skipping bash_logger")
        return

    # ログファイルパスを取得
    bash_history_file = get_path_from_config("bash_history_file")

    # ログエントリを構築
    log_entry = build_bash_log_entry(hook_data)

    # ログファイルに書き込み
    write_bash_log(log_entry, bash_history_file)

    # 統計情報を更新
    update_bash_statistics(hook_data)

if __name__ == "__main__":
    # スタンドアロン実行時
    main()  # hook_data=Noneなのでstdinから読み込む
