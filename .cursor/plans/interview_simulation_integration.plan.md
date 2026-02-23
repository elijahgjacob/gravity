---
name: ""
overview: ""
todos: []
isProject: false
---

# Interview Simulation Integration - Implementation Plan

**Plan ID:** `interview_simulation_integration`  
**Created:** 2026-02-22  
**Status:** Ready for Implementation  
**Estimated Effort:** 3-5 days  

---

## Executive Summary

This plan outlines the integration of the **interview** ad campaign simulation system into the **gravity** ad retrieval API. The integration will enable performance prediction, testing, and validation of gravity's retrieval decisions through realistic auction simulations.

### Key Objectives

1. **Campaign Performance Prediction**: Simulate how retrieved campaigns perform in real auctions
2. **Retrieval Validation**: Test if high relevance scores translate to good auction outcomes
3. **End-to-End Testing**: Create comprehensive testing framework using simulation data
4. **Performance Analytics**: Provide insights into budget utilization, fill rates, and ROI

### Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Gravity System                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   Retrieval  │───▶│   Ranking    │───▶│  Simulation  │     │
│  │   Pipeline   │    │   Service    │    │   Service    │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│         │                    │                    │             │
│         │                    │                    ▼             │
│         │                    │           ┌──────────────┐      │
│         │                    │           │  Interview   │      │
│         │                    │           │  Simulation  │      │
│         │                    │           │   Engine     │      │
│         │                    │           └──────────────┘      │
│         ▼                    ▼                    │             │
│  ┌──────────────────────────────────────────────┐│             │
│  │         New API Endpoints                    ││             │
│  │  • POST /api/simulate-performance            ││             │
│  │  • POST /api/retrieve-and-simulate           ││             │
│  │  • GET  /api/simulation/metrics              ││             │
│  └──────────────────────────────────────────────┘│             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Project Setup & Dependencies

**Duration:** 0.5 days  
**Priority:** Critical  

### 1.1 Copy Interview Code to Gravity

**Objective:** Import the interview simulation code as a submodule within gravity.

**Tasks:**

1. Create new directory structure:
  ```
   gravity/
   ├── src/
   │   ├── simulation/              # NEW
   │   │   ├── __init__.py
   │   │   ├── models.py            # From interview repo
   │   │   ├── simulation.py        # From interview repo
   │   │   ├── generator.py         # From interview repo
   │   │   └── adapters/            # NEW: Bridge code
   │   │       ├── __init__.py
   │   │       ├── campaign_adapter.py
   │   │       └── publisher_adapter.py
  ```
2. Copy files from interview repo:
  - `models.py` → `src/simulation/models.py`
  - `simulation.py` → `src/simulation/simulation.py`
  - `generator.py` → `src/simulation/generator.py`
3. Update imports in copied files to use relative imports
4. Add any missing dependencies to `requirements.txt`:
  ```txt
   # Existing dependencies...

   # Simulation dependencies (if any new ones needed)
   # (interview repo uses only stdlib, so likely none)
  ```

**Acceptance Criteria:**

- All interview simulation code copied to `src/simulation/`
- Imports updated and working
- No new external dependencies required (interview uses stdlib only)
- Can import and instantiate `Campaign`, `Publisher`, `AdSimulation` classes

**Files to Create:**

- `src/simulation/__init__.py`
- `src/simulation/models.py`
- `src/simulation/simulation.py`
- `src/simulation/generator.py`
- `src/simulation/adapters/__init__.py`

---

## Phase 2: Adapter Layer

**Duration:** 1 day  
**Priority:** Critical  

### 2.1 Campaign Adapter

**Objective:** Convert gravity's campaign format to interview's campaign format.

**File:** `src/simulation/adapters/campaign_adapter.py`

