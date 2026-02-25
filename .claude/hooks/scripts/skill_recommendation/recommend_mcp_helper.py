"""
recommend_mcp_helper.py
MCP関連のキーワードを検出してmcp-helper Skillの使用を推奨
UserPromptSubmit hookで実行
"""
import sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import log_hook_execution, get_user_message_from_stdin, detect_keywords, debug_log, log_hook_error

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
    try:
        # hook実行ログを記録
        log_hook_execution()

        # ユーザーメッセージを取得
        user_message = get_user_message_from_stdin()
        if not user_message:
            return

        # キーワード検出
        found, detected = detect_keywords(
            user_message=user_message,
            keywords=["mcp", "MCP", "追加", "削除", "設定", "サーバー", "server", "インストール", "install", "設定ファイル", "config", ".mcp.json"]
        )

        if not found:
            return

        # メッセージ出力
        debug_log("推奨メッセージ出力開始")
        print()
        print("=" * 20)
        print("💡 Skill推奨: mcp-helper")
        print("=" * 20)
        print()
        print(f"検出されたキーワード: {', '.join(detected)}")
        print()
        print("MCPに関する操作を行う場合、mcp-helper Skillの使用を推奨します。")
        print()
        print("【mcp-helper Skillでできること】")
        print("  - MCPサーバーのセットアップと管理")
        print("  - .mcp.jsonの設定")
        print("  - MCPサーバーの追加・削除")
        print("  - トラブルシューティング")
        print()
        print("Claude Codeが自動的にmcp-helper Skillを使用する可能性がありますが、")
        print("使用されない場合は明示的に「mcp-helper Skillを使って」と")
        print("リクエストしてください。")
        print()
        print("=" * 20)
        print()
        debug_log("推奨メッセージ出力完了")


    except Exception as e:
        error_msg = f"Unexpected error in main(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise

if __name__ == '__main__':
    main()
