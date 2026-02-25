#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
session_start_package.py
SessionStart hookで実行される全スクリプトを統合実行
"""
import sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import log_hook_execution, debug_log, sync_hook_utils_to_subdirs, log_hook_error, log_python_env

except ImportError as e:
    error_msg = f"Failed to import hook_utils: {e}"
    # stdoutとstderrに出力のみ（ファイル書き込みはしない）
    print(f"[HOOK ERROR] {error_msg}")
    print(f"[HOOK ERROR] Script: {__file__}")
    print(f"[HOOK ERROR] sys.path: {sys.path}")
    sys.stderr.write(f"[HOOK ERROR] {error_msg}\n")
    sys.stderr.write(f"[HOOK ERROR] Script: {__file__}\n")
    sys.exit(1)

def main():
    """SessionStartの全処理を順次実行"""
    try:
        log_hook_execution()
        debug_log("started.")

        # セッション開始時にPython環境をログに記録
        log_python_env()

        # 最初にhook_utils.pyを同期（最新版を使えるようにする）
        sync_hook_utils_to_subdirs()

        # session_start_messageを実行
        sys.path.insert(0, str(Path(__file__).parent))
        from session_start import ss_fundamental_process
        ss_fundamental_process.main()

        # show_project_structureを実行
        from session_start import ss_show_project_structure
        ss_show_project_structure.main()

        # すべてのhook toggleをリセット
        from session_start import ss_reset_hook_toggle
        ss_reset_hook_toggle.main()

        # Bash統計の初期化
        from session_start import ss_init_bash_statistics
        ss_init_bash_statistics.main()

        debug_log("finished.\n")

    except Exception as e:
        error_msg = f"Unexpected error in main(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise

if __name__ == "__main__":
    main()