```python
"""
Adapter to convert Gravity campaigns to Interview simulation campaigns.
"""

from typing import List, Dict
from src.simulation.models import Campaign as SimCampaign


class CampaignAdapter:
    """Converts Gravity campaign data to Interview simulation format."""
    
    @staticmethod
    def gravity_to_simulation(
        gravity_campaigns: List[Dict],
        default_daily_budget: float = 1000.0,
        default_max_bid_cpm: float = 10.0
    ) -> List[SimCampaign]:
        """
        Convert Gravity campaigns to Interview simulation campaigns.
        
        Args:
            gravity_campaigns: List of campaigns from Gravity retrieval
            default_daily_budget: Default budget if not specified
            default_max_bid_cpm: Default max bid if not specified
        
        Returns:
            List of SimCampaign objects ready for simulation
        """
        sim_campaigns = []
        
        for idx, campaign in enumerate(gravity_campaigns):
            # Extract or generate campaign parameters
            campaign_id = idx + 1
            name = campaign.get('title', f'Campaign {campaign_id}')
            
            # Use relevance score to influence budget/bid
            relevance = campaign.get('relevance_score', 0.5)
            
            # Higher relevance = higher budget/bid (simulate advertiser confidence)
            daily_budget = default_daily_budget * (0.5 + relevance)
            max_bid_cpm = default_max_bid_cpm * (0.5 + relevance)
            
            # Extract target categories
            target_categories = [campaign.get('category', 'general')]
            
            sim_campaign = SimCampaign(
                id=campaign_id,
                name=name,
                daily_budget=daily_budget,
                max_bid_cpm=max_bid_cpm,
                target_categories=target_categories
            )
            
            sim_campaigns.append(sim_campaign)
        
        return sim_campaigns
    
    @staticmethod
    def add_budget_metadata(
        gravity_campaign: Dict,
        sim_campaign: SimCampaign
    ) -> Dict:
        """
        Add simulation results back to Gravity campaign object.
        
        Args:
            gravity_campaign: Original Gravity campaign dict
            sim_campaign: Simulation campaign with results
        
        Returns:
            Enhanced campaign dict with simulation metrics
        """
        return {
            **gravity_campaign,
            'simulation_metrics': {
                'daily_budget': sim_campaign.daily_budget,
                'total_spent': sim_campaign.spent_today,
                'total_impressions': sim_campaign.impressions_today,
                'effective_cpm': sim_campaign.effective_cpm(),
                'budget_utilization': (
                    sim_campaign.spent_today / sim_campaign.daily_budget * 100
                    if sim_campaign.daily_budget > 0 else 0
                )
            }
        }
```

**Tasks:**

1. Implement `CampaignAdapter` class
2. Add method to convert Gravity → Simulation format
3. Add method to merge simulation results back to Gravity campaigns
4. Handle edge cases (missing fields, invalid data)
5. Write unit tests

**Acceptance Criteria:**

- Can convert list of Gravity campaigns to SimCampaign objects
- Relevance scores influence budget/bid allocation
- Can merge simulation results back to original campaigns
- Unit tests cover all conversion paths

---

### 2.2 Publisher Adapter

**Objective:** Generate realistic publishers based on extracted categories.

**File:** `src/simulation/adapters/publisher_adapter.py`

```python
"""
Adapter to generate publishers for simulation based on query categories.
"""

from typing import List
from src.simulation.models import Publisher


class PublisherAdapter:
    """Generates publishers for simulation based on query context."""
    
    # Default publisher profiles for different categories
    PUBLISHER_PROFILES = {
        'high_traffic': {
            'daily_requests_range': (100000, 500000),
            'count': 2
        },
        'medium_traffic': {
            'daily_requests_range': (50000, 100000),
            'count': 2
        },
        'low_traffic': {
            'daily_requests_range': (10000, 50000),
            'count': 1
        }
    }
    
    @staticmethod
    def generate_publishers(
        categories: List[str],
        total_publishers: int = 5,
        traffic_distribution: str = 'balanced'
    ) -> List[Publisher]:
        """
        Generate publishers for simulation based on extracted categories.
        
        Args:
            categories: List of extracted categories from query
            total_publishers: Number of publishers to generate
            traffic_distribution: 'balanced', 'high_traffic', or 'low_traffic'
        
        Returns:
            List of Publisher objects for simulation
        """
        import random
        
        publishers = []
        
        # Distribute publishers across categories
        for idx in range(total_publishers):
            publisher_id = idx + 1
            category = categories[idx % len(categories)]
            
            # Determine traffic based on distribution strategy
            if traffic_distribution == 'high_traffic':
                daily_requests = random.randint(100000, 500000)
            elif traffic_distribution == 'low_traffic':
                daily_requests = random.randint(10000, 50000)
            else:  # balanced
                if idx < 2:
                    daily_requests = random.randint(100000, 500000)
                elif idx < 4:
                    daily_requests = random.randint(50000, 100000)
                else:
                    daily_requests = random.randint(10000, 50000)
            
            publisher = Publisher(
                id=publisher_id,
                name=f"Publisher {publisher_id} ({category})",
                category=category,
                daily_requests=daily_requests
            )
            
            publishers.append(publisher)
        
        return publishers
    
    @staticmethod
    def generate_from_query_context(
        categories: List[str],
        query_context: dict = None
    ) -> List[Publisher]:
        """
        Generate publishers with traffic based on query context.
        
        If context suggests high commercial intent, generate high-traffic publishers.
        """
        # Analyze context to determine traffic level
        traffic_level = 'balanced'
        
        if query_context:
            # High commercial intent = high traffic publishers
            interests = query_context.get('interests', [])
            if any(keyword in str(interests).lower() 
                   for keyword in ['shopping', 'buying', 'purchase']):
                traffic_level = 'high_traffic'
        
        return PublisherAdapter.generate_publishers(
            categories=categories,
            total_publishers=5,
            traffic_distribution=traffic_level
        )
```

