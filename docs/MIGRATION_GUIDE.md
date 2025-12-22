# 📋 MIGRATION GUIDE - Python Script Reorganization

## ✅ COMPLETED STEPS:

1. ✅ Created folder structure:
   - `core/` (with __init__.py)
   - `features/` (with __init__.py)
   - `tests/` (with __init__.py already existed)

2. ✅ Created merged `system_validator_merged.py` in root

3. ✅ Moved `config.py` to `core/config.py`

---

## 📝 REMAINING STEPS:

### STEP 1: Copy Core Files to core/

Copy these files to the `core/` folder:
```
utils.py → core/utils.py
epub_io.py → core/epub_io.py
tts.py → core/tts.py
ui_manager.py → core/ui_manager.py
```

Move the merged validator:
```
system_validator_merged.py → core/system_validator.py
```

### STEP 2: Copy Feature Files to features/

Copy these files to the `features/` folder:
```
chapter_merger.py → features/chapter_merger.py
checkpoint_manager.py → features/checkpoint_manager.py
queue_manager.py → features/queue_manager.py
memory_manager.py → features/memory_manager.py
auto_recovery.py → features/auto_recovery.py
```

### STEP 3: Move Test Files to tests/

Copy these test files to the `tests/` folder:
```
test_auto_recovery.py → tests/test_auto_recovery.py
test_ffmpeg.py → tests/test_ffmpeg.py
test_imports.py → tests/test_imports.py
test_voices.py → tests/test_voices.py
```

### STEP 4: Handle Debug Files

**Option chosen: Create debug_tools.py in root**

Merge `debug_banner.py` and `debug_display.py` into one file:
```python
# debug_tools.py
import os
import time

def CP(text, color='white'):
    colors = {
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'purple': '\033[95m',
        'white': '\033[97m',
    }
    end = '\033[0m'
    return colors.get(color, '') + text + end

def print_rainbow_banner():
    lines = [
        "    ███████╗ █████╗ ███╗   ██╗███████╗██╗ ██████╗████████╗██╗ ██████╗ ███╗   ██╗",
        "    ██╔════╝██╔══██╗████╗  ██║██╔════╝██║██╔════╝╚══██╔══╝██║██╔═══██╗████╗  ██║",
        "    █████╗  ███████║██╔██╗ ██║█████╗  ██║██║        ██║   ██║██║   ██║██╔██╗ ██║",
        "    ██╔══╝  ██╔══██║██║╚██╗██║██╔══╝  ██║██║        ██║   ██║██║   ██║██║╚██╗██║",
        "    ██║     ██║  ██║██║ ╚████║██║     ██║╚██████╗   ██║   ██║╚██████╔╝██║ ╚████║",
        "    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝     ╚═╝ ╚═════╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝",
        "                            LEGEND AUTOMATION"
    ]
    colors = ['\033[91m', '\033[93m', '\033[92m', '\033[96m', '\033[94m', '\033[95m']
    
    os.system("")
    print()
    for i, line in enumerate(lines):
        print(colors[i % len(colors)] + line + '\033[0m')

def test_display():
    print("Hello! If you can read this, your terminal is capable of displaying text.")
    print("Testing diagonal stripes with minimal script.")
    import time
    print("Waiting 5 seconds...")
    time.sleep(5)
    print("Done.")
```

---

## 🔧 STEP 5: UPDATE IMPORTS (CRITICAL!)

### A. Main Entry Point (`epub_project_manager.py`)

