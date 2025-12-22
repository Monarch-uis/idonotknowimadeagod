
import os
import sys

def patch_file():
    target_file = 'epub_project_manager.py'
    print(f"Patching {target_file}...")
    
    with open(target_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    patched = False
    
    for line in lines:
        if 'main_choice = input' in line and 'default 1' in line:
            new_lines.append('    if cli_args.input:\n')
            new_lines.append('        main_choice = "1"\n')
            new_lines.append('        print(f"\\n   ℹ️  Auto-selecting [1] via CLI")\n')
            new_lines.append('    else:\n')
            new_lines.append('        main_choice = input("\\n👉 Select option (default 1): ").strip()\n')
            patched = True
        else:
            new_lines.append(line)
            
    if patched:
        with open(target_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print("✅ Patch applied successfully")
    else:
        print("❌ Could not find target line to patch")

if __name__ == "__main__":
    patch_file()
