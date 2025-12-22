import os
import json
from core.config import HISTORY_FILE

def clear_history():
    if not os.path.exists(HISTORY_FILE):
        print(f"History file not found: {HISTORY_FILE}")
        return

    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        # Filter out Marvel book
        new_history = {k: v for k, v in history.items() if "He is fighting against the Avengers in Marvel" not in k and "He_is_fighting_against_the_Avengers_in_Marvel" not in k}
        
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_history, f, indent=4)
        
        print(f"Successfully cleared Marvel history from {HISTORY_FILE}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clear_history()
