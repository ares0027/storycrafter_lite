import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# SQLAlchemy DB Models
class DBProject(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, index=True)
    filename = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Extracted data
    extracted_text = Column(Text)
    corrected_text = Column(Text)
    metadata_json = Column(JSON)
    story_bible_json = Column(JSON)
    
    # Settings used
    settings = Column(JSON)
    
    # Performance metrics
    performance_stats = Column(JSON)
    
    # Save Path
    export_path = Column(String)

# Pydantic Models for FastAPI and type hinting
class BookMetadata(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    details: Optional[str] = None
    genre: Optional[str] = None
    style: Optional[str] = None
    target_audience: Optional[str] = None
    publish_date: Optional[str] = None
    original_language: Optional[str] = None
    provided_language: Optional[str] = None
    is_translation: Optional[bool] = None
    translator: Optional[str] = None

class PerformanceStats(BaseModel):
    cpu_usage_percent: float = 0.0
    ram_usage_mb: float = 0.0
    gpu_usage_percent: Optional[float] = None
    vram_usage_mb: Optional[float] = None
    tokens_sent: int = 0
    tokens_received: int = 0
    total_time_seconds: float = 0.0
    tokens_per_second: float = 0.0

class ProjectConfig(BaseModel):
    words_extracted: int
    llm_provider: str
    llm_model: str

class ProjectData(BaseModel):
    id: str
    filename: str
    created_at: datetime
    updated_at: datetime
    extracted_text: str
    corrected_text: Optional[str] = None
    book_metadata: Optional[BookMetadata] = None
    settings: ProjectConfig
    performance: Optional[PerformanceStats] = None

class DBStyleProfile(Base):
    __tablename__ = "style_profiles"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), index=True)
    source_book_name = Column(String)
    language_specific_json = Column(Text)
    neutral_agnostic_json = Column(Text)
    status = Column(String, default="Pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DBStoryNode(Base):
    __tablename__ = "story_nodes"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), index=True)
    parent_id = Column(String, index=True, nullable=True)
    content = Column(Text)
    chapter_num = Column(Integer, nullable=True)
    prompt_used = Column(Text, nullable=True)
    llm_model = Column(String, nullable=True)
    vram_used = Column(Float, nullable=True)
    tokens_per_second = Column(Float, nullable=True)
    is_approved = Column(Boolean, default=False)
    is_active_head = Column(Boolean, default=False)
    embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DBStory(Base):
    __tablename__ = "stories"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String)
    status = Column(String, default="Draft")
    global_mascot_prompt = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class DBScene(Base):
    __tablename__ = "scenes"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    story_id = Column(String, index=True)
    chronological_order = Column(Integer)
    scene_type = Column(String, default="Story")
    render_status = Column(String, default="Draft")

class DBAssetVersion(Base):
    __tablename__ = "asset_versions"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    scene_id = Column(String, index=True)
    text_content = Column(Text)

class ChunkStateUpdate(BaseModel):
    language_specific_rules: str
    neutral_agnostic_rules: str
    new_vocabulary_found: List[str]

class LanguageSpecificProfile(BaseModel):
    translator_notes: str
    original_language_idioms: List[str]
    literal_vocabulary_lexicon: List[str]

class NeutralAgnosticProfile(BaseModel):
    pacing_and_rhythm: str
    dialogue_density: float
    sentence_variance: str
    narrative_pov: str
    cynicism_optimism_ratio: int = Field(..., ge=1, le=10)
    vocabulary_tier: str
    prose_guidelines: str

class StoryNode(BaseModel):
    id: str
    project_id: str
    parent_id: Optional[str] = None
    content: str
    chapter_num: Optional[int] = None
    prompt_used: Optional[str] = None
    llm_model: Optional[str] = None
    vram_used: Optional[float] = None
    tokens_per_second: Optional[float] = None
    is_approved: bool = False
    is_active_head: bool = False
    embedding: Optional[Any] = None
    created_at: datetime
    updated_at: datetime