**Tasks:**

1. Implement `PublisherAdapter` class
2. Add publisher generation logic based on categories
3. Support different traffic distribution strategies
4. Add context-aware publisher generation
5. Write unit tests

**Acceptance Criteria:**

- Can generate publishers from category list
- Traffic distribution is realistic and configurable
- Context-aware generation works correctly
- Unit tests cover all generation strategies

---

## Phase 3: Simulation Service

**Duration:** 1 day  
**Priority:** Critical  

### 3.1 Simulation Service Implementation

**Objective:** Create service layer that orchestrates simulation execution.

**File:** `src/services/simulation_service.py`

```python
"""
SERVICE: Campaign performance simulation using interview auction engine.
"""

from typing import List, Dict, Optional
from src.simulation.simulation import AdSimulation
from src.simulation.adapters.campaign_adapter import CampaignAdapter
from src.simulation.adapters.publisher_adapter import PublisherAdapter
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class SimulationService:
    """
    SERVICE: Simulates campaign performance using auction mechanics.
    
    Uses the interview simulation engine to predict how retrieved campaigns
    would perform in a real programmatic advertising marketplace.
    """
    
    def __init__(self):
        """Initialize simulation service."""
        self.campaign_adapter = CampaignAdapter()
        self.publisher_adapter = PublisherAdapter()
    
    async def simulate_campaign_performance(
        self,
        campaigns: List[Dict],
        categories: List[str],
        query_context: Optional[Dict] = None,
        simulation_hours: int = 24
    ) -> Dict:
        """
        Simulate campaign performance over specified time period.
        
        Args:
            campaigns: List of campaigns from Gravity retrieval
            categories: Extracted categories from query
            query_context: Optional context about the query
            simulation_hours: Number of hours to simulate (default: 24)
        
        Returns:
            Simulation results with performance metrics
        """
        logger.info(f"Starting simulation for {len(campaigns)} campaigns")
        
        # Convert campaigns to simulation format
        sim_campaigns = self.campaign_adapter.gravity_to_simulation(campaigns)
        
        # Generate publishers based on categories
        publishers = self.publisher_adapter.generate_from_query_context(
            categories=categories,
            query_context=query_context
        )
        
        logger.debug(f"Generated {len(publishers)} publishers for simulation")
        
        # Run simulation
        simulation = AdSimulation(sim_campaigns, publishers)
        
        # Simulate specified hours (default: full 24-hour day)
        for hour in range(simulation_hours):
            simulation.simulate_hour(hour)
        
        # Gather results
        campaign_summaries = simulation.get_campaign_summary()
        publisher_summaries = simulation.get_publisher_summary()
        
        # Calculate aggregate metrics
        total_budget = sum(cs["daily_budget"] for cs in campaign_summaries)
        total_spent = sum(cs["total_spent"] for cs in campaign_summaries)
        total_impressions = sum(cs["total_impressions"] for cs in campaign_summaries)
        total_requests = sum(ps["daily_requests"] for ps in publisher_summaries)
        
        logger.info(
            f"Simulation complete: ${total_spent:.2f} spent, "
            f"{total_impressions:,} impressions"
        )
        
        return {
            "simulation_summary": {
                "total_budget": round(total_budget, 2),
                "total_spent": round(total_spent, 2),
                "total_impressions": total_impressions,
                "total_requests": total_requests,
                "budget_utilization_pct": round(
                    (total_spent / total_budget * 100) if total_budget > 0 else 0,
                    2
                ),
                "fill_rate_pct": round(
                    (total_impressions / total_requests * 100) if total_requests > 0 else 0,
                    2
                ),
                "average_cpm": round(
                    (total_spent / total_impressions * 1000) if total_impressions > 0 else 0,
                    2
                ),
                "simulation_hours": simulation_hours
            },
            "campaign_performance": campaign_summaries,
            "publisher_performance": publisher_summaries,
            "hourly_results": simulation.hourly_results
        }
    
    async def predict_campaign_roi(
        self,
        campaigns: List[Dict],
        categories: List[str],
        query_context: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Predict ROI for each campaign based on simulation.
        
        Returns campaigns ranked by predicted performance.
        """
        # Run simulation
        results = await self.simulate_campaign_performance(
            campaigns=campaigns,
            categories=categories,
            query_context=query_context
        )
        
        # Enhance campaigns with simulation metrics
        enhanced_campaigns = []
        for campaign, perf in zip(campaigns, results["campaign_performance"]):
            enhanced = self.campaign_adapter.add_budget_metadata(campaign, perf)
            enhanced_campaigns.append(enhanced)
        
        # Sort by budget utilization (best performing first)
        enhanced_campaigns.sort(
            key=lambda c: c['simulation_metrics']['budget_utilization'],
            reverse=True
        )
        
        return enhanced_campaigns
```

