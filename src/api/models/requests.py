"""Request models for the Ad Retrieval API."""

from typing import List, Optional
from pydantic import BaseModel, Field


class UserContext(BaseModel):
    """User context information for ad targeting."""
    
    gender: Optional[str] = Field(None, description="User gender")
    age: Optional[int] = Field(None, ge=0, le=120, description="User age")
    location: Optional[str] = Field(None, description="User location (e.g., 'San Francisco, CA')")
    interests: Optional[List[str]] = Field(None, description="User interests")
    
    class Config:
        json_schema_extra = {
            "example": {
                "gender": "male",
                "age": 24,
                "location": "San Francisco, CA",
                "interests": ["fitness", "outdoor activities"]
            }
        }


class RetrievalRequest(BaseModel):
    """Request for ad retrieval."""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="User's natural language query"
    )
    context: Optional[UserContext] = Field(
        None,
        description="Optional user context for targeting"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "I'm running a marathon next month and need new shoes. What should I get?",
                "context": {
                    "gender": "male",
                    "age": 24,
                    "location": "San Francisco, CA",
                    "interests": ["fitness", "outdoor activities"]
                }
            }
        }
