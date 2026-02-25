#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
filecopy_trigger.py
UserPromptSubmit hook - \\filecopy トリガーを検知してBash cpコマンドの使用を促す
"""
import sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import log_hook_execution, debug_log, get_user_message_from_stdin, detect_trigger, log_hook_error

except ImportError as e:
    error_msg = f"Failed to import hook_utils: {e}"
    # stdoutとstderrに出力のみ（ファイル書き込みはしない）
    print(f"[HOOK ERROR] {error_msg}")
    print(f"[HOOK ERROR] Script: {__file__}")
    print(f"[HOOK ERROR] sys.path: {sys.path}")
    sys.stderr.write(f"[HOOK ERROR] {error_msg}\n")
    sys.stderr.write(f"[HOOK ERROR] Script: {__file__}\n")
    sys.exit(1)

def main(user_message=None):
    """メイン処理"""
    try:
        log_hook_execution()
        # debug_log("started.")

        # user_messageが渡されていない場合はstdinから取得
        if user_message is None:
            user_message = get_user_message_from_stdin()

        if not user_message:
            debug_log("No user message found")
            return

        if detect_trigger(user_message, "\\filecopy"):
            debug_log("\\filecopy trigger detected")
            print("📋 \\filecopy トリガー検知")
            print("  - ReadやGrepツールでファイルの中身を確認しなくてよいので、Bashのcpコマンドを使用してコピーしてください。\n")
        else:
            return

        debug_log("finished.")



    except Exception as e:
        error_msg = f"Unexpected error in main(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise

if __name__ == "__main__":
    main()
