#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stop_package.py
Stop hookで実行される全スクリプトを統合実行
"""
import sys
import time
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import log_hook_execution, debug_log, log_hook_error, get_path_from_config

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
    """Stopの全処理を順次実行"""
    try:
        log_hook_execution()
        debug_log("started.")

        # stop_messageを実行
        sys.path.insert(0, str(Path(__file__).parent))
        from stop import stop_fundamental_process
        stop_fundamental_process.main()

        # stop_notificationを実行（タスク完了通知）
        # 3秒遅延：Claude Codeの回答終了とターミナル描画の間のラグを考慮
        debug_log("Waiting 3 seconds before notification...")
        time.sleep(4)
        from stop import stop_notification
        stop_notification.main()

        # 次のセッション用にロックファイルを作成
        lock_file = get_path_from_config("ups_lock_file")
        lock_file.touch()
        debug_log("Lock file created for next session")

        debug_log("finished.")


    except Exception as e:
        error_msg = f"Unexpected error in main(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise

if __name__ == "__main__":
    main()
