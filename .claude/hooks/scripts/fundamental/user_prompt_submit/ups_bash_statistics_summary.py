#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ups_bash_statistics_summary.py
UserPromptSubmit hookで実行されるBash統計サマリー表示スクリプト
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from hook_utils import log_hook_execution, debug_log, get_path_from_config, get_project_root, load_json5

def format_bash_statistics_summary(stats: dict) -> str:
    """
    Bash統計情報をフォーマットして表示用文字列を生成

    Args:
        stats: 統計データ

    Returns:
        フォーマット済みサマリー文字列
    """
    summary = stats.get("summary", {})
    aggregated = stats.get("aggregated", {})

    if not summary or not aggregated:
        return ""

    lines = []
    lines.append("Bash Command Statistics (Last 10 Sessions)")
    lines.append(f"Total Sessions: {summary.get('total_sessions', 0)}")
    lines.append(f"Total Executions: {summary.get('total_executions', 0)}")
    lines.append(f"Unique Commands: {summary.get('unique_commands', 0)}")
    lines.append(f"Total Tokens: {summary.get('total_tokens', 0):,}")
    lines.append("")

    # トップ5コマンドの詳細を表示
    top_5_commands = summary.get("top_5_commands", [])
    if top_5_commands:
        lines.append("Top 5 Commands by Token Consumption:")

        for i, cmd in enumerate(top_5_commands, 1):
            if cmd in aggregated:
                cmd_data = aggregated[cmd]
                total_count = cmd_data.get("total_count", 0)
                total_tokens = cmd_data.get("total_tokens", 0)
                avg_tokens = cmd_data.get("avg_tokens_per_execution", 0)

                # コマンドが長い場合は省略
                display_cmd = cmd if len(cmd) <= 40 else cmd[:37] + "..."

                lines.append(f"{i}. {display_cmd}")
                lines.append(f"   Executions: {total_count}, Total Tokens: {total_tokens:,}, Avg: {avg_tokens}")

    lines.append("")

    return "\n".join(lines)

def main():
    """
    Bash統計サマリーを表示
    """
    try:
        log_hook_execution()

        bash_stats_file = get_path_from_config("bash_statistics_file")
        project_root = get_project_root()
        bash_stats_path = project_root / bash_stats_file

        if not bash_stats_path.exists():
            debug_log("bash_statistics.json5 does not exist, skipping summary display")
            return

        # 統計ファイルを読み込み
        try:
            stats = load_json5(bash_stats_path)
        except Exception as e:
            debug_log(f"Failed to load bash_statistics.json5: {e}")
            return

        # サマリーをフォーマット
        summary_text = format_bash_statistics_summary(stats)

        if summary_text:
            print(summary_text)

    except Exception as e:
        debug_log(f"Error in ups_bash_statistics_summary: {e}")

if __name__ == "__main__":
    main()
