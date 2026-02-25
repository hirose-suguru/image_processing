#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apply_paths.py
プロジェクト初回起動時にパスを適用
session_start hookから自動実行される、または手動実行も可能

使用方法:
    自動実行（初回のみ）: python apply_paths.py
    手動実行（強制）:    python apply_paths.py --force
"""
import json
import sys
import re
import argparse
from pathlib import Path

# hook_utils.pyをインポート
sys.path.insert(0, str(Path(__file__).parent.parent))
from hook_utils import get_project_root, debug_log, load_json5

def is_already_initialized() -> bool:
    """既に初期化済みかチェック"""
    project_root = get_project_root()
    marker_file = project_root / ".claude" / ".initialized"
    return marker_file.exists()

def mark_as_initialized():
    """初期化完了のマーカーを作成"""
    project_root = get_project_root()
    marker_file = project_root / ".claude" / ".initialized"
    marker_file.parent.mkdir(parents=True, exist_ok=True)
    marker_file.touch()
    debug_log(f"Created initialization marker: {marker_file}")

def expand_variables(text: str, variables: dict) -> str:
    """
    テキスト内の {key} を variables[key] で置換

    Args:
        text: 置換対象のテキスト（例: "{t_project_root}/.claude/commands/test.md"）
        variables: 変数の辞書（例: {"t_project_root": "/path/to/project"}）

    Returns:
        置換後のテキスト
    """
    pattern = r'\{([^}]+)\}'

    def replace_match(match):
        key = match.group(1)
        # ドット記法に対応（例: "t_obsidian.vault_path"）
        keys = key.split('.')
        value = variables
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, match.group(0))
            else:
                return match.group(0)
        return str(value) if not isinstance(value, dict) else match.group(0)

    return re.sub(pattern, replace_match, text)

def build_variable_dict(config: dict, vault_name: str) -> dict:
    """
    hook_path_config.json から変数辞書を構築

    Args:
        config: hook_path_config.json の内容
        vault_name: Obsidian vaultの名前

    Returns:
        変数辞書（例: {"t_project_root": "...", "t_obsidian": {...}}）
    """
    variables = {
        "t_project_root": str(get_project_root()),
    }

    # t_obsidian セクションをコピーして vault_path を更新
    if "obsidian" in config:
        obsidian_config = config["obsidian"].copy()
        obsidian_config["vault_path"] = vault_name
        variables["t_obsidian"] = obsidian_config
    else:
        variables["t_obsidian"] = {"vault_path": vault_name}

    return variables

def load_path_replacement_config(vault_name: str):
    """
    hook_path_replace.json を読み込み、変数を展開して返す

    Args:
        vault_name: Obsidian vaultの名前

    Returns:
        変数展開済みの置換設定
    """
    project_root = get_project_root()
    replace_config_path = project_root / ".claude" / "hooks" / "jsons" / "hook_path_replace.json"

    if not replace_config_path.exists():
        debug_log(f"hook_path_replace.json not found: {replace_config_path}")
        return {"path_replacements": []}

    with open(replace_config_path, 'r', encoding='utf-8') as f:
        replace_config = json.load(f)

    # config_source から参照先の設定を読み込み
    config_source = replace_config.get("config_source", "hook_path_config.json5")
    source_config_path = project_root / ".claude" / "hooks" / "jsons" / config_source

    # JSON5形式の場合は load_json5 を使用
    if source_config_path.suffix == ".json5":
        source_config = load_json5(source_config_path)
    else:
        with open(source_config_path, 'r', encoding='utf-8') as f:
            source_config = json.load(f)

    # 変数辞書を構築
    variables = build_variable_dict(source_config, vault_name)

    # 変数を展開
    for replacement in replace_config.get("path_replacements", []):
        # target_file を絶対パスに変換（相対パスの場合）
        target_file = replacement["target_file"]
        if not Path(target_file).is_absolute():
            replacement["target_file"] = str(project_root / target_file)

        # rules 内の変数を展開
        for rule in replacement.get("rules", []):
            # insertモードの変数展開
            if "insert" in rule:
                rule["insert"] = expand_variables(rule["insert"], variables)
            # replace_allモードの変数展開
            if "replace_with" in rule:
                rule["replace_with"] = expand_variables(rule["replace_with"], variables)

    return replace_config

def apply_path_replacements(vault_name: str):
    """パス置換を実行

    サポートする置換モード:
    1. "insert" モード (従来): before + insert + after で部分挿入
    2. "replace_all" モード (新規): プレースホルダーを一括置換
    """
    debug_log(f"Applying path replacements with vault_name={vault_name}")

    replace_config = load_path_replacement_config(vault_name)

    # パス置換を実行
    for replacement in replace_config.get("path_replacements", []):
        target_file = replacement["target_file"]
        target_path = Path(target_file)

        if not target_path.exists():
            debug_log(f"Target file not found, skipping: {target_path}")
            continue

        # ファイルを読み込み
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 置換ルールを適用
        for rule in replacement.get("rules", []):
            mode = rule.get("mode", "insert")  # デフォルトは従来のinsertモード

            if mode == "replace_all":
                # プレースホルダー一括置換モード
                placeholder = rule.get("placeholder", "")
                replace_with = rule.get("replace_with", "")

                if placeholder and placeholder in content:
                    count = content.count(placeholder)
                    content = content.replace(placeholder, replace_with)
                    debug_log(f"Replaced {count} occurrences in {target_path.name}: '{placeholder}' → '{replace_with}'")

            else:
                # 従来のinsertモード（部分挿入）
                before = rule.get("before", "")
                after = rule.get("after", "")
                insert = rule.get("insert", "")

                # 置換
                pattern = before + after
                new_pattern = before + insert + after
                if pattern in content:
                    content = content.replace(pattern, new_pattern)
                    debug_log(f"Replaced in {target_path.name}: '{pattern}' → '{new_pattern}'")

        # 変更があった場合のみ書き込み
        if content != original_content:
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            debug_log(f"Updated: {target_path}")
            print(f"✓ Updated: {target_path.name}")

def main():
    """メイン処理"""
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description='プロジェクトパスの置換を実行')
    parser.add_argument('--force', action='store_true', help='初期化済みでも強制的に実行')
    args = parser.parse_args()

    debug_log("=== apply_paths.py started ===")

    # 既に初期化済みかチェック（--forceオプションがない場合のみ）
    if not args.force and is_already_initialized():
        debug_log("Project already initialized, skipping (use --force to override)")
        return

    project_root = get_project_root()

    # vault名を hook_path_config.json5 から取得
    hook_config_path = project_root / ".claude" / "hooks" / "jsons" / "hook_path_config.json5"

    try:
        hook_config = load_json5(hook_config_path)
        vault_name = hook_config.get('obsidian', {}).get('vault_path', '').strip()
        debug_log(f"Read vault_path from hook_path_config.json5: {vault_name}")
    except Exception as e:
        debug_log(f"Failed to read hook_path_config.json5: {e}")
        vault_name = ''

    # vault_pathが空の場合はobsidian_template/の存在をチェック
    if not vault_name:
        obsidian_template = project_root / "obsidian_template"
        if obsidian_template.exists():
            print("\n=== プロジェクト初期化 ===")
            vault_name = input("Obsidian vaultのディレクトリ名: ").strip()

            if vault_name:
                # リネーム
                new_vault_path = project_root / vault_name
                obsidian_template.rename(new_vault_path)
                print(f"✓ Vault renamed: obsidian_template → {vault_name}")
                debug_log(f"Renamed vault directory: {obsidian_template} → {new_vault_path}")

                # hook_path_config.json5 を更新
                hook_config['obsidian']['vault_path'] = vault_name
                with open(hook_config_path, 'w', encoding='utf-8') as f:
                    json.dump(hook_config, f, indent=2, ensure_ascii=False)
                debug_log(f"Updated hook_path_config.json5 with vault_path: {vault_name}")
        else:
            debug_log("No vault_path in config and no obsidian_template/, skipping vault setup")
            return

    if not vault_name:
        debug_log("No vault name provided, aborting")
        print("Error: vault名が入力されていません")
        return

    # パス置換を実行
    print("\nパスを置換中...")
    apply_path_replacements(vault_name)

    # 初期化完了マーカーを作成
    mark_as_initialized()

    print(f"\n✓ パス適用完了（vault: {vault_name}）")
    debug_log("=== apply_paths.py finished ===")

if __name__ == "__main__":
    main()
