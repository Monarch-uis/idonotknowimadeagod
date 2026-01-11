import os

def test_tailwind_theme_config():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    config_path = os.path.join(root, "frontend", "tailwind.config.js")
    
    assert os.path.exists(config_path), "tailwind.config.js missing"
    
    with open(config_path, "r") as f:
        content = f.read()
        
    # Check for Brutalist theme tokens
    assert "brutal-black" in content, "Missing 'brutal-black' color"
    assert "brutal-white" in content, "Missing 'brutal-white' color"
    assert "display" in content, "Missing 'display' font family"
