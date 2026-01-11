from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
from typing import List
from backend.models.project import Project, ProjectList, ProjectLogs
from core.config import ACTIVE_NOVELS_DIR, ARCHIVED_NOVELS_DIR
from core.epub_io import parse_full_epub, sanitize_filename, setup_project_folders
from datetime import datetime

router = APIRouter(prefix="/api/projects", tags=["projects"])

def get_project_info(folder_path: str, status: str) -> Project:
    title = os.path.basename(folder_path)
    # Try to load book_profile.json if it exists
    profile_path = os.path.join(folder_path, "book_profile.json")
    author = "Unknown"
    last_updated = None
    
    if os.path.exists(profile_path):
        import json
        try:
            with open(profile_path, "r") as f:
                profile = json.load(f)
                author = profile.get("author", "Unknown")
                last_updated = profile.get("last_updated")
        except:
            pass
            
    return Project(
        id=sanitize_filename(title),
        title=title,
        author=author,
        status=status,
        last_updated=last_updated,
        path=folder_path
    )

@router.get("", response_model=ProjectList)
async def list_projects():
    active = []
    archived = []
    
    if os.path.exists(ACTIVE_NOVELS_DIR):
        for folder in os.listdir(ACTIVE_NOVELS_DIR):
            path = os.path.join(ACTIVE_NOVELS_DIR, folder)
            if os.path.isdir(path):
                active.append(get_project_info(path, "active"))
                
    if os.path.exists(ARCHIVED_NOVELS_DIR):
        for folder in os.listdir(ARCHIVED_NOVELS_DIR):
            path = os.path.join(ARCHIVED_NOVELS_DIR, folder)
            if os.path.isdir(path):
                archived.append(get_project_info(path, "archived"))
                
    return ProjectList(active=active, archived=archived)

@router.post("", response_model=Project, status_code=201)
async def create_project(file: UploadFile = File(...)):
    # 1. Save temporary EPUB
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file.filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # 2. Parse EPUB
        meta, chapters, book = parse_full_epub(temp_path)
        if not meta:
            raise HTTPException(status_code=400, detail="Invalid EPUB file")
            
        # 3. Initialize project folders
        paths = setup_project_folders(meta["title"], ACTIVE_NOVELS_DIR)
        
        # 4. Save EPUB to project
        dest_epub_path = os.path.join(paths["epub"], file.filename)
        shutil.move(temp_path, dest_epub_path)
        
        # 5. Save initial book profile
        import json
        profile = {
            "title": meta["title"],
            "author": meta["author"],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(os.path.join(paths["root"], "book_profile.json"), "w") as f:
            json.dump(profile, f, indent=4)
            
        return get_project_info(paths["root"], "active")
        
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}/logs", response_model=ProjectLogs)
async def get_project_logs(project_id: str):
    # Check if project exists in active or archived
    project_path = None
    for root_dir in [ACTIVE_NOVELS_DIR, ARCHIVED_NOVELS_DIR]:
        if not os.path.exists(root_dir):
            continue
        for folder in os.listdir(root_dir):
            if sanitize_filename(folder) == project_id:
                project_path = os.path.join(root_dir, folder)
                break
        if project_path:
            break
            
    if not project_path:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Read from global error log
    error_log_path = "logs/errors/errors.log"
    logs = []
    
    if os.path.exists(error_log_path):
        try:
            with open(error_log_path, "r") as f:
                # Read last 100 lines and filter
                lines = f.readlines()
                for line in lines[-100:]:
                    # Check if project_id or folder name is in line
                    if project_id.lower() in line.lower() or os.path.basename(project_path).lower() in line.lower():
                        logs.append(line.strip())
        except:
            pass
            
    return ProjectLogs(project_id=project_id, logs=logs)