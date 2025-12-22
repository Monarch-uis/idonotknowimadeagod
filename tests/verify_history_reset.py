
import os
import sys
import json
import hashlib
from datetime import datetime

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.utils import CP, logger
from core.epub_io import delete_book_from_history, load_history, HISTORY_FILE, calculate_epub_hash

def test_history_reset():
    print("\n   [Test] History Reset Logic...")
    
    # Setup mock history
    h_data = {
        "Test_Book": [
            {"start": 1, "end": 10, "epub_hash": "deadbeef", "date": "2023-01-01", "title": "Test Book"},
            {"start": 11, "end": 20, "epub_hash": "deadbeef", "date": "2023-01-02", "title": "Test Book"},
            {"start": 1, "end": 5, "epub_hash": "other", "date": "2023-01-01", "title": "Other Book"}
        ]
    }
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(h_data, f, indent=4)
        
    # We need to mock calculate_epub_hash to return 'deadbeef'
    import core.epub_io
    orig_hash = core.epub_io.calculate_epub_hash
    core.epub_io.calculate_epub_hash = lambda x: "deadbeef"
    
    try:
        # 1. Partial Reset (overlap with 1-10 and 11-20)
        print("      - Testing Partial Reset (Chapters 5-15)...")
        success, count = delete_book_from_history("dummy.epub", chapters=(5, 15))
        assert success == True
        assert count == 2 # Both 1-10 and 11-20 overlap with 5-15
        
        hist = load_history()
        assert len(hist.get("Test_Book", [])) == 1 # Only 'other' remains
        assert hist["Test_Book"][0]["epub_hash"] == "other"
        
        # 2. Reset Mock for Full Reset
        print("      - Testing Full Reset...")
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(h_data, f, indent=4)
            
        success, count = delete_book_from_history("dummy.epub", chapters=None)
        assert success == True
        assert count == 2
        hist = load_history()
        
        all_deadbeef_gone = True
        for k, entries in hist.items():
            for e in entries:
                if e.get('epub_hash') == 'deadbeef': all_deadbeef_gone = False
        assert all_deadbeef_gone == True
        
        print(CP("      ✅ Passed: History Reset (Partial & Full)", 'green'))
        
    finally:
        core.epub_io.calculate_epub_hash = orig_hash

if __name__ == "__main__":
    print(CP("🚀 Starting History Reset Verification", 'cyan'))
    try:
        test_history_reset()
        print(CP("\n✅ ALL TESTS PASSED!", 'green'))
    except Exception as e:
        print(CP(f"\n❌ TEST FAILED: {e}", 'red'))
        import traceback
        traceback.print_exc()
        sys.exit(1)