**Tasks:**

1. Implement `SimulationService` class
2. Add simulation orchestration logic
3. Integrate with adapters
4. Add aggregate metrics calculation
5. Add ROI prediction method
6. Write unit tests

**Acceptance Criteria:**

- Can run full simulation with Gravity campaigns
- Returns comprehensive performance metrics
- ROI prediction works correctly
- Handles edge cases (no campaigns, invalid data)
- Unit tests cover all methods

---

## Phase 4: API Models & Endpoints

**Duration:** 1 day  
**Priority:** High  

### 4.1 Request/Response Models

**File:** `src/api/models/simulation_models.py`

```python
"""Request and response models for simulation endpoints."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    """Request to simulate campaign performance."""
    
    query: str = Field(..., description="Search query")
    context: Optional[Dict] = Field(
        None,
        description="Optional context (age, location, interests, etc.)"
    )
    simulation_hours: int = Field(
        24,
        ge=1,
        le=168,
        description="Hours to simulate (1-168, default: 24)"
    )
    num_campaigns: int = Field(
        10,
        ge=1,
        le=100,
        description="Number of top campaigns to simulate (1-100)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "running shoes for marathon",
                "context": {
                    "age": 30,
                    "location": "San Francisco",
                    "interests": ["fitness", "running"]
                },
                "simulation_hours": 24,
                "num_campaigns": 10
            }
        }


class CampaignPerformance(BaseModel):
    """Performance metrics for a single campaign."""
    
    campaign_id: str
    name: str
    daily_budget: float
    total_spent: float
    total_impressions: int
    effective_cpm: float
    budget_utilization_pct: float


class SimulationResponse(BaseModel):
    """Response from simulation endpoint."""
    
    query: str
    ad_eligibility: float
    extracted_categories: List[str]
    
    simulation_summary: Dict = Field(
        ...,
        description="Aggregate simulation metrics"
    )
    campaign_performance: List[CampaignPerformance]
    publisher_performance: List[Dict]
    
    retrieval_latency_ms: float
    simulation_latency_ms: float
    total_latency_ms: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "running shoes",
                "ad_eligibility": 0.95,
                "extracted_categories": ["running_shoes", "athletic_footwear"],
                "simulation_summary": {
                    "total_budget": 15000.0,
                    "total_spent": 4590.25,
                    "total_impressions": 459025,
                    "budget_utilization_pct": 30.6,
                    "fill_rate_pct": 100.0,
                    "average_cpm": 10.0
                },
                "campaign_performance": [],
                "publisher_performance": [],
                "retrieval_latency_ms": 24.5,
                "simulation_latency_ms": 15.3,
                "total_latency_ms": 39.8
            }
        }
```

**Tasks:**

1. Create `SimulationRequest` model
2. Create `SimulationResponse` model
3. Create `CampaignPerformance` model
4. Add validation rules
5. Add example schemas

**Acceptance Criteria:**

- All models defined with proper validation
- Examples provided for API docs
- Validation catches invalid inputs

---

### 4.2 Simulation Controller

**File:** `src/controllers/simulation_controller.py`

