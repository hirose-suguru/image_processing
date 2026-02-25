# Fundamental Hook 統合の仕様変更

## 変更日
- 初版: 2025-11-07
- 更新: 2025-11-09 (get_path_from_config()の変更、PostToolUseロガーの分割)

## 変更の目的
fundamental/配下のhookが多数になり管理が困難になったため、hookイベント種別ごとにディレクトリを分割し、package.pyで統合実行する構造に変更。

---

## 1. ディレクトリ構造の変更
### 変更前
```
.claude/hooks/scripts/fundamental/
├── session_start_message.py
├── user_prompt_message.py
├── manage_timestamps.py
├── pre_mkdir_verify.py
├── post_mkdir_check.py
├── postu_tool_logger.py
└── ... (他にも複数のhook)
```

**課題**:
- settings.jsonにhookイベントごとに複数のエントリが必要
- 新規hookの追加時にsettings.jsonを編集する必要がある
- 実行順序の管理が困難

### 変更後
```
.claude/hooks/scripts/fundamental/
├── hook_utils.py                    # 自動同期されるユーティリティ
├── session_start_package.py         # SessionStart統合実行
├── user_prompt_submit_package.py    # UserPromptSubmit統合実行
├── pre_tool_use_package.py          # PreToolUse統合実行
├── post_tool_use_package.py         # PostToolUse統合実行
├── stop_package.py                  # Stop統合実行
├── session_start/
│   ├── __init__.py
│   └── session_start_message.py
├── user_prompt_submit/
│   ├── __init__.py
│   ├── user_prompt_message.py
│   └── manage_timestamps.py
├── pre_tool_use/
│   ├── __init__.py
│   └── pre_mkdir_verify.py
├── post_tool_use/
│   ├── __init__.py
│   ├── post_mkdir_check.py
│   ├── postu_tool_logger.py      # 全ツールのログ記録
│   └── postu_bash_logger.py      # Bash専用ログ記録
└── stop/
    ├── __init__.py
    ├── stop_message.py
    └── sync_hook_utils.py
```

**改善点**:
- hookイベント種別ごとにサブディレクトリで整理
- settings.jsonは各hookイベントにつき1エントリのみ
- 新規hook追加時はサブディレクトリに.pyを追加してpackage.pyでimportするだけ

---

## 2. settings.jsonの変更
### 変更前
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "*",
        "hooks": [
          {"type": "command", "command": "python .../user_prompt_message.py"},
          {"type": "command", "command": "python .../manage_timestamps.py"},
          ...
        ]
      }
    ]
  }
}
```

### 変更後
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "*",
        "hooks": [
          {"type": "command", "command": "python .../user_prompt_submit_package.py"}
        ]
      }
    ]
  }
}
```

**改善点**:
- 各hookイベントにつき1エントリに集約
- 新規hook追加時にsettings.jsonの編集が不要

---

## 3. hook_utils.pyの配置変更
### 変更前
```
.claude/hooks/scripts/hook_utils.py
```

各スクリプトから以下のようにimport:
```python
sys.path.insert(0, str(Path(__file__).parent.parent))
from hook_utils import ...
```

**課題**:
- fundamental/配下のスクリプトとscripts/直下のスクリプトで階層が異なる
- fundamental/配下を更にサブディレクトリに分割すると`.parent`の数が変わる

### 変更後
```
.claude/hooks/scripts/hook_utils.py          # マスター
.claude/hooks/scripts/fundamental/hook_utils.py  # 自動同期されるコピー
```

全スクリプトで統一的にimport:
```python
sys.path.insert(0, str(Path(__file__).parent.parent))
from hook_utils import ...
```

**改善点**:
- 階層の深さに関係なく`.parent.parent`で統一
- hook_utils.pyはSessionStart時とStop時に自動同期される

---

## 4. hook_utils.pyの機能追加
### 追加1: 動的パス解決
**変更前**:
```python
_config_path = Path(__file__).parent.parent / "jsons" / "hook_path_config.json"
```

**課題**:
- scripts/とfundamental/で階層が異なるため、`.parent.parent`の数が変わる

**変更後**:
```python
# hooks/ディレクトリを動的に探す
_hooks_dir = Path(__file__).resolve()
while _hooks_dir.name != "hooks" and _hooks_dir.parent != _hooks_dir:
    _hooks_dir = _hooks_dir.parent
if _hooks_dir.name != "hooks":
    raise RuntimeError("Could not find 'hooks' directory in path")
_config_path = _hooks_dir / "jsons" / "hook_path_config.json"
```