**OLD imports:**
```python
from config import CONFIG, DEFAULT_CONFIG, INPUT_ZONE, HISTORY_DIR, HISTORY_FILE, CONFIG_FILE, MASTER_NOVEL_DIR, ACTIVE_NOVELS_DIR, ARCHIVED_NOVELS_DIR
from utils import CP, beep_notification, play_critical_failure_alarm, sanitize_filename, seconds_to_time_str, extract_smart_number, censor_text, fix_pronunciation, generate_smart_tags, logger
from epub_io import setup_global_input, cleanup_temp_dir, setup_project_folders, load_history, save_to_history, check_history_conflict, calculate_epub_hash, check_duplicate_epub, load_book_profile, save_book_profile, clean_html_for_tts, clean_html_summary, parse_full_epub, extract_cover_to_project, generate_description_file
from tts import EDGE_TTS_AVAILABLE, PYTTSX3_AVAILABLE, PIPER_AVAILABLE, select_tts_engine_and_mode, select_voice, test_edge_tts_connection, get_piper_models, select_piper_model, gen_single_clip_edge_with_retry, gen_single_clip_pyttsx3_with_retry, gen_single_clip_piper_with_retry, resolve_piper_model_path
from checkpoint_manager import CheckpointManager, save_progress_checkpoint, check_for_resume
import ui_manager
from auto_recovery import AutoRecovery, try_auto_recover, ErrorCategory
from memory_manager import optimize_memory, check_memory_status
from queue_manager import QueueManager
```

**NEW imports:**
```python
from core.config import CONFIG, DEFAULT_CONFIG, INPUT_ZONE, HISTORY_DIR, HISTORY_FILE, CONFIG_FILE, MASTER_NOVEL_DIR, ACTIVE_NOVELS_DIR, ARCHIVED_NOVELS_DIR
from core.utils import CP, beep_notification, play_critical_failure_alarm, sanitize_filename, seconds_to_time_str, extract_smart_number, censor_text, fix_pronunciation, generate_smart_tags, logger
from core.epub_io import setup_global_input, cleanup_temp_dir, setup_project_folders, load_history, save_to_history, check_history_conflict, calculate_epub_hash, check_duplicate_epub, load_book_profile, save_book_profile, clean_html_for_tts, clean_html_summary, parse_full_epub, extract_cover_to_project, generate_description_file
from core.tts import EDGE_TTS_AVAILABLE, PYTTSX3_AVAILABLE, PIPER_AVAILABLE, select_tts_engine_and_mode, select_voice, test_edge_tts_connection, get_piper_models, select_piper_model, gen_single_clip_edge_with_retry, gen_single_clip_pyttsx3_with_retry, gen_single_clip_piper_with_retry, resolve_piper_model_path
from features.checkpoint_manager import CheckpointManager, save_progress_checkpoint, check_for_resume
from core import ui_manager
from features.auto_recovery import AutoRecovery, try_auto_recover, ErrorCategory
from features.memory_manager import optimize_memory, check_memory_status
from features.queue_manager import QueueManager
```

### B. Core Module Imports

**`core/utils.py`** - NO CHANGES (no local imports)

**`core/epub_io.py`** - Update:
```python
# OLD:
from config import HISTORY_DIR, HISTORY_FILE, ACTIVE_NOVELS_DIR, ARCHIVED_NOVELS_DIR
from utils import sanitize_filename, CP, logger

# NEW:
from core.config import HISTORY_DIR, HISTORY_FILE, ACTIVE_NOVELS_DIR, ARCHIVED_NOVELS_DIR
from core.utils import sanitize_filename, CP, logger
```

**`core/tts.py`** - Update:
```python
# OLD:
from config import CONFIG
from utils import CP, logger

# NEW:
from core.config import CONFIG
from core.utils import CP, logger
```

**`core/ui_manager.py`** - Update:
```python
# OLD:
from utils import CP, beep_notification
from config import CONFIG, CONFIG_FILE, logger
from queue_manager import QueueManager

# NEW:
from core.utils import CP, beep_notification
from core.config import CONFIG, CONFIG_FILE, logger
from features.queue_manager import QueueManager
```

### C. Feature Module Imports

**`features/chapter_merger.py`** - NO CHANGES (no local imports)

**`features/checkpoint_manager.py`** - NO CHANGES (no local imports)

**`features/queue_manager.py`** - NO CHANGES (no local imports)

**`features/memory_manager.py`** - NO CHANGES (no local imports)

**`features/auto_recovery.py`** - Update:
```python
# OLD:
from utils import CP, logger

# NEW:
from core.utils import CP, logger
```

### D. Test Module Imports

**`tests/test_auto_recovery.py`** - Update:
```python
# OLD:
from auto_recovery import AutoRecovery, ErrorCategory, try_auto_recover
from utils import CP

# NEW:
from features.auto_recovery import AutoRecovery, ErrorCategory, try_auto_recover
from core.utils import CP
```