```python
"""
CONTROLLER: Orchestrates retrieval + simulation pipeline.
"""

import time
from typing import Optional
from src.api.models.requests import RetrievalRequest
from src.api.models.simulation_models import SimulationRequest, SimulationResponse
from src.controllers.retrieval_controller import RetrievalController
from src.services.simulation_service import SimulationService
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class SimulationController:
    """
    CONTROLLER: Orchestrates retrieval and simulation pipeline.
    """
    
    def __init__(
        self,
        retrieval_controller: RetrievalController,
        simulation_service: SimulationService
    ):
        self.retrieval_controller = retrieval_controller
        self.simulation_service = simulation_service
    
    async def retrieve_and_simulate(
        self,
        request: SimulationRequest
    ) -> SimulationResponse:
        """
        Execute retrieval + simulation pipeline.
        
        Pipeline:
        1. Retrieve campaigns using standard retrieval pipeline
        2. Take top N campaigns
        3. Run simulation
        4. Return combined results
        """
        total_start = time.perf_counter()
        
        # Phase 1: Retrieval
        retrieval_start = time.perf_counter()
        
        retrieval_request = RetrievalRequest(
            query=request.query,
            context=request.context
        )
        
        retrieval_response = await self.retrieval_controller.retrieve(
            retrieval_request
        )
        
        retrieval_latency = (time.perf_counter() - retrieval_start) * 1000
        
        # Take top N campaigns for simulation
        top_campaigns = [
            c.model_dump() 
            for c in retrieval_response.campaigns[:request.num_campaigns]
        ]
        
        logger.info(
            f"Retrieved {len(top_campaigns)} campaigns for simulation "
            f"in {retrieval_latency:.2f}ms"
        )
        
        # Phase 2: Simulation
        simulation_start = time.perf_counter()
        
        simulation_results = await self.simulation_service.simulate_campaign_performance(
            campaigns=top_campaigns,
            categories=retrieval_response.extracted_categories,
            query_context=request.context,
            simulation_hours=request.simulation_hours
        )
        
        simulation_latency = (time.perf_counter() - simulation_start) * 1000
        total_latency = (time.perf_counter() - total_start) * 1000
        
        logger.info(
            f"Simulation complete in {simulation_latency:.2f}ms "
            f"(total: {total_latency:.2f}ms)"
        )
        
        # Build response
        return SimulationResponse(
            query=request.query,
            ad_eligibility=retrieval_response.ad_eligibility,
            extracted_categories=retrieval_response.extracted_categories,
            simulation_summary=simulation_results["simulation_summary"],
            campaign_performance=simulation_results["campaign_performance"],
            publisher_performance=simulation_results["publisher_performance"],
            retrieval_latency_ms=retrieval_latency,
            simulation_latency_ms=simulation_latency,
            total_latency_ms=total_latency
        )
```

**Tasks:**

1. Implement `SimulationController`
2. Add retrieval + simulation orchestration
3. Add timing/latency tracking
4. Add error handling
5. Write unit tests

**Acceptance Criteria:**

- Controller orchestrates both retrieval and simulation
- Latency tracking works correctly
- Error handling is robust
- Unit tests cover all paths

---

### 4.3 API Routes

**File:** `src/api/routes/simulation.py`

```python
"""API routes for campaign simulation."""

from fastapi import APIRouter, Depends
from src.api.models.simulation_models import SimulationRequest, SimulationResponse
from src.controllers.simulation_controller import SimulationController
from src.core.dependencies import get_simulation_controller

router = APIRouter(prefix="/api", tags=["simulation"])


@router.post(
    "/simulate-performance",
    response_model=SimulationResponse,
    summary="Retrieve campaigns and simulate performance",
    description="""
    Execute the complete retrieval + simulation pipeline:
    1. Retrieve relevant campaigns for the query
    2. Simulate their performance in a programmatic auction
    3. Return performance predictions and metrics
    
    This endpoint is useful for:
    - Predicting campaign ROI before deployment
    - Testing retrieval algorithm effectiveness
    - Understanding auction dynamics
    """,
)
async def simulate_performance(
    request: SimulationRequest,
    controller: SimulationController = Depends(get_simulation_controller)
) -> SimulationResponse:
    """Retrieve campaigns and simulate their auction performance."""
    return await controller.retrieve_and_simulate(request)


@router.post(
    "/retrieve-and-simulate",
    response_model=SimulationResponse,
    summary="Alias for /simulate-performance",
    description="Same as /simulate-performance (provided for clarity)",
)
async def retrieve_and_simulate(
    request: SimulationRequest,
    controller: SimulationController = Depends(get_simulation_controller)
) -> SimulationResponse:
    """Alias endpoint for clarity."""
    return await controller.retrieve_and_simulate(request)
```

**Tasks:**

1. Create simulation router
2. Add `/api/simulate-performance` endpoint
3. Add `/api/retrieve-and-simulate` alias
4. Add comprehensive API documentation
5. Register router in main app

**Acceptance Criteria:**

- Endpoints defined and working
- API documentation is clear and helpful
- Endpoints registered in FastAPI app
- Can test via Swagger UI

---

### 4.4 Update Dependencies

**File:** `src/core/dependencies.py`

Add dependency injection for simulation controller:

```python
# Add to existing dependencies.py

from src.controllers.simulation_controller import SimulationController
from src.services.simulation_service import SimulationService

# Singleton instances
_simulation_service: Optional[SimulationService] = None
_simulation_controller: Optional[SimulationController] = None


def get_simulation_service() -> SimulationService:
    """Get or create simulation service instance."""
    global _simulation_service
    if _simulation_service is None:
        _simulation_service = SimulationService()
    return _simulation_service


def get_simulation_controller() -> SimulationController:
    """Get or create simulation controller instance."""
    global _simulation_controller
    if _simulation_controller is None:
        retrieval_controller = get_retrieval_controller()
        simulation_service = get_simulation_service()
        _simulation_controller = SimulationController(
            retrieval_controller=retrieval_controller,
            simulation_service=simulation_service
        )
    return _simulation_controller
```

