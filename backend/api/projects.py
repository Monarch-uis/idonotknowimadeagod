from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
from typing import List
from backend.models.project import Project, ProjectList, ProjectLogs
from core.config import ACTIVE_NOVELS_DIR, ARCHIVED_NOVELS_DIR, CONFIG
from core.epub_io import parse_full_epub, sanitize_filename, setup_project_folders
from features.queue_manager import QueueManager
from datetime import datetime
import json
import logging

logger = logging.getLogger("api.projects")

router = APIRouter(prefix="/api/projects", tags=["projects"])

def get_project_info(folder_path: str, status: str, queued_ids: List[str] = None) -> Project:
    title = os.path.basename(folder_path)
    profile_path = os.path.join(folder_path, "book_profile.json")
    author = "Unknown"
    last_updated = None
    
    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r") as f:
                profile = json.load(f)
                author = profile.get("author", "Unknown")
                last_updated = profile.get("last_updated")
        except:
            pass
            
    proj_id = sanitize_filename(title)
    # Check if project is in queue
    current_status = status
    if queued_ids and proj_id in queued_ids:
        current_status = "processing"

    return Project(
        id=proj_id,
        title=title,
        author=author,
        status=current_status,
        last_updated=last_updated,
        path=folder_path
    )

@router.get("", response_model=ProjectList)
async def list_projects():
    active = []
    archived = []
    
    # Get current queue to mark processing projects
    queued_ids = []
    try:
        qm = QueueManager()
        queued_ids = [sanitize_filename(os.path.basename(j["path"])) for j in qm.queue_data if j["status"] == "pending"]
    except:
        pass

    if os.path.exists(ACTIVE_NOVELS_DIR):
        for folder in os.listdir(ACTIVE_NOVELS_DIR):
            path = os.path.join(ACTIVE_NOVELS_DIR, folder)
            if os.path.isdir(path):
                active.append(get_project_info(path, "active", queued_ids))
                
    if os.path.exists(ARCHIVED_NOVELS_DIR):
        for folder in os.listdir(ARCHIVED_NOVELS_DIR):
            path = os.path.join(ARCHIVED_NOVELS_DIR, folder)
            if os.path.isdir(path):
                archived.append(get_project_info(path, "archived", queued_ids))
                
    return ProjectList(active=active, archived=archived)

@router.post("", response_model=Project, status_code=201)
async def create_project(file: UploadFile = File(...)):
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file.filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        meta, chapters, book = parse_full_epub(temp_path)
        if not meta:
            raise HTTPException(status_code=400, detail="Invalid EPUB file")
            
        paths = setup_project_folders(meta["title"], ACTIVE_NOVELS_DIR)
        dest_epub_path = os.path.join(paths["epub"], file.filename)
        shutil.move(temp_path, dest_epub_path)
        
        profile = {
            "title": meta["title"],
            "author": meta["author"],
            "epub_path": dest_epub_path,
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
        
    error_log_path = "logs/errors/errors.log"
    logs = []
    
    if os.path.exists(error_log_path):
        try:
            with open(error_log_path, "r") as f:
                lines = f.readlines()
                for line in lines[-100:]:
                    if project_id.lower() in line.lower() or os.path.basename(project_path).lower() in line.lower():
                        logs.append(line.strip())
        except:
            pass
            
    return ProjectLogs(project_id=project_id, logs=logs)

@router.post("/{project_id}/process")
async def process_project(project_id: str, settings: dict = None):
    project_path = None
    for folder in os.listdir(ACTIVE_NOVELS_DIR):
        if sanitize_filename(folder) == project_id:
            project_path = os.path.join(ACTIVE_NOVELS_DIR, folder)
            break
            
    if not project_path:
        raise HTTPException(status_code=404, detail="Project not found")
        
    profile_path = os.path.join(project_path, "book_profile.json")
    if not os.path.exists(profile_path):
        raise HTTPException(status_code=400, detail="Project profile missing")
        
    try:
        with open(profile_path, "r") as f:
            profile = json.load(f)
            
        epub_path = profile.get("epub_path")
        if not epub_path or not os.path.exists(epub_path):
            source_dir = os.path.join(project_path, "source_epub")
            if os.path.exists(source_dir):
                files = os.listdir(source_dir)
                if files:
                    epub_path = os.path.join(source_dir, files[0])
                    
        if not epub_path:
            raise HTTPException(status_code=400, detail="EPUB source file not found")

        qm = QueueManager()
        
        # Construct final settings
        final_settings = {
            "engine": "edge-tts",
            "voice": CONFIG["audio_settings"]["voice"],
            "speed": CONFIG["audio_settings"]["tts_speed_default"],
            "quality": CONFIG["video_settings"]["current_quality_preset"],
            "batch_size": CONFIG["system_limits"]["max_batch_size"]
        }
        
        if settings:
            final_settings.update(settings)
        
        job = qm.add_to_queue(
            epub_path=epub_path,
            settings=final_settings,
            title=profile.get("title", project_id),
            original_title=profile.get("title", project_id)
        )
        
        if not job:
            raise HTTPException(status_code=500, detail="Failed to add to processing queue")
            
        return {"status": "queued", "job_id": job["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
