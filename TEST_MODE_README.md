# Test Mode Script Documentation

## Overview
The `scripts\test_mode.bat` script allows you to run the EPUB to Audiobook/Video converter in a **sandbox environment** where no permanent data is saved. This is perfect for testing the application repeatedly without conflicts or cluttering your workspace.

## Features

### 🧪 Isolated Testing Environment
- Creates temporary directories for all test data
- Uses timestamped folders to avoid conflicts
- No interference with your production data

### 📂 Temporary Storage
All data is stored in a timestamped test directory:
- **Test History**: `_TEST_DATA_<timestamp>/history/`
- **Test Novels**: `_TEST_DATA_<timestamp>/novels/`

### 🔄 Repeatable Testing
- Run the same test multiple times
- No "already exists" errors
- No need to manually clean up between tests

### 🧹 Auto-Cleanup Option
After each test run, you can choose to:
- Delete test data immediately
- Keep test data for review

## Usage

### Running Test Mode
Simply double-click `scripts\test_mode.bat` or run from command line:
```batch
scripts\test_mode.bat
```

### What Happens
1. **System Checks**: Verifies Python and dependencies
2. **Test Setup**: Creates temporary directories with timestamp
3. **Launch**: Runs the application with test mode flags
4. **Cleanup Prompt**: Asks if you want to delete test data

### Test Data Location
Test data is stored in: `_TEST_DATA_YYYYMMDD_HHMMSS/`

Example: `_TEST_DATA_20251224_134530/`

## Differences from Normal Mode

| Feature | Normal Mode | Test Mode |
|---------|-------------|-----------|
| History Storage | `~/.epub_project_history/` | `_TEST_DATA_*/history/` |
| Novel Output | `Novels/Active Novels/` | `_TEST_DATA_*/novels/Active Novels/` |
| Data Persistence | Permanent | Temporary |
| Conflict Warnings | Yes (if duplicate) | No (fresh each time) |

## Benefits

### For Development
- Test new features without affecting production data
- Quickly iterate on changes
- No manual cleanup required

### For Testing
- Verify bug fixes
- Test different configurations
- Reproduce issues in isolation

### For Experimentation
- Try different TTS engines
- Test various video settings
- Experiment with chapter merging

## Cleanup

### Automatic Cleanup
After running, you'll be prompted:
```
Do you want to delete test data now? (y/n, default n):
```

- Press `y` to delete immediately
- Press `n` to keep for review

### Manual Cleanup
You can manually delete test folders anytime:
```batch
rd /s /q _TEST_DATA_*
```

Or delete specific test runs:
```batch
rd /s /q _TEST_DATA_20251224_134530
```

## Technical Details

### Environment Variables
The test script sets:
- `EPUB_TEST_MODE=1`
- `EPUB_HISTORY_DIR=<test_history_path>`
- `EPUB_NOVELS_DIR=<test_novels_path>`

### Command-Line Flags
The Python script receives:
```
--test-mode --history-dir "<path>" --novels-dir "<path>"
```

### Path Overrides
Test mode overrides these configuration paths:
- `HISTORY_DIR`
- `HISTORY_FILE`
- `MASTER_NOVEL_DIR`
- `ACTIVE_NOVELS_DIR`
- `ARCHIVED_NOVELS_DIR`

## Troubleshooting

### Test Data Not Deleted
If cleanup fails (files in use):
1. Close any video players or file explorers
2. Wait a few seconds
3. Manually delete the folder

### Permission Errors
Run as administrator if you encounter permission issues.

### Python Not Found
Ensure Python is installed and added to PATH.

## Examples

### Quick Test Run
```batch
:: Run test, complete workflow, delete data
scripts\test_mode.bat
:: ... do your testing ...
:: When prompted, press 'y' to cleanup
```

### Keep Test Data for Review
```batch
:: Run test, keep data for inspection
scripts\test_mode.bat
:: ... do your testing ...
:: When prompted, press 'n' to keep data
:: Review files in _TEST_DATA_* folder
:: Delete manually when done
```

### Multiple Test Runs
```batch
:: Run test #1
scripts\test_mode.bat
:: ... test something ...

:: Run test #2 (new timestamp, no conflicts)
scripts\test_mode.bat
:: ... test something else ...
```

## Notes

- Test mode uses the same `config.json` as normal mode
- Input EPUBs still go in `_NEW_EPUBS_HERE/`
- All other functionality works identically
- Perfect for CI/CD testing pipelines

## See Also
- `scripts\startgod.bat` - Normal production mode
- `scripts\test_mode.bat` - Test mode (this script)
- `Lookup Novel.bat` - Novel lookup tool
- `config.json` - Application configuration
