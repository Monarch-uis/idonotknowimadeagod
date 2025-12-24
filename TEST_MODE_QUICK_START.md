# Quick Start Guide: Test Mode

## What is Test Mode?

Test mode allows you to run the EPUB converter **without saving any permanent data**. Perfect for:
- 🧪 Testing new features
- 🔄 Repeating the same conversion
- 🐛 Debugging issues
- 📚 Experimenting with settings

## How to Use

### Step 1: Run the Test Script
Double-click `scripts\test_mode.bat` or run from command line:
```batch
scripts\test_mode.bat
```

### Step 2: Use Normally
The application works exactly the same as normal mode:
- Select your EPUB
- Choose TTS settings
- Generate audio/video

### Step 3: Cleanup (Optional)
After testing, you'll be asked:
```
Do you want to delete test data now? (y/n, default n):
```
- Press **y** to delete test data immediately
- Press **n** to keep it for review

## Key Differences

### Normal Mode (`scripts\startgod.bat`)
- ✅ Saves history permanently
- ✅ Outputs to `Novels/Active Novels/`
- ⚠️ Shows "already processed" warnings

### Test Mode (`scripts\test_mode.bat`)
- 🧪 Uses temporary directories
- 🔄 No "already processed" warnings
- 🧹 Easy cleanup after testing

## Test Data Location

All test data goes to: `_TEST_DATA_<timestamp>/`

Example:
```
_TEST_DATA_20251224_140530/
├── history/
│   └── global_database.json
└── novels/
    ├── Active Novels/
    │   └── [Your Test Novel]/
    └── Archived Novels/
```

## Tips

### Repeat Same Test
Just run `test_mode.bat` again! Each run creates a new timestamped folder.

### Keep Test Data
Press **n** when asked to cleanup. Review the output, then delete manually when done.

### Quick Cleanup
Delete all test folders at once:
```batch
rd /s /q _TEST_DATA_*
```

## Troubleshooting

**Q: Can't delete test folder?**  
A: Close any programs using the files (video players, file explorer), wait a few seconds, then try again.

**Q: Test mode using production data?**  
A: Make sure you're running `scripts\test_mode.bat`, not `scripts\startgod.bat`.

**Q: Where's my test output?**  
A: Look in `_TEST_DATA_<timestamp>/novels/Active Novels/[Book Name]/`

## Need Help?

- Check `TEST_MODE_README.md` for detailed documentation
- Review the test folder structure
- Ensure you're using `scripts\test_mode.bat`
