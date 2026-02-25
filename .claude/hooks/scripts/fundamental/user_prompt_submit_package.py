#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
user_prompt_submit_package.py
UserPromptSubmit hookで実行される全スクリプトを統合実行
"""
import sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import log_hook_execution, debug_log, get_path_from_config, get_user_message_from_stdin, sync_hook_utils_to_subdirs, rotate_debug_log, log_hook_error, log_python_env

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
    """UserPromptSubmitの全処理を順次実行"""
    try:
        # デバッグログのローテーション（2プロンプト分を保持）
        # この中でPROMPT_MARKER_0が出力される
        rotate_debug_log()

        # ロックファイルを削除（他のスクリプトの実行を許可）
        lock_file = get_path_from_config("ups_lock_file")
        lock_file.unlink(missing_ok=True)

        log_hook_execution
        debug_log("started.")

        # hook_log_ executions.log での改行の挿入
        log_file = get_path_from_config("log_file")
        with open(log_file, 'a') as f:
            f.write("\n")
    
        log_hook_execution()

        # hook_utils.py の同期
        sync_hook_utils_to_subdirs()

        # \project_structure トリガーチェック（一時的に表示）
        user_message = get_user_message_from_stdin()
        if user_message and "\\show_project_structure" in user_message:
            sys.path.insert(0, str(Path(__file__).parent))
            from session_start import show_project_structure
            show_project_structure.main()

        # user_prompt_messageを実行
        sys.path.insert(0, str(Path(__file__).parent))
        from user_prompt_submit import ups_fundamental_process
        ups_fundamental_process.main()

        # manage_timestampsを実行
        from user_prompt_submit import manage_timestamps
        manage_timestamps.main()

        # filecopy_triggerを実行
        from user_prompt_submit import filecopy_trigger
        filecopy_trigger.main(user_message)

        # ups_file_path_suggestを実行（ファイルパスサジェスト）
        try:
            from user_prompt_submit import ups_file_path_suggest
            # hook_dataを構築
            hook_data = {"prompt": user_message}
            ups_file_path_suggest.main(hook_data)
        except Exception as e:
            debug_log(f"Error in ups_file_path_suggest: {e}")

        debug_log("finished.\n")

    except Exception as e:
        error_msg = f"Unexpected error in main(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        # エラー時もロックファイルを削除
        lock_file.unlink(missing_ok=True)
        raise

if __name__ == "__main__":
    main()
