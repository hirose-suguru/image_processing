# PreToolUse / PostToolUse の正しいパターン

パッケージから `execute()` を直接呼び出せるよう、ロジックと入出力を分離する。

```python
def execute(tool_data: dict):
    """ロジックの本体"""
    try:
        log_hook_execution()
        # メインロジック...

    except Exception as e:
        error_msg = f"Unexpected error in execute(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise


def main():
    """スタンドアロン実行用"""
    from hook_utils import get_tool_data_from_stdin
    tool_data = get_tool_data_from_stdin()
    execute(tool_data)


if __name__ == "__main__":
    main()
```

## UserPromptSubmit の場合

```python
def execute(hook_data: dict):
    """ロジックの本体"""
    try:
        log_hook_execution()
        user_message = hook_data.get("prompt", "")
        # メインロジック...

    except Exception as e:
        log_hook_error(f"Unexpected error: {e}")
        raise


def main(hook_data: dict = None):
    """エントリーポイント"""
    if hook_data is None:
        from hook_utils import get_user_message_from_stdin
        hook_data = {"prompt": get_user_message_from_stdin()}
    execute(hook_data)


if __name__ == "__main__":
    main()
```

## 分離の理由

- パッケージから `execute()` を直接呼び出せる（再利用性）
- テスト時にstdinのモックが不要（テスト容易性）
- 副作用を `main()` に集約できる（保守性）

詳細は `execute_and_main.md` を参照。
