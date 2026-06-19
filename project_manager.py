import json
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
import config
from models import DBProject, ProjectData

def create_project_id() -> str:
    return str(uuid.uuid4())

def save_project(db: Session, project_data: ProjectData) -> str:
    """Saves project to both SQLite Database and a JSON file."""
    
    # 1. Save to SQLite
    db_project = db.query(DBProject).filter(DBProject.id == project_data.id).first()
    if not db_project:
        db_project = DBProject(id=project_data.id)
        db.add(db_project)
    
    db_project.filename = project_data.filename
    # Do not save heavy text blocks in SQLite to prevent DB bloat
    db_project.extracted_text = ""
    db_project.corrected_text = ""
    db_project.metadata_json = project_data.book_metadata.model_dump() if project_data.book_metadata else None
    db_project.settings = project_data.settings.model_dump()
    db_project.performance_stats = project_data.performance.model_dump() if project_data.performance else None
    db_project.updated_at = datetime.utcnow()
    
    # Determine human-readable file path
    import re
    import os
    def sanitize(name):
        if not name: return ""
        return re.sub(r'[<>:"/\\|?*]', '', str(name)).strip()

    if project_data.book_metadata:
        m = project_data.book_metadata
        author = sanitize(m.author) if m.author else "Unknown Author"
        title = sanitize(m.title) if m.title else sanitize(project_data.filename)
        
        folder = config.BASE_DIR / "Library" / author
        folder.mkdir(parents=True, exist_ok=True)
        json_path = folder / f"{title}.json"
    else:
        folder = config.BASE_DIR / "Library" / "Unprocessed"
        folder.mkdir(parents=True, exist_ok=True)
        fname = sanitize(project_data.filename)
        if not fname.lower().endswith('.json'):
            fname += '.json'
        json_path = folder / fname

    # Delete old file if path changed
    if db_project.export_path and db_project.export_path != str(json_path):
        if os.path.exists(db_project.export_path):
            try:
                os.remove(db_project.export_path)
            except:
                pass

    db_project.export_path = str(json_path)

    db.commit()
    db.refresh(db_project)

    # 2. Save as Standalone JSON
    project_dict = project_data.model_dump()
    # convert datetime to string for JSON serialization
    project_dict['created_at'] = project_dict['created_at'].isoformat()
    project_dict['updated_at'] = project_dict['updated_at'].isoformat()
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(project_dict, f, indent=4, ensure_ascii=False)
        
    return project_data.id

def delete_project(db: Session, project_id: str):
    import os
    db_project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not db_project:
        return
        
    if db_project.export_path and os.path.exists(db_project.export_path):
        try:
            os.remove(db_project.export_path)
        except:
            pass
            
    # Also clean up legacy UUID path just in case
    legacy_path = config.PROJECTS_DIR / f"{project_id}.json"
    if legacy_path.exists():
        os.remove(legacy_path)
        
    db.delete(db_project)
    db.commit()

def load_project_from_json(project_id: str) -> ProjectData:
    """Loads a project from the JSON file."""
    json_path = config.PROJECTS_DIR / f"{project_id}.json"
    if not json_path.exists():
        raise FileNotFoundError(f"Project {project_id} not found in JSON files.")
        
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ProjectData(**data)

def load_project_from_db(db: Session, project_id: str) -> ProjectData:
    """Loads a project from the SQLite DB, but reads heavy text chunks from JSON to prevent DB bloat."""
    db_project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not db_project:
        raise ValueError(f"Project {project_id} not found in Database.")
        
    # Read the text fields directly from the Standalone JSON file to avoid SQLite bloat
    extracted_text = ""
    corrected_text = ""
    
    import os
    json_path = db_project.export_path
    if not json_path or not os.path.exists(json_path):
        json_path = config.PROJECTS_DIR / f"{project_id}.json"
        
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            extracted_text = data.get("extracted_text", "")
            corrected_text = data.get("corrected_text", "")
            
    return ProjectData(
        id=db_project.id,
        filename=db_project.filename,
        created_at=db_project.created_at,
        updated_at=db_project.updated_at,
        extracted_text=extracted_text,
        corrected_text=corrected_text,
        book_metadata=db_project.metadata_json,
        settings=db_project.settings,
        performance=db_project.performance_stats
    )

def list_all_projects(db: Session):
    """Returns a simplified list of all projects from the Database."""
    projects = db.query(DBProject).order_by(DBProject.created_at.desc()).all()
    return [
        {
            "id": p.id,
            "filename": p.filename,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "book_metadata": p.metadata_json
        }
        for p in projects
    ]
