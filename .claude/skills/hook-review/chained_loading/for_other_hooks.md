# その他hook（SessionStart / Stop等）の正しいパターン

分離不要。`main()` のみで十分。

```python
def main():
    try:
        log_hook_execution()
        # 処理

    except Exception as e:
        error_msg = f"Unexpected error in main(): {e}"
        log_hook_error(error_msg)
        debug_log(error_msg)
        raise


if __name__ == "__main__":
    main()
```
