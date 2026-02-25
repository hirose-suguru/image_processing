**原則**: `stop_tool_use()` 関数を使用する

**チェックポイント**:
- [ ] `hook_utils.py` から `stop_tool_use` をインポートしているか
- [ ] ブロック時に `stop_tool_use(message)` を呼び出しているか
- [ ] 直接 `sys.exit(2)` や `print(..., file=sys.stderr)` を使っていないか

**正しいパターン**:
```python
from hook_utils import stop_tool_use

# ブロックしたいとき
stop_tool_use("このファイルは大きすぎます。offsetとlimitを指定してください。")
```

**Exit Codeの意味**:
| Exit Code | 動作 |
|-----------|------|
| `0` | 許可（ツール実行続行） |
| `1` | 警告（stderrをユーザーに表示、ツール実行続行） |
| `2` | ブロック（stderrをClaudeにフィードバック） |

**詳細**: `.claude/hooks/docs/pre_tool_use_blocking.md` を参照
