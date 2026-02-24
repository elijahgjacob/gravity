"""Response models for the Ad Retrieval API."""

from pydantic import BaseModel, Field


class Campaign(BaseModel):
    """Campaign information returned in response."""

    campaign_id: str = Field(..., description="Unique campaign identifier")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0.0-1.0)")
    title: str = Field(..., description="Campaign title")
    category: str = Field(..., description="Primary category")
    description: str = Field(..., description="Campaign description")
    keywords: list[str] = Field(..., description="Campaign keywords")

    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": "camp_00123",
                "relevance_score": 0.94,
                "title": "Nike Premium Running Shoes",
                "category": "running_shoes",
                "description": "Lightweight running shoes designed for marathon training...",
                "keywords": ["running", "marathon", "shoes", "athletic", "training"],
            }
        }


class RetrievalResponse(BaseModel):
    """Response from ad retrieval endpoint."""

    ad_eligibility: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Ad eligibility score (0.0 = do not show ads, 1.0 = highly appropriate)",
    )
    extracted_categories: list[str] = Field(
        ..., min_length=1, max_length=10, description="Extracted product/service categories (1-10)"
    )
    campaigns: list[Campaign] = Field(..., description="Retrieved campaigns ordered by relevance")
    latency_ms: float = Field(..., ge=0.0, description="Processing time in milliseconds")
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata (debugging, intermediate scores, etc.)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "ad_eligibility": 0.95,
                "extracted_categories": ["running_shoes", "marathon_gear", "athletic_footwear"],
                "campaigns": [
                    {
                        "campaign_id": "camp_00123",
                        "relevance_score": 0.94,
                        "title": "Nike Premium Running Shoes",
                        "category": "running_shoes",
                        "description": "Lightweight running shoes...",
                        "keywords": ["running", "marathon", "shoes"],
                    }
                ],
                "latency_ms": 67.5,
                "metadata": {"candidates_retrieved": 1500, "campaigns_returned": 1000},
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")

    class Config:
        json_schema_extra = {"example": {"status": "healthy", "version": "1.0.0"}}
