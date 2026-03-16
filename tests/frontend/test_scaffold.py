import os

def test_frontend_scaffold_exists():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    frontend_dir = os.path.join(root, "frontend")
    
    assert os.path.exists(os.path.join(frontend_dir, "package.json")), "frontend/package.json missing"
    assert os.path.exists(os.path.join(frontend_dir, "vite.config.ts")), "frontend/vite.config.ts missing"
    assert os.path.exists(os.path.join(frontend_dir, "src", "App.tsx")), "frontend/src/App.tsx missing"
