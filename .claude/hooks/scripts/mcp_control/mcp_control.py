#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mcp_control.py
UserPromptSubmit hookで実行される汎用MCP制御スクリプト

使用方法:
    mcp_control_config.jsonに定義されたトリガーをプロンプトに含めると、
    対応するMCPの有効化/無効化コマンドが実行されます

例:
    プロンプトに "\serena" → Serena MCPをプロジェクトスコープでインストール
    プロンプトに "\serena_stop" → Serena MCPを削除

動作:
    1. mcp_control_config.jsonから全MCP設定を読み込み
    2. ユーザーメッセージから該当するトリガーを検出
    3. enable/disableコマンドを実行
"""
import sys
from pathlib import Path
import subprocess

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import log_hook_execution, debug_log, get_user_message_from_stdin, get_project_root, get_path_from_config, detect_trigger, log_hook_error, load_json5

except ImportError as e:
    error_msg = f"Failed to import hook_utils: {e}"
    # stdoutとstderrに出力のみ（ファイル書き込みはしない）
    print(f"[HOOK ERROR] {error_msg}")
    print(f"[HOOK ERROR] Script: {__file__}")
    print(f"[HOOK ERROR] sys.path: {sys.path}")
    sys.stderr.write(f"[HOOK ERROR] {error_msg}\n")
    sys.stderr.write(f"[HOOK ERROR] Script: {__file__}\n")
    sys.exit(1)

def load_mcp_config() -> dict:
    """MCP制御設定を読み込む"""
    config_path = get_path_from_config("mcp_control_file")

    try:
        config = load_json5(config_path)
        return config
    except Exception as e:
        debug_log(f"Failed to load MCP config: {e}")
        return {}

def execute_mcp_command(mcp_name: str, command_template: str, is_enable: bool):
    """MCPコマンドを実行"""
    action = "enable" if is_enable else "disable"
    debug_log(f"{action.capitalize()}ing {mcp_name} MCP...")

    try:
        # {project_root}を実際のパスで置換
        project_root = get_project_root()
        cmd_str = command_template.replace("{project_root}", str(project_root))

        debug_log(f"Running command: {cmd_str}")
        # Windows環境ではshell=Trueが必要（PATHに登録されたコマンドを実行するため）
        result = subprocess.run(cmd_str, capture_output=True, text=True, shell=True)

        if result.returncode == 0:
            debug_log(f"{mcp_name} MCP {action}d successfully")
            print(f"✅ {mcp_name} MCPが{'有効化' if is_enable else '無効化'}されました")
            print("🔄 Claude Codeを再起動してください（Ctrl+Shift+P → 'Reload Window'）")
        else:
            debug_log(f"{mcp_name} MCP {action} failed: {result.stderr}")
            print(f"❌ {mcp_name} MCPの{'有効化' if is_enable else '無効化'}に失敗しました: {result.stderr}")

    except Exception as e:
        debug_log(f"{mcp_name} MCP {action} error: {e}")
        print(f"❌ エラーが発生しました: {e}")

def main(user_message: str = None):
    """MCP制御のメイン処理

    Args:
        user_message: ユーザーメッセージ（Noneの場合はstdinから取得）
    """
    try:
        # ユーザーメッセージを取得
        if user_message is None:
            user_message = get_user_message_from_stdin()
        if not user_message:
            return

        # MCP設定を読み込み
        config = load_mcp_config()
        if not config:
            return

        # 各MCPのトリガーをチェック
        triggered = False
        for mcp_name, mcp_config in config.items():
            if mcp_name == "comment":
                continue

            enable_trigger = mcp_config.get("enable_trigger")
            disable_trigger = mcp_config.get("disable_trigger")

            # disable_triggerを優先チェック（独立した単語として検出）
            if disable_trigger and detect_trigger(user_message, disable_trigger):
                if not triggered:
                    # 最初のトリガー検知時のみログ開始
                    debug_log("started.")
                    log_hook_execution()
                debug_log(f"{disable_trigger} trigger detected, disabling {mcp_name} MCP")
                disable_cmd = mcp_config.get("disable_command")
                if disable_cmd:
                    execute_mcp_command(mcp_name, disable_cmd, is_enable=False)
                    triggered = True

            # enable_triggerをチェック（独立した単語として検出）
            elif enable_trigger and detect_trigger(user_message, enable_trigger):
                if not triggered:
                    # 最初のトリガー検知時のみログ開始
                    debug_log("started.")
                    log_hook_execution()
                debug_log(f"{enable_trigger} trigger detected, enabling {mcp_name} MCP")
                enable_cmd = mcp_config.get("enable_command")
                if enable_cmd:
                    execute_mcp_command(mcp_name, enable_cmd, is_enable=True)
                    triggered = True

        # トリガーが検知されなかった場合は静かに終了
        if not triggered:
            return

        debug_log("finished.")


    except Exception as e:
        error_msg = f"Unexpected error in main(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise

if __name__ == "__main__":
    main()
