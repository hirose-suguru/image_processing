#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ss_reset_hook_toggle.py
SessionStart hookで実行されるスクリプト
すべてのhook toggleをリセットするが、{toggle_name}_compact が存在する場合は復元する
"""
import sys
from pathlib import Path
import json

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import log_hook_execution, set_hook_toggle, debug_log, get_path_from_config, log_hook_error, load_json5

except ImportError as e:
    error_msg = f"Failed to import hook_utils: {e}"
    # stdoutとstderrに出力のみ（ファイル書き込みはしない）
    print(f"[HOOK ERROR] {error_msg}")
    print(f"[HOOK ERROR] Script: {__file__}")
    print(f"[HOOK ERROR] sys.path: {sys.path}")
    sys.stderr.write(f"[HOOK ERROR] {error_msg}\n")
    sys.stderr.write(f"[HOOK ERROR] Script: {__file__}\n")
    sys.exit(1)

def load_reset_config():
    """リセット設定ファイルを読み込む"""
    try:
        config_path = get_path_from_config("ss_hook_toggle_file")
        if config_path.exists():
            config = load_json5(config_path)
            return config.get("toggles", {})
    except Exception as e:
        debug_log(f"Failed to load reset config: {e}")
    return {}


def main():
    try:
        # hook実行ログを記録
        log_hook_execution()
        debug_log("started.")

        # hook_toggle_config.json5を読み込む
        toggle_config_path = get_path_from_config("hook_toggle_file")

        try:
            if not toggle_config_path.exists():
                debug_log(f"Toggle config not found: {toggle_config_path}")
                debug_log("finished.")
                return

            all_toggles = load_json5(toggle_config_path)

            # commentキーを除外
            all_toggles = {k: v for k, v in all_toggles.items() if k != "comment"}
            debug_log(f"SessionStart: Current toggles = {all_toggles}")

        except (json.JSONDecodeError, IOError) as e:
            debug_log(f"Failed to read toggle config: {e}")
            debug_log("finished.")
            return

        # リセット設定を読み込む
        reset_config = load_reset_config()
        debug_log(f"SessionStart: Reset config = {reset_config}")

        # _compact で終わるtoggleを検出
        compact_toggles = {k: v for k, v in all_toggles.items() if k.endswith("_compact")}

        if compact_toggles:
            # AutoCompact後の復元処理
            debug_log(f"SessionStart: AutoCompact detected, restoring toggles")
            restored_count = 0

            for compact_name, compact_value in compact_toggles.items():
                # 元のtoggle名を取得（_compactを除去）
                original_name = compact_name[:-8]  # "_compact" の8文字を除去

                # 元のtoggleに復元
                set_hook_toggle(original_name, compact_value)
                debug_log(f"SessionStart: Restored {original_name} = {compact_value} from {compact_name}")

                # compact用toggleをFalseにリセット
                set_hook_toggle(compact_name, False)
                debug_log(f"SessionStart: Reset {compact_name} to False")

                if compact_value:
                    restored_count += 1

            if restored_count > 0:
                print(f"AutoCompact: Restored {restored_count} toggle state(s)")
            debug_log(f"SessionStart: AutoCompact restoration completed")
        else:
            # 通常のSessionStart: 設定に基づいてリセット
            debug_log("SessionStart: Normal startup, resetting toggles based on config")
            reset_count = 0

            for toggle_name, toggle_value in all_toggles.items():
                # リセット設定を取得（デフォルト: reset=True, default=False）
                toggle_config = reset_config.get(toggle_name, {"reset": True, "default": False})
                should_reset = toggle_config.get("reset", True)
                default_value = toggle_config.get("default", False)

                if should_reset:
                    # リセット対象: デフォルト値に設定
                    if toggle_value != default_value:
                        set_hook_toggle(toggle_name, default_value)
                        debug_log(f"SessionStart: Reset {toggle_name} to {default_value}")
                        reset_count += 1
                else:
                    # リセット対象外: 前回の値を維持
                    debug_log(f"SessionStart: Keeping {toggle_name} = {toggle_value} (reset disabled)")

            if reset_count > 0:
                print(f"Hook toggles were reset to defaults")
                debug_log(f"SessionStart: Reset {reset_count} toggle(s)")

        debug_log("finished.")


    except Exception as e:
        error_msg = f"Unexpected error in main(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise

if __name__ == "__main__":
    main()
