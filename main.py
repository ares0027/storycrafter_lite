import os
import time
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import config
from database import init_db, get_db
from extractor import extract_text
from llm.llm_manager import get_llm_provider
from performance import get_system_stats, calculate_performance
from project_manager import create_project_id, save_project, load_project_from_db
from models import ProjectData, ProjectConfig, BookMetadata

app = FastAPI(title="Storycrafter API")

# Initialize database
init_db()



from services.websocket_logger import manager

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, wait for client messages if any
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=FileResponse)
async def read_root():
    return FileResponse("templates/index.html")

@app.get("/api/config")
async def get_configuration():
    return {
        "LLM_PROVIDER": config.LLM_PROVIDER,
        "LLM_BASE_URL": config.LLM_BASE_URL,
        "LLM_PORT": config.LLM_PORT,
        "LLM_MODEL_NAME": config.LLM_MODEL_NAME,
        "WORDS_TO_EXTRACT": config.WORDS_TO_EXTRACT,
        "EXTRACTOR_SYSTEM_PROMPT": config.EXTRACTOR_SYSTEM_PROMPT,
        "OCR_CHUNK_WORDS": config.OCR_CHUNK_WORDS,
        "OCR_OVERLAP_WORDS": config.OCR_OVERLAP_WORDS
    }

@app.post("/api/config")
async def update_configuration(new_config: dict):
    print(f"[DEBUG main] Received configuration update: {new_config}")
    for key, value in new_config.items():
        if hasattr(config, key):
            config.update_config(key, value)
    return {"status": "success", "config": await get_configuration()}

@app.get("/api/models")
async def get_models():
    provider = get_llm_provider()
    models = provider.get_models()
    return {"models": models}

# --- OCR Endpoints ---
class OCRStartRequest(BaseModel):
    system_prompt: str = ""

@app.post("/api/project/{project_id}/ocr_start")
async def start_ocr(project_id: str, req: OCRStartRequest, background_tasks: BackgroundTasks):
    from ocr_service import run_ocr_pipeline, get_job_status
    status = get_job_status(project_id)
    if status.get("status") == "running":
        return {"status": "error", "message": "OCR job is already running."}
    
    background_tasks.add_task(run_ocr_pipeline, project_id, req.system_prompt)
    return {"status": "success", "message": "OCR job started."}

@app.get("/api/project/{project_id}/ocr_status")
async def get_ocr_status(project_id: str):
    from ocr_service import get_job_status
    return get_job_status(project_id)

@app.post("/api/project/{project_id}/ocr_stop")
async def stop_ocr(project_id: str):
    from ocr_service import stop_ocr_job
    stop_ocr_job(project_id)
    return {"status": "success"}

@app.get("/api/llm/check")
async def check_llm_connection():
    provider = get_llm_provider()
    is_connected = provider.check_connection()
    return {"status": "success" if is_connected else "error", "connected": is_connected}

@app.post("/api/llm/unload")
async def unload_llm_model():
    provider = get_llm_provider()
    success = provider.unload_model()
    return {"status": "success" if success else "error"}

@app.get("/api/performance")
async def get_performance():
    return get_system_stats()

@app.get("/api/projects")
async def get_projects(db: Session = Depends(get_db)):
    from project_manager import list_all_projects
    projects = list_all_projects(db)
    return {"status": "success", "projects": projects}

@app.get("/api/project/{project_id}")
async def get_project(project_id: str, db: Session = Depends(get_db)):
    try:
        project = load_project_from_db(db, project_id)
        return {"status": "success", "project": project.model_dump()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/project/{project_id}")
async def save_project_metadata(project_id: str, metadata: BookMetadata, db: Session = Depends(get_db)):
    from datetime import datetime
    try:
        project = load_project_from_db(db, project_id)
        project.book_metadata = metadata
        project.updated_at = datetime.utcnow()
        save_project(db, project)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.delete("/api/project/{project_id}")
async def api_delete_project(project_id: str, db: Session = Depends(get_db)):
    try:
        from project_manager import delete_project
        delete_project(db, project_id)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/upload_book")
async def upload_book(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_bytes = await file.read()
    extracted_text = extract_text(file_bytes, file.filename)
    
    from datetime import datetime
    project_id = create_project_id()
    project_data = ProjectData(
        id=project_id,
        filename=file.filename,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        extracted_text=extracted_text,
        corrected_text="",
        settings=ProjectConfig(
            words_extracted=config.WORDS_TO_EXTRACT,
            llm_provider=config.LLM_PROVIDER,
            llm_model=config.LLM_MODEL_NAME
        )
    )
    save_project(db, project_data)
    
    return {
        "status": "success",
        "project": project_data.model_dump()
    }

@app.post("/api/project/{project_id}/ask_llm")
async def ask_llm(project_id: str, db: Session = Depends(get_db)):
    try:
        project = load_project_from_db(db, project_id)
    except Exception as e:
        return {"status": "error", "message": str(e)}

    start_time = time.time()
    llm = get_llm_provider()
    
    try:
        words = project.extracted_text.split()
        if len(words) > project.settings.words_extracted:
            text_to_process = " ".join(words[:project.settings.words_extracted])
        else:
            text_to_process = project.extracted_text
            
        corrected_text, metadata_dict, tokens_sent, tokens_received = llm.process_text(text_to_process)
    except Exception as e:
        print(f"LLM Processing Error: {e}")
        return {"status": "error", "message": f"LLM error: {str(e)}"}
        
    end_time = time.time()
    perf_stats = calculate_performance(start_time, end_time, tokens_sent, tokens_received)
    
    project.corrected_text = corrected_text
    project.book_metadata = BookMetadata(**metadata_dict) if metadata_dict else None
    project.performance = perf_stats
    
    save_project(db, project)
    
    return {
        "status": "success",
        "project": project.model_dump()
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.SERVER_HOST, port=config.SERVER_PORT, reload=True)