**`tests/test_imports.py`** - This file needs complete rewrite for new structure

### E. System Validator

**`core/system_validator.py`** - Update:
```python
# OLD:
from utils import CP

# NEW:
from core.utils import CP
```

---

## 🧪 STEP 6: TESTING PLAN

1. **Test imports first:**
   ```bash
   python -c "from core import config, utils, tts, ui_manager, epub_io, system_validator; print('Core imports OK')"
   python -c "from features import chapter_merger, checkpoint_manager, queue_manager, memory_manager, auto_recovery; print('Features imports OK')"
   ```

2. **Run system validator:**
   ```bash
   python -m core.system_validator
   ```

3. **Test main script:**
   ```bash
   python epub_project_manager.py
   ```

4. **Run test suite:**
   ```bash
   python -m tests.test_imports
   python -m tests.test_ffmpeg
   ```

---

## 🗑️ STEP 7: CLEANUP (After Verification)

**Once everything works, delete old files:**
```
config.py (root)
utils.py (root)
epub_io.py (root)
tts.py (root)
ui_manager.py (root)
chapter_merger.py (root)
checkpoint_manager.py (root)
queue_manager.py (root)
memory_manager.py (root)
auto_recovery.py (root)
system_validator_merged.py (root)
health_check.py (root)
system_check.py (root)
system_validator.py (root)
debug_banner.py (root)
debug_display.py (root)
```

---

## 📊 FINAL STRUCTURE

```
idonotknowimadeagod/
├── epub_project_manager.py       # MAIN (imports updated)
├── safe_launcher.py               # Alternative launcher
├── debug_tools.py                 # Debug utilities (merged)
├── config.json                    # Configuration
├── background.mp3
├── *.bat files
│
├── core/                          
│   ├── __init__.py
│   ├── config.py ✅
│   ├── utils.py
│   ├── epub_io.py
│   ├── tts.py
│   ├── ui_manager.py
│   └── system_validator.py
│
├── features/                      
│   ├── __init__.py
│   ├── chapter_merger.py
│   ├── checkpoint_manager.py
│   ├── queue_manager.py
│   ├── memory_manager.py
│   └── auto_recovery.py
│
├── tests/                         
│   ├── __init__.py
│   ├── test_auto_recovery.py
│   ├── test_ffmpeg.py
│   ├── test_imports.py
│   └── test_voices.py
│
├── Novels/
├── _NEW_EPUBS_HERE/
├── piper/
└── piper_models/
```

---

## ⚡ QUICK COMMANDS TO EXECUTE

```powershell
# 1. Copy core files
copy utils.py core\utils.py
copy epub_io.py core\epub_io.py
copy tts.py core\tts.py
copy ui_manager.py core\ui_manager.py
move system_validator_merged.py core\system_validator.py

# 2. Copy feature files
copy chapter_merger.py features\chapter_merger.py
copy checkpoint_manager.py features\checkpoint_manager.py
copy queue_manager.py features\queue_manager.py
copy memory_manager.py features\memory_manager.py
copy auto_recovery.py features\auto_recovery.py

# 3. Copy test files
copy test_auto_recovery.py tests\test_auto_recovery.py
copy test_ffmpeg.py tests\test_ffmpeg.py
copy test_imports.py tests\test_imports.py
copy test_voices.py tests\test_voices.py
```

---

## ✅ COMPLETION CHECKLIST

- [ ] Step 1: Copy core files
- [ ] Step 2: Copy feature files  
- [ ] Step 3: Copy test files
- [ ] Step 4: Create debug_tools.py
- [ ] Step 5: Update imports in epub_project_manager.py
- [ ] Step 6: Update imports in core modules
- [ ] Step 7: Update imports in feature modules
- [ ] Step 8: Update imports in test modules
- [ ] Step 9: Test all imports
- [ ] Step 10: Run system validator
- [ ] Step 11: Test main script
- [ ] Step 12: Delete old files (after verification)

---

**NEXT ACTION:** Execute the PowerShell commands above, then I'll help you update the imports!
