from sqlmodel import SQLModel, Field, JSON, Column
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import Index, text


class AgentTrace(SQLModel, table=True):
    """
    Stores the complete trace of an agent's reasoning process.
    The grounding_metadata field uses JSON for storing nested source data.

    Deduplication: A unique hash index on response_text silently drops
    identical responses so the caller receives {"duplicate": true} instead
    of an error.
    """
    __table_args__ = (
        Index('idx_response_hash', text('md5(response_text)'), unique=True),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    prompt: str
    response_text: str = Field(index=True)
    # The 'receipts' - where Gemini got its info
    grounding_metadata: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    is_hallucinated: bool = Field(default=False)
    detection_reason: Optional[str] = Field(default=None, nullable=True)
