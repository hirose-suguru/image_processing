---
name: hook-review
description: hookをレビューするときに使用してください。レビューする項目が記載されています。
allowed-tools: Read, Grep, Edit, AskUserQuestion
---

# Hook Review Skill

Pythonで書かれたClaude Code hookスクリプトのレビュー基準です。
このSkillを用いるとき、必ず`../agents/hook-reviewer.md`のSubAgentsを呼び出してください。
SubAgentsを呼び出したらメインコンテキストは何もせずに待機していて下さい。

## レビュー項目

### (i) hook_utils.py のインポートパターン

**チェックポイント**:
- [ ] `sys.path.insert(0, ...)` の書き方が正しいか
- [ ] `Path(__file__).parent.parent` になっているか
- [ ] 必要な関数のみを明示的にインポートしているか
- [ ] `ImportError` のエラーハンドリングが実装されているか

**正しいパターン**:
```python
import sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import log_hook_execution, debug_log, get_path_from_config

except ImportError as e:
    error_msg = f"[HOOK ERROR] Failed to import hook_utils: {e}\nScript: {__file__}"
    print(error_msg, file=sys.stderr)
    sys.exit(2)
```

### (ii) 関数構造とエラーハンドリング

**チェックポイント**:
- [ ] `log_hook_execution()` を呼び出しているか
- [ ] `try-except` ブロックで例外を捕捉しているか
- [ ] エラー時に `log_hook_error(error_msg)` を呼び出しているか
- [ ] デバッグ出力に `debug_log()` を使用しているか（`print()` ではなく）
- [ ] PreToolUse/PostToolUse/UserPromptSubmitの場合: `execute()` と `main()` が分離されているか。packageの方のファイルで`.execute()`を呼び出すようにしているか。

**正しいパターン**:
- PreToolUse / PostToolUse / UserPromptSubmit → `chained_loading/for_pretu_postu.md` を参照
- その他のhook → `chained_loading/for_other_hooks.md` を参照

### (iii) パスの読み込み方

**原則**: `get_path_from_config()` または `get_obsidian_path()` **のみ**を使用する

**チェックポイント**:
- [ ] `get_path_from_config()` または `get_obsidian_path()` を使用しているか
- [ ] `get_project_root()` を直接使ってパスを構築していないか
- [ ] パス文字列を直接ハードコードしていないか

**正しいパターン**:
```python
from hook_utils import get_path_from_config, get_obsidian_path

# 設定ファイルからパスを取得（これのみ使用）
timestamps_file = get_path_from_config("timestamps_file")
progress_md = get_obsidian_path("progress")
```

**よくある間違い**:
```python
# ❌ パスをハードコード
log_file = Path(".claude/hooks/logs/hook_log.log")

# ❌ get_project_root() でパスを構築（非推奨）
project_root = get_project_root()
custom_file = project_root / ".claude" / "custom" / "data.json"
```

**キーが存在するかの確認**:

必要なキーが `hook_path_config.json5` に存在するかを確認:
```bash
python .claude/python_scripts/check_config_key.py your_key_name
```

キーが存在しない場合、メインコンテキストに報告して `hook_path_config.json5` への追加を提案してください。

### (iv-a) 汎用性の検討

**チェックポイント**:
- [ ] 関数が特定のファイル名やパスにハードコードされていないか。
- [ ] より汎用的な実装手法が使えるのに、特定の用途に限定していないか。

**悪い例**:
```python
def check_progress_md():  # progress.mdに限定
    progress_path = Path(".claude/obsidian/progress.md")  # ハードコード
```

**良い例**:
```python
def check_file_content(file_path: Path):  # 任意のファイルを受け取る
    if not file_path.exists():
        return None
```

### (iv-b) ファイル名の妥当性

**チェックポイント**:
- [ ] ファイル名が特定の用途に限定されすぎていないか。

### (v) PreToolUse hookでのブロック方法(それ以外のhookならチェックしなくてよい)
`chained_loading.md`を参照。

