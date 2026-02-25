#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ss_init_bash_statistics.py
SessionStart hookで実行されるBash統計初期化スクリプト
"""
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from hook_utils import log_hook_execution, debug_log, get_path_from_config, get_project_root, load_json5

def generate_session_id() -> str:
    """
    新しいセッションIDを生成

    Returns:
        セッションID（例: "20251224_103000"）
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def init_bash_statistics_file():
    """
    bash_statistics.json5ファイルの初期化または新規セッション追加
    """
    try:
        bash_stats_file = get_path_from_config("bash_statistics_file")
        project_root = get_project_root()
        bash_stats_path = project_root / bash_stats_file

        # 新しいセッションIDを生成
        new_session_id = generate_session_id()
        current_time = datetime.now().isoformat()

        # ファイルが存在する場合は読み込み、存在しない場合は初期化
        if bash_stats_path.exists():
            try:
                stats = load_json5(bash_stats_path)
            except Exception as e:
                debug_log(f"Failed to load bash_statistics.json5: {e}, creating new file")
                stats = {}
        else:
            stats = {}

        # 初期構造を設定
        if "sessions" not in stats:
            stats["sessions"] = []
        if "aggregated" not in stats:
            stats["aggregated"] = {}
        if "summary" not in stats:
            stats["summary"] = {
                "total_sessions": 0,
                "total_executions": 0,
                "unique_commands": 0,
                "total_tokens": 0,
                "top_5_commands": []
            }

        # 新しいセッションを追加
        new_session = {
            "session_id": new_session_id,
            "start_time": current_time,
            "commands": {}
        }
        stats["sessions"].insert(0, new_session)  # 最新のセッションを先頭に挿入

        # 10セッションを超えた場合は古いものを削除
        if len(stats["sessions"]) > 10:
            removed_session = stats["sessions"].pop()  # 最古のセッションを削除
            debug_log(f"Removed old session: {removed_session.get('session_id')}")

        # メタデータ更新
        stats["last_updated"] = current_time
        stats["current_session_id"] = new_session_id

        # ファイルに書き込み
        bash_stats_path.parent.mkdir(parents=True, exist_ok=True)
        with open(bash_stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        debug_log(f"Initialized bash statistics for session: {new_session_id}")

    except Exception as e:
        debug_log(f"Error in init_bash_statistics_file: {e}")

def main():
    """
    メイン処理
    """
    log_hook_execution()
    init_bash_statistics_file()

if __name__ == "__main__":
    main()