**Tasks:**

1. Add simulation service dependency
2. Add simulation controller dependency
3. Update existing dependencies if needed

**Acceptance Criteria:**

- Dependency injection works correctly
- Singletons are properly managed
- No circular dependencies

---

### 4.5 Register Routes

**File:** `src/api/main.py`

Update main app to include simulation routes:

```python
# Add to existing main.py

from src.api.routes import simulation

# Register simulation routes
app.include_router(simulation.router)
```

**Tasks:**

1. Import simulation router
2. Register with FastAPI app
3. Verify routes appear in OpenAPI docs

**Acceptance Criteria:**

- Routes registered successfully
- Appear in `/docs` and `/redoc`
- Can be called via HTTP

---

## Phase 5: Testing

**Duration:** 1 day  
**Priority:** High  

### 5.1 Unit Tests

**Files to Create:**

- `tests/unit/test_campaign_adapter.py`
- `tests/unit/test_publisher_adapter.py`
- `tests/unit/test_simulation_service.py`

**Test Coverage:**

1. **Campaign Adapter Tests**
  - Conversion from Gravity to Simulation format
  - Relevance score influences budget/bid
  - Metadata merging works correctly
  - Edge cases (empty campaigns, missing fields)
2. **Publisher Adapter Tests**
  - Publisher generation from categories
  - Traffic distribution strategies
  - Context-aware generation
  - Edge cases (no categories, invalid context)
3. **Simulation Service Tests**
  - Full simulation execution
  - ROI prediction
  - Aggregate metrics calculation
  - Edge cases (no campaigns, no publishers)

**Tasks:**

1. Write unit tests for each adapter
2. Write unit tests for simulation service
3. Achieve >80% code coverage
4. Add edge case tests

**Acceptance Criteria:**

- All unit tests passing
- Code coverage >80%
- Edge cases covered
- Tests run in <10 seconds

---

### 5.2 Integration Tests

**File:** `tests/integration/test_simulation_integration.py`

```python
"""Integration tests for simulation pipeline."""

import pytest
from src.api.models.simulation_models import SimulationRequest
from src.core.dependencies import get_simulation_controller


@pytest.mark.asyncio
async def test_full_simulation_pipeline():
    """Test complete retrieval + simulation pipeline."""
    controller = get_simulation_controller()
    
    request = SimulationRequest(
        query="running shoes for marathon training",
        context={
            "age": 30,
            "location": "San Francisco",
            "interests": ["fitness", "running"]
        },
        simulation_hours=24,
        num_campaigns=10
    )
    
    response = await controller.retrieve_and_simulate(request)
    
    # Assertions
    assert response.ad_eligibility > 0.0
    assert len(response.extracted_categories) > 0
    assert response.simulation_summary["total_budget"] > 0
    assert response.simulation_summary["total_spent"] >= 0
    assert response.simulation_summary["budget_utilization_pct"] >= 0
    assert response.retrieval_latency_ms > 0
    assert response.simulation_latency_ms > 0
    assert len(response.campaign_performance) > 0


@pytest.mark.asyncio
async def test_simulation_with_blocked_query():
    """Test simulation with blocked query (should short-circuit)."""
    controller = get_simulation_controller()
    
    request = SimulationRequest(
        query="how to harm myself",
        simulation_hours=24,
        num_campaigns=10
    )
    
    response = await controller.retrieve_and_simulate(request)
    
    # Should have zero eligibility and no campaigns
    assert response.ad_eligibility == 0.0
    assert len(response.campaign_performance) == 0


@pytest.mark.asyncio
async def test_simulation_performance_metrics():
    """Test that simulation returns valid performance metrics."""
    controller = get_simulation_controller()
    
    request = SimulationRequest(
        query="buy laptop computer",
        simulation_hours=24,
        num_campaigns=5
    )
    
    response = await controller.retrieve_and_simulate(request)
    
    # Check simulation summary
    summary = response.simulation_summary
    assert summary["total_budget"] > 0
    assert 0 <= summary["budget_utilization_pct"] <= 100
    assert 0 <= summary["fill_rate_pct"] <= 100
    assert summary["average_cpm"] >= 0
    
    # Check campaign performance
    for campaign in response.campaign_performance:
        assert campaign["daily_budget"] > 0
        assert campaign["total_spent"] >= 0
        assert campaign["total_impressions"] >= 0
        assert 0 <= campaign["budget_utilization_pct"] <= 100
```

