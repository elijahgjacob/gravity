"""Request models for the Ad Retrieval API."""

from typing import Literal

from pydantic import BaseModel, Field


class UserContext(BaseModel):
    """User context information for ad targeting."""

    gender: Literal["male", "female", "non-binary", "other", "prefer_not_to_say"] | None = Field(
        None,
        description="User gender (must be one of: male, female, non-binary, other, prefer_not_to_say)",
    )
    age: int | None = Field(None, ge=0, le=120, description="User age")
    location: str | None = Field(None, description="User location (e.g., 'San Francisco, CA')")
    interests: list[str] | None = Field(None, description="User interests")

    class Config:
        json_schema_extra = {
            "example": {
                "gender": "male",
                "age": 24,
                "location": "San Francisco, CA",
                "interests": ["fitness", "outdoor activities"],
            }
        }


class RetrievalRequest(BaseModel):
    """Request for ad retrieval."""

    query: str = Field(
        ..., min_length=1, max_length=500, description="User's natural language query"
    )
    context: UserContext | None = Field(None, description="Optional user context for targeting")
    user_id: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Optional user identifier for profile tracking and personalization"
    )
    session_id: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Optional session identifier for tracking query sequences"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "I'm running a marathon next month and need new shoes. What should I get?",
                "context": {
                    "gender": "male",
                    "age": 24,
                    "location": "San Francisco, CA",
                    "interests": ["fitness", "outdoor activities"],
                },
                "user_id": "user_12345",
                "session_id": "sess_abc123"
            }
        }
