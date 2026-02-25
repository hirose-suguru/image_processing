#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
user_prompt_message.py
UserPromptSubmit hookで実行されるスクリプト
"""
import os
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from hook_utils import log_hook_execution, get_counter, increment_counter, get_project_root

def main():
    # hook実行ログを記録
    log_hook_execution()

    # プロジェクトルート取得（hook_utils.pyの関数を使用）
    project_root = get_project_root()

    # ディレクトリを移動
    os.chdir(project_root)
    print(f"Working directory changed to: {project_root}")

    # カウンターをチェック（3回に1回だけメッセージ表示）
    message_counter = get_counter("read_claude_reminder")

    if message_counter == 0:
        #print("Read(CLAUDE.md) を実行してください。")
        print("必要に応じて context7 MCP を活用してください。")

    # カウンターをインクリメント（0 → 1 → 2 → 0）
    increment_counter("read_claude_reminder")

    


if __name__ == "__main__":
    main()