**Tasks:**

1. Write integration tests for full pipeline
2. Test with various query types
3. Test edge cases and error conditions
4. Test performance (latency targets)

**Acceptance Criteria:**

- All integration tests passing
- Tests cover happy path and edge cases
- Performance tests validate latency
- Tests run in <30 seconds

---

### 5.3 API Tests

**File:** `tests/api/test_simulation_endpoints.py`

```python
"""API endpoint tests for simulation routes."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_simulate_performance_endpoint():
    """Test /api/simulate-performance endpoint."""
    response = client.post(
        "/api/simulate-performance",
        json={
            "query": "running shoes",
            "simulation_hours": 24,
            "num_campaigns": 10
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "query" in data
    assert "ad_eligibility" in data
    assert "simulation_summary" in data
    assert "campaign_performance" in data
    assert "retrieval_latency_ms" in data
    assert "simulation_latency_ms" in data


def test_simulate_performance_with_context():
    """Test simulation with user context."""
    response = client.post(
        "/api/simulate-performance",
        json={
            "query": "best laptop for programming",
            "context": {
                "age": 25,
                "location": "New York",
                "interests": ["technology", "coding"]
            },
            "simulation_hours": 24,
            "num_campaigns": 5
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ad_eligibility"] > 0


def test_simulate_performance_validation():
    """Test request validation."""
    # Invalid simulation_hours (too high)
    response = client.post(
        "/api/simulate-performance",
        json={
            "query": "test",
            "simulation_hours": 200  # Max is 168
        }
    )
    assert response.status_code == 422
    
    # Invalid num_campaigns (too high)
    response = client.post(
        "/api/simulate-performance",
        json={
            "query": "test",
            "num_campaigns": 150  # Max is 100
        }
    )
    assert response.status_code == 422
```

**Tasks:**

1. Write API endpoint tests
2. Test request validation
3. Test response format
4. Test error handling

**Acceptance Criteria:**

- All API tests passing
- Validation tests work correctly
- Error responses are proper HTTP codes
- Tests run in <20 seconds

---

## Phase 6: Documentation

**Duration:** 0.5 days  
**Priority:** Medium  

### 6.1 Update README

**File:** `README.md`

Add new section:

```markdown
## Simulation Integration

Gravity now includes campaign performance simulation powered by programmatic auction mechanics.

### Simulation Endpoint

```bash
curl -X POST http://localhost:8000/api/simulate-performance \
  -H "Content-Type: application/json" \
  -d '{
    "query": "running shoes for marathon",
    "simulation_hours": 24,
    "num_campaigns": 10
  }'
```

### What It Does

1. Retrieves relevant campaigns for your query
2. Simulates a 24-hour programmatic auction
3. Returns predicted performance metrics:
  - Budget utilization
  - Impressions delivered
  - Fill rates
  - Effective CPM
  - ROI predictions

### Use Cases

- **Pre-deployment Testing**: Validate campaign performance before going live
- **Algorithm Validation**: Test if high relevance scores lead to good outcomes
- **Budget Planning**: Predict spend and impressions for budget allocation
- **A/B Testing**: Compare different retrieval strategies

```

**Tasks:**
1. Add simulation section to README
2. Add usage examples
3. Add API documentation links
4. Update architecture diagram

**Acceptance Criteria:**
- [ ] README updated with simulation info
- [ ] Examples are clear and working
- [ ] Links to API docs added

---

### 6.2 Create Simulation Guide

**File:** `docs/SIMULATION_GUIDE.md`

Create comprehensive guide covering:
- How simulation works
- Auction mechanics
- Interpreting results
- Best practices
- Troubleshooting

**Tasks:**
1. Create simulation guide document
2. Add architecture diagrams
3. Add example workflows
4. Add FAQ section

**Acceptance Criteria:**
- [ ] Guide is comprehensive and clear
- [ ] Includes diagrams and examples
- [ ] Covers common questions

---

### 6.3 Update API Documentation

**Tasks:**
1. Ensure OpenAPI schemas are complete
2. Add detailed endpoint descriptions
3. Add request/response examples
4. Test Swagger UI documentation

**Acceptance Criteria:**
- [ ] API docs are complete and accurate
- [ ] Examples work when tested
- [ ] Swagger UI renders correctly

---

## Phase 7: Performance Optimization

**Duration:** 0.5 days  
**Priority:** Low  

### 7.1 Optimize Simulation Speed

**Objectives:**
- Keep simulation latency under 50ms for 10 campaigns
- Optimize adapter conversions
- Cache publisher generation if possible

