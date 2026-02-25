#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
session_start_message.py
SessionStart hookで実行されるスクリプト
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from hook_utils import log_hook_execution, reset_counter, clear_file, get_path_from_config

def main():
    # hook実行ログを記録
    log_hook_execution()

    # ログファイルをクリア
    clear_file(get_path_from_config("log_file"))
    clear_file(get_path_from_config("debug_file"))
    clear_file(get_path_from_config("error_file"))
    clear_file(get_path_from_config("timestamps_file"))
    clear_file(get_path_from_config("focus_wezterm_log"))

    # read_claude_reminderカウンターをリセット
    reset_counter("read_claude_reminder")

    #print("Read(CLAUDE.md) を実行してください。")

if __name__ == "__main__":
    main()
