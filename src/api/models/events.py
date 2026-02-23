"""Event models for Graphiti knowledge graph."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CampaignImpression(BaseModel):
    """Campaign impression event for tracking which campaigns were shown."""
    
    campaign_id: str = Field(..., description="Unique campaign identifier")
    position: int = Field(..., ge=0, description="Position in results (0-indexed)")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    category: str = Field(..., description="Campaign category")
    
    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": "camp_00123",
                "position": 0,
                "relevance_score": 0.94,
                "category": "running_shoes"
            }
        }


class QueryEvent(BaseModel):
    """Query event for recording user queries and results."""
    
    query: str = Field(..., min_length=1, max_length=500, description="User query text")
    context: Optional[Dict] = Field(None, description="User context (age, gender, location, interests)")
    eligibility: float = Field(..., ge=0.0, le=1.0, description="Ad eligibility score")
    categories: List[str] = Field(..., min_length=1, max_length=10, description="Extracted categories")
    campaigns: List[CampaignImpression] = Field(
        default_factory=list,
        max_length=10,
        description="Top campaigns shown (max 10)"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    session_id: Optional[str] = Field(None, description="Session identifier for tracking user journeys")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "running shoes for marathon",
                "context": {
                    "age": 30,
                    "gender": "male",
                    "location": "San Francisco, CA",
                    "interests": ["fitness", "running"]
                },
                "eligibility": 0.95,
                "categories": ["running_shoes", "marathon_gear"],
                "campaigns": [
                    {
                        "campaign_id": "camp_00123",
                        "position": 0,
                        "relevance_score": 0.94,
                        "category": "running_shoes"
                    }
                ],
                "timestamp": "2026-02-22T20:00:00Z",
                "session_id": "sess_abc123"
            }
        }


class UserSession(BaseModel):
    """User session for tracking query patterns over time."""
    
    session_id: str = Field(..., description="Unique session identifier")
    user_id: Optional[str] = Field(None, description="User identifier if available")
    start_time: datetime = Field(default_factory=datetime.utcnow, description="Session start time")
    end_time: Optional[datetime] = Field(None, description="Session end time")
    query_count: int = Field(default=0, ge=0, description="Number of queries in session")
    queries: List[str] = Field(default_factory=list, description="List of queries in session")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "user_id": "user_456",
                "start_time": "2026-02-22T20:00:00Z",
                "end_time": "2026-02-22T20:15:00Z",
                "query_count": 3,
                "queries": [
                    "running shoes",
                    "marathon training plan",
                    "running watch"
                ]
            }
        }


class GraphitiEpisode(BaseModel):
    """Episode model for Graphiti knowledge graph ingestion."""
    
    name: str = Field(..., description="Unique episode name")
    episode_body: str = Field(..., min_length=1, description="Episode text content")
    source_description: str = Field(default="Ad Retrieval Query", description="Source of the episode")
    reference_time: datetime = Field(default_factory=datetime.utcnow, description="Reference time for temporal graph")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "query_2026-02-22_20-00-00_abc123",
                "episode_body": "User searched for 'running shoes for marathon'. Context: 30 year old male from San Francisco, CA interested in fitness and running. Ad eligibility: 0.95. Extracted categories: running_shoes, marathon_gear. Top campaign shown: Nike Premium Running Shoes (relevance: 0.94).",
                "source_description": "Ad Retrieval Query",
                "reference_time": "2026-02-22T20:00:00Z"
            }
        }
