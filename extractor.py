import io
import fitz  # PyMuPDF
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from docx import Document
import config

def extract_text(file_bytes: bytes, filename: str) -> str:
    """Extracts text based on file extension."""
    ext = filename.lower().split('.')[-1]
    
    text = ""
    if ext == "pdf":
        text = extract_from_pdf(file_bytes)
    elif ext == "epub":
        text = extract_from_epub(file_bytes)
    elif ext == "docx" or ext == "doc":
        text = extract_from_docx(file_bytes)
    elif ext in ["txt", "json", "md"]:
        text = file_bytes.decode('utf-8', errors='ignore')
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
        
    return text

def extract_from_pdf(file_bytes: bytes) -> str:
    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text() + "\n"
    return text

def extract_from_epub(file_bytes: bytes) -> str:
    # Need to save bytes to a temporary object to read with ebooklib
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as temp:
        temp.write(file_bytes)
        temp_path = temp.name
        
    text = ""
    try:
        book = epub.read_epub(temp_path)
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_body_content(), 'html.parser')
                text += soup.get_text() + "\n"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    return text

def extract_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join([p.text for p in doc.paragraphs])
