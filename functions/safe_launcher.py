import sys
import os
import subprocess

# Set window title directly
if sys.platform == "win32":
    subprocess.run(["cmd", "/c", "title", "Fanfiction Legend Manager (Safe Mode)"],
                  creationflags=0x08000000)  # CREATE_NO_WINDOW
else:
    sys.stdout.write("\033]0;Fanfiction Legend Manager (Safe Mode)\007")
    sys.stdout.flush()

print("Starting Safe Mode...")

try:
    from core import ui_manager
    import epub_project_manager
except ImportError:
    # Add usage of current directory
    sys.path.append(os.getcwd())
    try:
        from core import ui_manager
        import epub_project_manager
    except ImportError as e:
        print(f"Could not import main script: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

# Monkey patch the banner function to be simple text
def simple_banner():
    print("\n")
    print("   FANFICTION LEGEND MANAGER")
    print("   -------------------------")
    print("   (Safe Mode - No Graphics)")
    print("\n")

ui_manager.print_rainbow_banner = simple_banner

# Run the main function
if __name__ == "__main__":
    try:
        epub_project_manager.main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter...")
