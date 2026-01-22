# cc-read-limit-hook

A Claude Code PreToolUse hook that enforces file read limits to optimize context usage.

一个 Claude Code PreToolUse 钩子，用于限制文件读取范围以优化上下文使用。

---

## Features / 功能

- **Block large file reads** - Files >1000 lines or >50KB require `offset` + `limit` parameters
- **Limit single reads** - Max 500 lines / 20KB per read operation
- **Auto-add limit** - Automatically adds limit when only offset is specified
- **Statistics logging** - Logs read attempts for analysis

---

- **阻止大文件读取** - 超过 1000 行或 50KB 的文件必须指定 `offset` + `limit` 参数
- **限制单次读取** - 每次最多读取 500 行 / 20KB
- **自动添加 limit** - 仅指定 offset 时自动补充 limit
- **统计日志** - 记录读取操作用于分析

## Installation / 安装

1. Copy `read-guard.py` to your hooks directory:
   ```bash
   cp read-guard.py "$USERPROFILE/.claude/hooks/"
   ```

2. Add to `~/.claude/settings.json`:
   ```json
   {
     "hooks": {
       "PreToolUse": [
         {
           "matcher": "Read",
           "hooks": [
             {
               "type": "command",
               "command": "python \"$USERPROFILE/.claude/hooks/read-guard.py\""
             }
           ]
         }
       ]
     }
   }
   ```

## Configuration / 配置

Edit the constants in `read-guard.py`:

```python
MAX_FILE_LINES = 1000        # Line threshold / 行数阈值
MAX_FILE_BYTES = 50 * 1024   # Byte threshold / 字节阈值
MAX_SINGLE_READ_LINES = 500  # Max lines per read / 单次最大行数
MAX_SINGLE_READ_BYTES = 20 * 1024  # Max bytes per read / 单次最大字节
```

## License / 许可

MIT