**Tasks:**
1. Profile simulation execution
2. Identify bottlenecks
3. Optimize hot paths
4. Add caching where appropriate
5. Benchmark improvements

**Acceptance Criteria:**
- [ ] Simulation latency <50ms for 10 campaigns
- [ ] No performance regression in retrieval
- [ ] Benchmarks show improvements

---

### 7.2 Add Caching

**Objectives:**
- Cache publisher generation for common categories
- Cache simulation results for identical queries (optional)

**Tasks:**
1. Add publisher cache
2. Add TTL and invalidation logic
3. Add cache metrics
4. Test cache effectiveness

**Acceptance Criteria:**
- [ ] Caching reduces latency by >20%
- [ ] Cache invalidation works correctly
- [ ] Memory usage is acceptable

---

## Phase 8: Deployment

**Duration:** 0.5 days  
**Priority:** Medium  

### 8.1 Update Deployment Configuration

**Tasks:**
1. Update Docker configuration if needed
2. Update environment variables
3. Update deployment scripts
4. Test deployment locally

**Acceptance Criteria:**
- [ ] Deployment configuration updated
- [ ] Local deployment works
- [ ] No breaking changes to existing endpoints

---

### 8.2 Production Checklist

**Pre-deployment Verification:**
- [ ] All tests passing (unit, integration, API)
- [ ] Performance benchmarks meet targets
- [ ] Documentation complete
- [ ] API docs updated
- [ ] No breaking changes to existing endpoints
- [ ] Error handling is robust
- [ ] Logging is comprehensive
- [ ] Monitoring metrics added

---

## Success Metrics

### Functional Metrics
- [ ] Can simulate 10 campaigns in <50ms
- [ ] Simulation results are realistic and consistent
- [ ] All endpoints return valid responses
- [ ] 100% test coverage for new code

### Performance Metrics
- [ ] Retrieval latency unchanged (<100ms)
- [ ] Simulation latency <50ms
- [ ] Total pipeline latency <150ms
- [ ] No memory leaks

### Quality Metrics
- [ ] Code review completed
- [ ] Documentation complete
- [ ] All tests passing
- [ ] No linter errors

---

## Risk Assessment

### High Risk
1. **Performance Impact**: Simulation could slow down retrieval
   - **Mitigation**: Keep simulation separate, optimize aggressively
   
2. **Data Format Mismatch**: Gravity and Interview formats differ
   - **Mitigation**: Robust adapter layer with validation

### Medium Risk
1. **Unrealistic Simulations**: Generated publishers may not match reality
   - **Mitigation**: Tune publisher generation based on real data
   
2. **Memory Usage**: Simulation stores hourly results
   - **Mitigation**: Limit simulation hours, add cleanup

### Low Risk
1. **API Breaking Changes**: New endpoints shouldn't affect existing ones
   - **Mitigation**: Separate routes, comprehensive testing

---

## Future Enhancements

### Phase 9: Advanced Features (Post-MVP)
1. **Multi-run Simulations**: Run N simulations and average results
2. **Custom Publisher Profiles**: Let users define publisher mix
3. **Historical Data Integration**: Use real auction data for validation
4. **Real-time Simulation**: Stream results as simulation progresses
5. **Visualization Dashboard**: Web UI for simulation results
6. **A/B Testing Framework**: Compare retrieval strategies
7. **Budget Optimization**: Suggest optimal budget allocation

---

## Timeline Summary

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| 1. Project Setup | 0.5 days | None |
| 2. Adapter Layer | 1 day | Phase 1 |
| 3. Simulation Service | 1 day | Phase 2 |
| 4. API Layer | 1 day | Phase 3 |
| 5. Testing | 1 day | Phase 4 |
| 6. Documentation | 0.5 days | Phase 5 |
| 7. Optimization | 0.5 days | Phase 5 |
| 8. Deployment | 0.5 days | Phase 6 |
| **Total** | **5-6 days** | |

---

## Getting Started

To begin implementation:

1. **Review this plan** with the team
2. **Start with Phase 1**: Copy interview code and set up structure
3. **Follow phases sequentially**: Each phase builds on the previous
4. **Test continuously**: Run tests after each phase
5. **Update this plan**: Mark tasks complete as you go

---

## Questions & Decisions Needed

1. **Budget/Bid Defaults**: What default values should we use for campaigns without budget data?
2. **Publisher Traffic**: Should we use real traffic data or synthetic?
3. **Simulation Hours**: Should we support simulations >24 hours?
4. **Caching Strategy**: Should we cache simulation results?
5. **Monitoring**: What metrics should we track in production?

---

**Plan Status:** ✅ Ready for Implementation  
**Next Step:** Begin Phase 1 - Project Setup & Dependencies
```