**改善点**:
- 階層の深さに依存しない
- scripts/でもfundamental/でも同じロジックで動作

### 追加2: get_project_root()関数
**新規追加**:
```python
def get_project_root() -> Path:
    """
    プロジェクトルートディレクトリを取得
    hooks/ → .claude/ → プロジェクトルート
    """
    return _hooks_dir.parent.parent
```

**理由**:
- ディレクトリ階層が深くなったため、`.parent.parent.parent.parent`のようなハードコーディングを避ける
- プロジェクトルート取得を一元化

**使用例**:
```python
from hook_utils import get_project_root
project_root = get_project_root()
os.chdir(project_root)
```

### 追加3: get_path_from_config()の改善（2025-11-09追加）
**変更前**:
```python
def get_path_from_config(key: str) -> Path:
    """相対パスを返す"""
    if key not in _config:
        raise KeyError(f"'{key}' は設定ファイルに存在しません")
    return Path(_config[key])
```

**課題**:
- 相対パスを返すため、呼び出し側で毎回`project_root`と結合する必要がある
- カレントディレクトリに依存してしまう

**変更後**:
```python
def get_path_from_config(key: str) -> Path:
    """プロジェクトルートからの絶対パスを返す"""
    if key not in _config:
        raise KeyError(f"'{key}' は設定ファイルに存在しません")

    # 相対パスを取得
    relative_path = Path(_config[key])

    # プロジェクトルートと結合して絶対パスを返す
    project_root = get_project_root()
    return project_root / relative_path
```

**改善点**:
- **常にプロジェクトルートからの絶対パスを返す**
- 呼び出し側がシンプルに: `tool_history_file = get_path_from_config("tool_history_file")`
- カレントディレクトリに依存しない安全な設計

**使用例（変更前 vs 変更後）**:
```python
# 変更前: 3行必要
project_root = get_project_root()
tool_history_rel = get_path_from_config("tool_history_file")
tool_history_file = project_root / tool_history_rel

# 変更後: 1行で完結
tool_history_file = get_path_from_config("tool_history_file")
```

---

## 5. 各スクリプトの変更
### user_prompt_message.py, session_start_message.py
**変更前**:
```python
project_root = Path(__file__).parent.parent.parent.parent
os.chdir(project_root)
```

**変更後**:
```python
from hook_utils import get_project_root
project_root = get_project_root()
os.chdir(project_root)
```

### stop_message.py

**新規追加**:
```python
import os
from hook_utils import get_project_root

def main():
    log_hook_execution()

    # プロジェクトルートに移動（次回SessionStartのため）
    project_root = get_project_root()
    os.chdir(project_root)
```

**理由**: Stop時にもプロジェクトルートに移動することで、次回SessionStart時の作業ディレクトリを保証

---

## 6. PostToolUseのstdin読み取り処理変更
### 変更前
各スクリプト（post_mkdir_check.py, postu_tool_logger.py）が個別にstdinを読み取り

**課題**:
- stdinは1回しか読めないため、複数スクリプトで読み取りできない

### 変更後
post_tool_use_package.pyで1回だけstdinを読み取り、各モジュールに渡す

```python
def main():
    # stdin読み取り（1回のみ）
    input_data = sys.stdin.read()
    if input_data.strip():
        hook_data = json.loads(input_data)

    tool_name = hook_data.get("tool_name", "")
    tool_input = hook_data.get("tool_input", {})

    # Bashツールの場合のみmkdirチェック実行
    if tool_name == "Bash":
        from post_tool_use import post_mkdir_check
        result = post_mkdir_check.verify_mkdir_execution(tool_input)

    # 全ツールでログ記録
    if hook_data:
        from post_tool_use.postu_tool_logger import build_log_entry, write_log
        tool_history_file = get_path_from_config("tool_history_file")
        log_entry = build_log_entry(hook_data)
        write_log(log_entry, tool_history_file)

        # Bash専用ログも記録
        if tool_name == "Bash":
            from post_tool_use import postu_bash_logger
            postu_bash_logger.main(hook_data)
```

**改善点**:
- stdinを1回だけ読み取り、各モジュールにデータを渡す
- matcher条件分岐をpackage.py内で実装（`if tool_name == "Bash"`）
- データ再利用: package.pyで取得したhook_dataを各loggerに渡す

