"""Pattern rule models and definitions for intent inference."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class PatternStep(BaseModel):
    """Single step in a pattern sequence."""
    
    step: int = Field(..., ge=1, description="Step number in sequence (1-indexed)")
    keywords: List[str] = Field(..., min_length=1, description="Keywords to match in query")
    category_match: Optional[List[str]] = Field(
        None,
        description="Categories that must be present in extracted categories"
    )
    requires_location: bool = Field(
        default=False,
        description="Whether this step requires a location to be mentioned"
    )
    location_must_match_step: Optional[int] = Field(
        None,
        description="If set, location must match the location from this step number"
    )
    min_keyword_matches: int = Field(
        default=1,
        ge=1,
        description="Minimum number of keywords that must match"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "step": 1,
                "keywords": ["marathon", "running", "shoes", "training"],
                "category_match": ["running_shoes", "athletic_footwear"],
                "requires_location": False,
                "min_keyword_matches": 2
            }
        }


class PatternRule(BaseModel):
    """Rule for detecting user intent patterns from query sequences."""
    
    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Human-readable rule name")
    description: str = Field(..., description="What this rule detects")
    pattern: List[PatternStep] = Field(
        ...,
        min_length=2,
        description="Sequence of steps that must match"
    )
    inferred_categories: List[str] = Field(
        ...,
        min_length=1,
        description="Categories to add when pattern matches"
    )
    confidence_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Minimum confidence to trigger this rule"
    )
    time_window_hours: int = Field(
        default=72,
        ge=1,
        description="Maximum time window for pattern to occur (hours)"
    )
    enabled: bool = Field(default=True, description="Whether this rule is active")
    priority: int = Field(
        default=1,
        ge=1,
        description="Rule priority (higher = checked first)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "rule_id": "marathon_planning",
                "name": "Marathon Event Planning",
                "description": "Detects users planning to attend a marathon event",
                "pattern": [
                    {
                        "step": 1,
                        "keywords": ["marathon", "running", "shoes"],
                        "category_match": ["running_shoes"],
                        "requires_location": False,
                        "min_keyword_matches": 2
                    },
                    {
                        "step": 2,
                        "keywords": ["weather", "forecast"],
                        "requires_location": True,
                        "min_keyword_matches": 1
                    }
                ],
                "inferred_categories": ["airfare", "travel_packages"],
                "confidence_threshold": 0.75,
                "time_window_hours": 72,
                "enabled": True,
                "priority": 1
            }
        }


# Predefined pattern rules
MARATHON_PLANNING_RULE = PatternRule(
    rule_id="marathon_planning",
    name="Marathon Event Planning",
    description="Detects users planning to attend a marathon event",
    pattern=[
        PatternStep(
            step=1,
            keywords=["marathon", "running", "shoes", "training", "race"],
            category_match=["running_shoes", "athletic_footwear", "sportswear"],
            requires_location=False,
            min_keyword_matches=2
        ),
        PatternStep(
            step=2,
            keywords=["weather", "forecast", "temperature", "climate"],
            requires_location=True,
            min_keyword_matches=1
        ),
        PatternStep(
            step=3,
            keywords=["hotel", "accommodation", "lodging", "stay", "booking"],
            requires_location=True,
            location_must_match_step=2,
            min_keyword_matches=1
        )
    ],
    inferred_categories=["airfare", "travel_packages", "event_tickets", "car_rental", "travel_insurance"],
    confidence_threshold=0.75,
    time_window_hours=168,  # 1 week
    enabled=True,
    priority=1
)


VACATION_PLANNING_RULE = PatternRule(
    rule_id="vacation_planning",
    name="Vacation Planning",
    description="Detects users planning a vacation or leisure trip",
    pattern=[
        PatternStep(
            step=1,
            keywords=["vacation", "holiday", "trip", "travel", "getaway"],
            requires_location=False,
            min_keyword_matches=1
        ),
        PatternStep(
            step=2,
            keywords=["flight", "airfare", "tickets", "airline"],
            requires_location=True,
            min_keyword_matches=1
        ),
        PatternStep(
            step=3,
            keywords=["hotel", "resort", "accommodation", "stay"],
            requires_location=True,
            location_must_match_step=2,
            min_keyword_matches=1
        )
    ],
    inferred_categories=["car_rental", "travel_insurance", "tours", "activities", "restaurants"],
    confidence_threshold=0.8,
    time_window_hours=336,  # 2 weeks
    enabled=True,
    priority=2
)


SHOPPING_RESEARCH_RULE = PatternRule(
    rule_id="shopping_research",
    name="Product Research & Shopping",
    description="Detects users researching products before purchase",
    pattern=[
        PatternStep(
            step=1,
            keywords=["best", "top", "review", "comparison", "vs"],
            requires_location=False,
            min_keyword_matches=1
        ),
        PatternStep(
            step=2,
            keywords=["price", "cost", "cheap", "deal", "discount", "sale"],
            requires_location=False,
            min_keyword_matches=1
        )
    ],
    inferred_categories=["coupons", "price_comparison", "cashback", "financing"],
    confidence_threshold=0.7,
    time_window_hours=24,  # 1 day
    enabled=True,
    priority=3
)


HOME_IMPROVEMENT_RULE = PatternRule(
    rule_id="home_improvement",
    name="Home Improvement Project",
    description="Detects users planning home improvement or renovation",
    pattern=[
        PatternStep(
            step=1,
            keywords=["kitchen", "bathroom", "renovation", "remodel", "upgrade"],
            requires_location=False,
            min_keyword_matches=1
        ),
        PatternStep(
            step=2,
            keywords=["contractor", "professional", "service", "installation"],
            requires_location=False,
            min_keyword_matches=1
        )
    ],
    inferred_categories=["home_services", "tools", "materials", "financing", "insurance"],
    confidence_threshold=0.75,
    time_window_hours=168,  # 1 week
    enabled=True,
    priority=4
)


FITNESS_JOURNEY_RULE = PatternRule(
    rule_id="fitness_journey",
    name="Fitness Journey Start",
    description="Detects users starting a fitness or weight loss journey",
    pattern=[
        PatternStep(
            step=1,
            keywords=["lose weight", "fitness", "workout", "gym", "exercise"],
            requires_location=False,
            min_keyword_matches=1
        ),
        PatternStep(
            step=2,
            keywords=["diet", "nutrition", "meal plan", "protein", "supplements"],
            requires_location=False,
            min_keyword_matches=1
        )
    ],
    inferred_categories=["fitness_equipment", "gym_membership", "personal_training", "meal_delivery", "fitness_apps"],
    confidence_threshold=0.7,
    time_window_hours=72,  # 3 days
    enabled=True,
    priority=5
)


# Default rule set
DEFAULT_RULES = [
    MARATHON_PLANNING_RULE,
    VACATION_PLANNING_RULE,
    SHOPPING_RESEARCH_RULE,
    HOME_IMPROVEMENT_RULE,
    FITNESS_JOURNEY_RULE
]


class RuleSet(BaseModel):
    """Collection of pattern rules."""
    
    rules: List[PatternRule] = Field(default_factory=list, description="List of pattern rules")
    version: str = Field(default="1.0.0", description="Rule set version")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    def get_enabled_rules(self) -> List[PatternRule]:
        """Get only enabled rules, sorted by priority."""
        enabled = [rule for rule in self.rules if rule.enabled]
        return sorted(enabled, key=lambda r: r.priority)
    
    def get_rule_by_id(self, rule_id: str) -> Optional[PatternRule]:
        """Get a specific rule by ID."""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None
    
    class Config:
        json_schema_extra = {
            "example": {
                "rules": [
                    {
                        "rule_id": "marathon_planning",
                        "name": "Marathon Event Planning",
                        "description": "Detects marathon planning",
                        "pattern": [],
                        "inferred_categories": ["airfare"],
                        "enabled": True
                    }
                ],
                "version": "1.0.0",
                "last_updated": "2026-02-24T10:00:00Z"
            }
        }
