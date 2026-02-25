#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stop_message.py
Stop hookで実行されるスクリプト
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from hook_utils import log_hook_execution, get_project_root

def main():
    # hook実行ログを記録
    log_hook_execution()

    # プロジェクトルートに移動（次回SessionStartのため）
    project_root = get_project_root()
    os.chdir(project_root)


if __name__ == "__main__":
    main()