---

## 7. hook_utils.pyの自動同期
### 新規追加: sync_hook_utils.py
```python
def main():
    # scripts/hook_utils.py -> fundamental/hook_utils.py
    source = Path(__file__).parent.parent.parent / "hook_utils.py"
    dest = Path(__file__).parent.parent / "hook_utils.py"
    shutil.copy2(source, dest)
```

**同期タイミング**:
- **SessionStart時**: session_start_package.py内で実行（最新版を取得）
- **Stop時**: stop_package.pyで実行（バックアップ同期）

**理由**:
- scripts/hook_utils.pyを編集した後、fundamental/にも反映させるため
- 手動コピーを不要にする

---

## 8. log_hook_execution()の引数削除
### 変更前
一部のスクリプトで誤って引数を渡していた:
```python
log_hook_execution("user_prompt_message.py")
```

### 変更後
全スクリプトで引数なしに統一:
```python
log_hook_execution()
```

**修正方法**: sedで一括置換
```bash
find .claude/hooks/scripts/fundamental/ -name "*.py" -type f -exec sed -i 's/log_hook_execution("[^"]*")/log_hook_execution()/g' {} \;
```

---

## 9. PostToolUseロガーの分割（2025-11-09追加）

### 背景
- 全ツールのログ（Read/Edit/Write/Grep/Bash等）を記録したい
- Bashコマンドは別ファイルにも詳細ログを記録したい

### 実装
#### hook_path_config.jsonに追加
```json
{
  "tool_history_file": ".claude/hooks/logs/tool_history.log",
  "bash_history_file": ".claude/hooks/logs/bash_history.log"
}
```

#### postu_tool_logger.py
- **対象**: 全ツール（Read, Edit, Write, Grep, Bash等）
- **ログファイル**: `tool_history.log`
- **記録内容**: ツール名、入力、レスポンス、作業ディレクトリ

#### postu_bash_logger.py（新規追加）
- **対象**: Bashツールのみ
- **ログファイル**: `bash_history.log`
- **記録内容**: コマンド、stdout, stderr, 終了コード、タイムスタンプ

#### 柔軟な実行パターン
両loggerは2つの実行モードをサポート:

```python
def main(hook_data: dict = None):
    """
    Args:
        hook_data: ツール実行データ（省略時はstdinから取得）
                  - packageから呼ばれる場合: hook_dataを渡す（データ再利用）
                  - スタンドアロン実行の場合: Noneのままでstdinから読み込む
    """
    # hook_dataが渡されていない場合はstdinから取得
    if hook_data is None:
        log_hook_execution()
        hook_data = get_tool_data_from_stdin()
        if not hook_data:
            debug_log("ツールデータの取得に失敗したため終了")
            return

    # ログ処理...
```

**メリット**:
- **データ再利用**: package.pyから呼ぶときはhook_dataを渡してstdin再読み取りを回避
- **スタンドアロン実行**: 単体テスト時は引数なしで実行可能

---

## まとめ
### 主な変更点
1. **ディレクトリ構造の再編**: hookイベント種別ごとにサブディレクトリで整理
2. **package.pyによる統合実行**: settings.jsonを簡素化、新規hook追加を容易に
3. **hook_utils.pyの自動同期**: scripts/ → fundamental/ の自動コピー
4. **動的パス解決**: 階層の深さに依存しないパス取得
5. **get_project_root()関数の追加**: プロジェクトルート取得を一元化
6. **PostToolUseのstdin読み取り最適化**: 1回の読み取りで複数モジュールに配信
7. **stop_message.pyでプロジェクトルートへ移動**: 次回SessionStart時の作業ディレクトリを保証
8. **get_path_from_config()の改善**: 常に絶対パスを返すことでコードを簡潔化（2025-11-09）
9. **PostToolUseロガーの分割**: 全ツールログとBash専用ログを分離（2025-11-09）

### メリット
- **管理性向上**: hookイベント種別ごとに整理され、見通しが良くなった
- **拡張性向上**: 新規hook追加時にsettings.jsonの編集が不要
- **保守性向上**: 統一的なimport方法、動的パス解決により、階層変更に強い構造
- **デバッグ性向上**: debug_logで各処理の開始/終了を記録
- **コード簡潔化**: get_path_from_config()が絶対パスを返すため、呼び出し側が1行で完結
- **ログの柔軟性**: 全ツールログとBash専用ログを分離し、用途に応じた記録が可能
