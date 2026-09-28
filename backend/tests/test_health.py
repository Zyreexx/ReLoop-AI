from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_config_defaults():
    assert "http://localhost:3000" in settings.CORS_ORIGINS
    assert settings.MAX_UPLOAD_MB == 10
    assert settings.ENVIRONMENT == "development"
    assert settings.GEMINI_MODEL in ["gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-3.5-flash", "gemini-flash-latest"]
