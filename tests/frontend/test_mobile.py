import os

def test_mobile_responsiveness_tokens():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    hero_path = os.path.join(root, "frontend", "src", "components", "Hero.tsx")
    dashboard_path = os.path.join(root, "frontend", "src", "components", "Dashboard.tsx")
    
    # Check Hero for mobile-specific classes
    with open(hero_path, "r") as f:
        hero_content = f.read()
        assert "md:text-" in hero_content, "Hero missing responsive text sizes"
        assert "flex-col" in hero_content, "Hero missing mobile flex direction"

    # Check Dashboard for mobile grid
    with open(dashboard_path, "r") as f:
        dash_content = f.read()
        assert "grid-cols-1" in dash_content, "Dashboard missing mobile single column grid"
        assert "md:grid-cols-2" in dash_content, "Dashboard missing responsive grid columns"
