#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manage_timestamps.py
タイムスタンプの記録と管理を行うスクリプト

機能:
- 現在のタイムスタンプを記録
- 最新5件のみを保持（古いエントリを削除）
"""
import sys
from datetime import datetime
from pathlib import Path

# 1階層上（hooks/）のhook_excution_logger.pyをインポート
sys.path.insert(0, str(Path(__file__).parent.parent))
from hook_utils import log_hook_execution, get_path_from_config

def manage_timestamps():
    """
    タイムスタンプを記録し、最新5件のみを保持する
    """
    # タイムスタンプファイルのパスを取得
    timestamps_file = get_path_from_config("timestamps_file")

    # ディレクトリが存在しない場合は作成
    timestamps_file.parent.mkdir(parents=True, exist_ok=True)

    # 現在のタイムスタンプを生成
    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 既存のタイムスタンプを読み込む
    if timestamps_file.exists():
        with open(timestamps_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        lines = []

    # 新しいタイムスタンプを追加
    lines.append(f"{current_timestamp}\n")

    # 最新5件のみを保持
    lines = lines[-5:]

    # ファイルに書き込み
    with open(timestamps_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print("[completed] Timestamp recorded successfully")

def main():
    # hook実行ログを記録
    log_hook_execution()

    # タイムスタンプ管理を実行
    manage_timestamps()


if __name__ == '__main__':
    main()
