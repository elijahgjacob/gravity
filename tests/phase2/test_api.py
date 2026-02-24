"""Integration tests for FastAPI application."""

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns API information."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert "message" in data
    assert "version" in data
    assert data["version"] == "1.0.0"
    assert "/docs" in data["docs"]


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "version" in data
    assert data["version"] == "1.0.0"


def test_ready_endpoint():
    """Test readiness check endpoint."""
    response = client.get("/api/ready")

    assert response.status_code == 200
    data = response.json()

    assert "ready" in data
    assert "dependencies" in data
    assert isinstance(data["dependencies"], dict)


def test_retrieve_endpoint_valid_request():
    """Test retrieve endpoint with valid request."""
    request_data = {
        "query": "I need running shoes",
        "context": {
            "age": 25,
            "gender": "male",
            "location": "San Francisco, CA",
            "interests": ["fitness"],
        },
    }

    response = client.post("/api/retrieve", json=request_data)

    assert response.status_code == 200
    data = response.json()

    assert "ad_eligibility" in data
    assert "extracted_categories" in data
    assert "campaigns" in data
    assert "latency_ms" in data
    assert "metadata" in data

    assert 0.0 <= data["ad_eligibility"] <= 1.0
    assert isinstance(data["extracted_categories"], list)
    assert isinstance(data["campaigns"], list)


def test_retrieve_endpoint_no_context():
    """Test retrieve endpoint without context."""
    request_data = {"query": "test query"}

    response = client.post("/api/retrieve", json=request_data)

    assert response.status_code == 200
    data = response.json()

    assert "ad_eligibility" in data
    assert "extracted_categories" in data


def test_retrieve_endpoint_empty_query():
    """Test retrieve endpoint with empty query."""
    request_data = {"query": ""}

    response = client.post("/api/retrieve", json=request_data)

    assert response.status_code == 422  # Validation error


def test_retrieve_endpoint_long_query():
    """Test retrieve endpoint with too long query."""
    request_data = {"query": "a" * 501}

    response = client.post("/api/retrieve", json=request_data)

    assert response.status_code == 422  # Validation error


def test_retrieve_endpoint_invalid_age():
    """Test retrieve endpoint with invalid age in context."""
    request_data = {"query": "test query", "context": {"age": -1}}

    response = client.post("/api/retrieve", json=request_data)

    assert response.status_code == 422  # Validation error


def test_latency_header_present():
    """Test that X-Latency-Ms header is added to responses."""
    response = client.get("/api/health")

    assert response.status_code == 200
    assert "X-Latency-Ms" in response.headers

    latency = float(response.headers["X-Latency-Ms"])
    assert latency >= 0.0


def test_openapi_docs_available():
    """Test that OpenAPI documentation is available."""
    response = client.get("/docs")

    assert response.status_code == 200


def test_openapi_schema():
    """Test OpenAPI schema is generated."""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()

    assert "openapi" in schema
    assert "info" in schema
    assert schema["info"]["title"] == "Ad Retrieval API"
    assert schema["info"]["version"] == "1.0.0"
