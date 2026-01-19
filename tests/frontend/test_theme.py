import os

def test_tailwind_theme_config():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    # Check index.css for the new Tailwind v4 theme configuration
    config_path = os.path.join(root, "frontend", "src", "index.css")
    
    assert os.path.exists(config_path), "frontend/src/index.css missing"
    
    with open(config_path, "r") as f:
        content = f.read()
        
    # Check for Brutalist theme tokens in CSS variables
    assert "--color-brutal-black" in content, "Missing 'brutal-black' color variable"
    assert "--color-brutal-white" in content, "Missing 'brutal-white' color variable"
    assert "--font-display" in content, "Missing 'display' font family variable"
