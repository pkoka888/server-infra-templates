# Cline Troubleshooting Guide

## Current Status (2026-04-06)

### Installation Details
- **VS Code Extension**: `saoudrizwan.claude-dev` v3.77.0
- **CLI**: v2.13.0 (at `~/.local/bin/cline` → `~/.nvm/versions/node/v24.11.1/lib/node_modules/cline/`)
- **API Provider**: novita (via OpenRouter gateway)
- **Model**: `kwaipilot/kat-coder-pro-v1`

## CRITICAL FIX: Infinite Loop Issue (Known Bug #9846)

**Symptom**: Cline stuck in "Thinking" mode, repeating the same output like:
- "First stop the running scenario, then fix the error:"
- "It can be stopped, let me first stop the scenario, then fix the code:"
- "Fix completed. Now clear the previous error logs, then run the scenario to verify:"

**Root Cause**: Model keeps outputting plain text without calling tools → Creates infinite loop

### Fix Options:

#### Option 1: Disable Native Tool Calling (RECOMMENDED)
In VS Code:
1. Press `F1` → Type `Cline: Open Settings`
2. Find and **disable**:
   - ❌ "Native Tool Call" (turn OFF)
   - ❌ "Parallel Tool Calling" (turn OFF)
3. Save settings and reload VS Code window

#### Option 2: Change Model
- Use a different model like `claude-sonnet-4-20250514` instead of `kwaipilot/kat-coder-pro-v1`

#### Option 3: Kill Stuck CLI Process
```bash
# Find and kill stuck Cline process
ps aux | grep cline | grep -v grep
kill <PID>
```

#### Option 4: Restart Extension via Command Line
```bash
# Reload VS Code window
code --folder-uri /var/www/metabase --reuse-window
```

### Quick Fix Applied
We killed the stuck Cline CLI process (PID 4004675) and the task resumed successfully.

### Known Issues

1. **Focus Chain File Errors**
   - Error: `Could not load from markdown file: ENOENT`
   - Location: `~/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/tasks/{task_id}/focus_chain_taskid_{task_id}.md`
   - **Impact**: Low - task continues working despite error
   - **Root cause**: Race condition when file watcher triggers before file is written

2. **Checkpoint Failures**
   - Error: `Failed to create checkpoint commit`
   - Error: `Failed to add at least one file(s) to checkpoints shadow git`
   - **Impact**: Low - checkpoints eventually succeed on retry
   - **Root cause**: Nested git repository handling issues

3. **Model Output Issues**
   - The model (`kwaipilot/kat-coder-pro-v1`) is producing repetitive output like "Failure", "error", "fail", "stop"
   - This appears to be a model issue, not Cline itself
   - **Impact**: Tasks may get stuck in loops or produce poor results

4. **System Notifications**
   - Error: `Could not show system notification`
   - **Impact**: Cosmetic only

## How to Check Cline Logs

### VS Code Extension Logs
```bash
# Find the latest log directory
ls -lt ~/.vscode-server/data/logs/ | head -3

# Check Cline logs
cat ~/.vscode-server/data/logs/20260405T092900/exthost13/output_logging_20260406T081702/1-Cline.log

# Check for errors
grep -i "error\|fail" ~/.vscode-server/data/logs/20260405T092900/exthost13/output_logging_20260406T081702/1-Cline.log | tail -30
```

### Cline CLI Logs
```bash
cat ~/.cline/data/logs/cline-cli.1.log
```

## Log Locations

| Component | Location |
|-----------|-----------|
| VS Code Extension | `~/.vscode-server/data/logs/` |
| Cline Extension Logs | `{log_dir}/output_logging_*/1-Cline.log` |
| Cline CLI | `~/.cline/data/logs/` |
| Task Data | `~/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/tasks/` |
| Checkpoints | `~/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/checkpoints/` |

## Debug Console in VS Code

To access VS Code debug console:
1. Open VS Code
2. Go to View → Debug Console (Ctrl+Shift+Y)
3. Or use Command Palette → "Debug: Show Debug Console"

The debug console shows extension host output and any errors from extensions.

## Possible Solutions

### 1. Restart the Extension
- Press F1 → "Developer: Reload Window"
- Or: Press F1 → "Extension: Restart Extension Host"

### 2. Clear Task State
```bash
# Remove stuck task directories
rm -rf ~/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/tasks/
```

### 3. Reset Cline Settings
```bash
# Backup first
cp -r ~/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/ ~/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev.backup/

# Clear state (will reset all settings)
rm -rf ~/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/state/
```

### 4. Change API Provider/Model
- Open Cline settings → API & Model Settings
- Try a different model like `claude-sonnet-4-20250514`

### 5. Check Network/API Issues
```bash
# Test novita API connectivity
curl -s https://api.novita.ai/v1/models -H "Authorization: YOUR_KEY"
```

## Current Running Processes

- Cline extension is running via VS Code remote (extension host)
- Task 1775459517038 is currently active but appears stuck
- Checkpoints are being created successfully

## Notes

- Cline uses the VS Code terminal for command execution
- It uses shadow git for checkpoint tracking
- The model `kwaipilot/kat-coder-pro-v1` may be unreliable - consider using Anthropic models instead
