import asyncio
import difflib
import json
from typing import Dict, Any, List
from datetime import datetime

import config
from llm.llm_manager import get_llm_provider
from project_manager import load_project_from_db, save_project
from database import SessionLocal
from models import DBProject

ocr_jobs: Dict[str, Dict[str, Any]] = {}

def get_job_status(project_id: str) -> Dict[str, Any]:
    return ocr_jobs.get(project_id, {"status": "none"})

def stop_ocr_job(project_id: str):
    if project_id in ocr_jobs and ocr_jobs[project_id]["status"] == "running":
        ocr_jobs[project_id]["status"] = "stopped"

def overlap_chunk_text(text: str, chunk_words: int = 2000, overlap_words: int = 50) -> List[str]:
    """Splits text into chunks of approx `chunk_words` with `overlap_words` overlap."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_words])
        chunks.append(chunk)
        if i + chunk_words >= len(words):
            break
        i += (chunk_words - overlap_words)
    return chunks

def merge_overlapping_text(text_a: str, text_b: str) -> str:
    """Uses SequenceMatcher to find the longest matching overlap between the end of A and start of B and merges them cleanly."""
    if not text_a: return text_b
    if not text_b: return text_a
    
    search_a = text_a[-1000:] if len(text_a) > 1000 else text_a
    search_b = text_b[:1000] if len(text_b) > 1000 else text_b

    s = difflib.SequenceMatcher(None, search_a, search_b)
    match = s.find_longest_match(0, len(search_a), 0, len(search_b))
    
    if match.size > 10:
        overlap_end_index_in_b = match.b + match.size
        clean_text_b = text_b[overlap_end_index_in_b:]
        return text_a + clean_text_b
    else:
        return text_a + " " + text_b

def extract_diffs(original: str, corrected: str) -> List[str]:
    """Uses difflib to extract a human-readable list of changes."""
    import re
    orig_words = re.findall(r'\S+|\n', original)
    corr_words = re.findall(r'\S+|\n', corrected)
    
    matcher = difflib.SequenceMatcher(None, orig_words, corr_words)
    diffs = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            old = " ".join(orig_words[i1:i2]).replace('\n', ' ').strip()
            new = " ".join(corr_words[j1:j2]).replace('\n', ' ').strip()
            if old and new:
                diffs.append(f"Fixed: '{old}' -> '{new}'")
        elif tag == 'delete':
            old = " ".join(orig_words[i1:i2]).replace('\n', ' ').strip()
            if old:
                diffs.append(f"Deleted: '{old}'")
        elif tag == 'insert':
            new = " ".join(corr_words[j1:j2]).replace('\n', ' ').strip()
            if new:
                diffs.append(f"Inserted: '{new}'")
    
    return diffs

def run_ocr_pipeline(project_id: str, system_prompt: str = ""):
    db = SessionLocal()
    try:
        project = load_project_from_db(db, project_id)
        if not project.extracted_text:
            ocr_jobs[project_id] = {"status": "error", "error_msg": "No extracted text found."}
            return

        chunks = overlap_chunk_text(project.extracted_text, chunk_words=config.OCR_CHUNK_WORDS, overlap_words=config.OCR_OVERLAP_WORDS)
        
        ocr_jobs[project_id] = {
            "status": "running",
            "total_chunks": len(chunks),
            "chunks_sent": 0,
            "chunks_received": 0,
            "eta_seconds": 0,
            "stitched_text": "",
            "corrections": [],
            "error_msg": "",
            "llm_stats": {}
        }

        llm = get_llm_provider()
        
        if not system_prompt.strip():
            system_prompt = """You are an expert editor and OCR correction AI. 
Fix any OCR scanning errors, typos, and formatting artifacts in the text. 
Pay special attention to words that may have been accidentally split by spaces or line breaks.
Do not rewrite or alter the author's words.

Return strictly in JSON format:
{
    "corrected_text": "..."
}"""

        stitched_text = ""
        all_corrections = []
        
        start_time = datetime.now()

        for i, chunk in enumerate(chunks):
            if ocr_jobs[project_id]["status"] == "stopped":
                break

            ocr_jobs[project_id]["chunks_sent"] = i + 1
            
            try:
                def chunk_callback(text, tokens, elapsed):
                    if project_id in ocr_jobs:
                        ocr_jobs[project_id]["llm_stats"] = {
                            "tokens_received": tokens,
                            "elapsed": elapsed,
                            "speed_tps": (tokens / elapsed) if elapsed > 0 else 0
                        }

                result_dict = llm.process_custom_json_stream(system_prompt, f"Here is the text:\n\n{chunk}", chunk_callback)
                
                corrected_chunk = result_dict.get("corrected_text", chunk)
                
                # Extract Python Diffs
                chunk_corrections = extract_diffs(chunk, corrected_chunk)
                
                stitched_text = merge_overlapping_text(stitched_text, corrected_chunk)
                all_corrections.extend(chunk_corrections)
                
                ocr_jobs[project_id]["stitched_text"] = stitched_text
                ocr_jobs[project_id]["corrections"] = all_corrections
                
            except Exception as e:
                print(f"Error processing chunk {i}: {e}")
                stitched_text = merge_overlapping_text(stitched_text, chunk)
                ocr_jobs[project_id]["stitched_text"] = stitched_text

            # Update received and ETA
            ocr_jobs[project_id]["chunks_received"] = i + 1
            elapsed = (datetime.now() - start_time).total_seconds()
            avg_time = elapsed / (i + 1)
            remaining_chunks = len(chunks) - (i + 1)
            ocr_jobs[project_id]["eta_seconds"] = int(avg_time * remaining_chunks)

        if ocr_jobs[project_id]["status"] != "stopped":
            # Save the fully corrected text to the DB
            project.corrected_text = stitched_text
            save_project(db, project)
            ocr_jobs[project_id]["status"] = "completed"

    except Exception as e:
        if project_id in ocr_jobs:
            ocr_jobs[project_id]["status"] = "error"
            ocr_jobs[project_id]["error_msg"] = str(e)
    finally:
        db.close()
