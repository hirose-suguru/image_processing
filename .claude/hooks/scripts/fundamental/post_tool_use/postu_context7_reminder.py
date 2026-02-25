#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
postu_context7_reminder.py
Context7使用後に知見記録を促すリマインダー
"""
import sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import debug_log, log_hook_execution, get_tool_data_from_stdin, log_hook_error

except ImportError as e:
    error_msg = f"Failed to import hook_utils: {e}"
    # stdoutとstderrに出力のみ（ファイル書き込みはしない）
    print(f"[HOOK ERROR] {error_msg}")
    print(f"[HOOK ERROR] Script: {__file__}")
    print(f"[HOOK ERROR] sys.path: {sys.path}")
    sys.stderr.write(f"[HOOK ERROR] {error_msg}\n")
    sys.stderr.write(f"[HOOK ERROR] Script: {__file__}\n")
    sys.exit(1)

def show_reminder():
    """Context7使用後のリマインダーを表示"""
    message = "何かしらの知見が得られた場合は`change_key_v4/ahk_v4_obsidian/01_knowledge/references` に`.md` の形で記載してください。"
    print(f"\n{message}")
    debug_log(f"Context7 reminder displayed: {message}")

def main(hook_data: dict = None):
    """
    メイン処理

    Args:
        hook_data: フックデータ（tool_name, tool_input等）
                  - post_tool_use_package.pyから呼ばれる場合: hook_dataを渡す（データ再利用）
                  - スタンドアロン実行の場合: Noneのままでstdinから読み込む
    """
    try:
        # hook_dataが渡されていない場合はstdinから取得
        if hook_data is None:
            log_hook_execution()
            hook_data = get_tool_data_from_stdin()
            if not hook_data:
                debug_log("ツールデータの取得に失敗したため終了")
                return

        debug_log("started.")

        tool_name = hook_data.get("tool_name", "")

        # Context7関連のツールかチェック
        if tool_name in ["mcp__context7__resolve-library-id", "mcp__context7__get-library-docs"]:
            debug_log(f"Context7 tool detected: {tool_name}")
            show_reminder()
        else:
            debug_log(f"Not a Context7 tool: {tool_name}")

        debug_log("finished.")


    except Exception as e:
        error_msg = f"Unexpected error in main(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise

if __name__ == "__main__":
    # スタンドアロン実行時
    main()  # hook_data=Noneなのでstdinから読み込む
