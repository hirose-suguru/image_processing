#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
develop_user_prompt_submit_package.py
UserPromptSubmit hookで実行されるdevelopモード統合パッケージ

トリガー:
  - \develop: トグルON + メッセージ表示 + 構造表示
  - \show_dev_structure: 構造表示のみ（トグル無関係）
  - \develop_stop: トグルOFF

トグルON時の動作:
  - split_file.py の処理を毎回実行
"""
import sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import log_hook_execution, debug_log, get_hook_toggle, set_hook_toggle, detect_trigger, log_hook_error, get_user_message_from_stdin, wait_for_lock_release, get_path_from_config

except ImportError as e:
    error_msg = f"Failed to import hook_utils: {e}"
    # stdoutとstderrに出力のみ（ファイル書き込みはしない）
    print(f"[HOOK ERROR] {error_msg}")
    print(f"[HOOK ERROR] Script: {__file__}")
    print(f"[HOOK ERROR] sys.path: {sys.path}")
    sys.stderr.write(f"[HOOK ERROR] {error_msg}\n")
    sys.stderr.write(f"[HOOK ERROR] Script: {__file__}\n")
    sys.exit(1)

# 各スクリプトをインポート
try:
    sys.path.insert(0, str(Path(__file__).parent))
    import split_file
    import show_dev_structure
    import develop_ups_message
except ImportError as e:
    sys.stderr.write(f"[HOOK ERROR] Failed to import develop scripts: {e}")
    sys.stderr.write(f"[HOOK ERROR] sys.path: {sys.path}")
    sys.exit(1)

def main():

    try:
        """developモードの統合制御処理"""
        # fundamental/user_prompt_submit_package.py の完了を待機
        ups_lock_file = get_path_from_config("ups_lock_file")
        wait_for_lock_release(ups_lock_file)

        # ユーザーメッセージを取得（stdinキャッシュ対応）
        user_message = get_user_message_from_stdin()
        if not user_message:
            return

        # \develop_stop を検知したらトグルをOFFにして終了
        if user_message and detect_trigger(user_message, "\\develop_stop"):
            log_hook_execution()
            debug_log("started.")
            set_hook_toggle("develop", False)
            debug_log("finished.")
            return

        # \develop を検知
        develop_triggered = user_message and detect_trigger(user_message, "\\develop")
        if develop_triggered:
            set_hook_toggle("develop", True)

        # \show_dev_structure を検知
        show_structure_triggered = user_message and detect_trigger(user_message, "\\show_dev_structure")

        # トグルチェック
        toggle_on = get_hook_toggle("develop")

        # 何も処理しない場合は早期リターン
        if not develop_triggered and not show_structure_triggered and not toggle_on:
            return

        # ここから実際に処理を行う
        log_hook_execution()
        debug_log("started.")

        if develop_triggered:
            debug_log("\\develop trigger detected, enabling toggle")

        if show_structure_triggered:
            debug_log("\\show_dev_structure trigger detected")

        # トリガー検出時の処理
        if develop_triggered:
            # \develop: メッセージ表示 + 構造表示
            develop_ups_message.main()
            show_dev_structure.main()
        elif show_structure_triggered:
            # \show_dev_structure: 構造表示のみ
            show_dev_structure.main()

        # トグルがONの場合はsplit_file処理を実行
        if toggle_on:
            debug_log("develop toggle is ON, running split_file")
            split_file.main()

        debug_log("finished.")


    except Exception as e:
        error_msg = f"Unexpected error in main(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise

if __name__ == "__main__":
    main()
