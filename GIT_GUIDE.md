# 🌿 Gemini Project: Git Branching Guide

This guide outlines our **AI-Optimized GitHub Flow** strategy to keep development clean, safe, and experimental.

## 🚀 The Main Branch
The `main` branch is always **stable** and **production-ready**. 
> [!IMPORTANT]
> Never commit experimental or broken code directly to `main`.

---

## 🏗️ Branch Naming Conventions
Always create a new branch for your work. Use these prefixes:

| Prefix | Description | Example |
| :--- | :--- | :--- |
| `feature/` | New tools, logic, or UI components. | `feature/dynamic-subtitles` |
| `fix/` | Bug fixes and reliability improvements. | `fix/memory-leak-render` |
| `ai-exp/` | Experiments with Gemini prompts, models, or workflows. | `ai-exp/gemini-flash-tuning` |
| `chore/` | Maintenance, dependencies, or docs. | `chore/update-readme` |

---

## 🛠️ Common Workflows

### 1. Starting a New Feature
```bash
# Ensure you are on main and up to date
git checkout main
git pull origin main

# Create and switch to your new branch
git checkout -b feature/your-feature-name
```

### 2. Saving Your Work
```bash
git add .
git commit -m "feat: descriptive message about what you did"
```

### 3. Merging Changes (Local Flow)
Once your work is tested and solid:
```bash
# Switch back to main
git checkout main

# Merge your branch
git merge feature/your-feature-name

# Delete the feature branch (optional but recommended)
git branch -d feature/your-feature-name
```

---

## 🧪 AI Experimentation (`ai-exp/`)
Since AI behavior can be unpredictable, use `ai-exp/` branches to test new `config.json` prompt templates or Gemini API logic. Only merge these to `main` once you've confirmed they improve the output quality.
