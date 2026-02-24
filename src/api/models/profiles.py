"""User profile models for intent inference and personalization."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class InferredIntent(BaseModel):
    """Detected user intent from query pattern analysis."""
    
    intent_type: str = Field(..., description="Type of intent (e.g., 'marathon_planning', 'vacation_planning')")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for this intent")
    evidence: List[str] = Field(default_factory=list, description="Supporting queries that led to this inference")
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="When this intent was detected")
    expires_at: datetime = Field(..., description="When this intent expires (time-based decay)")
    inferred_categories: List[str] = Field(
        default_factory=list,
        description="Categories to boost based on this intent"
    )
    metadata: Dict = Field(
        default_factory=dict,
        description="Additional metadata (e.g., location, dates, rule_id)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "intent_type": "marathon_planning",
                "confidence": 0.85,
                "evidence": [
                    "best marathon running shoes",
                    "Boston weather in April",
                    "hotels near Boston Marathon"
                ],
                "detected_at": "2026-02-24T10:00:00Z",
                "expires_at": "2026-04-24T10:00:00Z",
                "inferred_categories": ["airfare", "travel_packages", "car_rental"],
                "metadata": {
                    "location": "Boston",
                    "event_month": "April",
                    "rule_id": "marathon_planning"
                }
            }
        }


class QueryHistoryItem(BaseModel):
    """Single query in user's history."""
    
    query: str = Field(..., description="Query text")
    categories: List[str] = Field(default_factory=list, description="Extracted categories")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Query timestamp")
    location: Optional[str] = Field(None, description="Location mentioned or from context")
    session_id: Optional[str] = Field(None, description="Session this query belongs to")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "best marathon running shoes",
                "categories": ["running_shoes", "athletic_footwear"],
                "timestamp": "2026-02-24T10:00:00Z",
                "location": None,
                "session_id": "sess_abc123"
            }
        }


class UserProfile(BaseModel):
    """Aggregated user profile with inferred attributes."""
    
    user_id: str = Field(..., description="User identifier")
    session_ids: List[str] = Field(default_factory=list, description="Associated session IDs")
    query_history: List[QueryHistoryItem] = Field(
        default_factory=list,
        max_length=50,
        description="Recent queries (last 50)"
    )
    inferred_intents: List[InferredIntent] = Field(
        default_factory=list,
        description="Active inferred intents"
    )
    inferred_categories: List[str] = Field(
        default_factory=list,
        description="Categories to boost based on all active intents"
    )
    aggregated_interests: List[str] = Field(
        default_factory=list,
        description="Interests aggregated from context + inferred"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last profile update timestamp"
    )
    query_count: int = Field(default=0, ge=0, description="Total queries from this user")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Profile creation timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_12345",
                "session_ids": ["sess_abc123", "sess_def456"],
                "query_history": [
                    {
                        "query": "best marathon running shoes",
                        "categories": ["running_shoes"],
                        "timestamp": "2026-02-24T10:00:00Z",
                        "location": None,
                        "session_id": "sess_abc123"
                    },
                    {
                        "query": "Boston weather in April",
                        "categories": ["weather"],
                        "timestamp": "2026-02-24T10:05:00Z",
                        "location": "Boston",
                        "session_id": "sess_abc123"
                    }
                ],
                "inferred_intents": [
                    {
                        "intent_type": "marathon_planning",
                        "confidence": 0.85,
                        "evidence": ["best marathon running shoes", "Boston weather in April"],
                        "detected_at": "2026-02-24T10:05:00Z",
                        "expires_at": "2026-04-24T10:05:00Z",
                        "inferred_categories": ["airfare", "travel_packages"],
                        "metadata": {"location": "Boston", "rule_id": "marathon_planning"}
                    }
                ],
                "inferred_categories": ["airfare", "travel_packages", "car_rental"],
                "aggregated_interests": ["fitness", "running", "travel"],
                "last_updated": "2026-02-24T10:05:00Z",
                "query_count": 2,
                "created_at": "2026-02-24T10:00:00Z"
            }
        }
    
    def get_active_intents(self) -> List[InferredIntent]:
        """Get intents that haven't expired."""
        now = datetime.utcnow()
        return [intent for intent in self.inferred_intents if intent.expires_at > now]
    
    def update_inferred_categories(self) -> None:
        """Update inferred_categories from active intents."""
        active_intents = self.get_active_intents()
        categories = set()
        for intent in active_intents:
            categories.update(intent.inferred_categories)
        self.inferred_categories = list(categories)
