from uuid import uuid4

from fastapi.testclient import TestClient
from jose import jwt

from app.core.settings import settings
from app.main import app
from app.schemas.research import ResearchRequest
from app.services.llm.models import JudgeResult, MarketIntelligenceReport
from app.services.research_service import ResearchService

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_login_endpoint():
    response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "Bearer"
    assert payload["user"]["email"] == "user@example.com"

    decoded = jwt.decode(
        payload["access_token"],
        settings.secrets.get_jwt_secret(),
        algorithms=[settings.jwt_algorithm],
    )
    assert decoded["sub"] == "user@example.com"


def test_login_with_long_password_is_supported():
    long_password = "a" * 80
    unique_email = f"longpassword-{uuid4().hex[:8]}@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={"email": unique_email, "password": long_password},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": long_password},
    )
    assert login_response.status_code == 200


def test_invalid_login_returns_unauthorized():
    response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_registration_creates_new_user():
    unique_email = f"newuser-{uuid4().hex[:8]}@example.com"
    response = client.post(
        "/api/auth/register",
        json={"email": unique_email, "password": "NewPassword123!"},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["user"]["email"] == unique_email


def test_research_endpoint_requires_auth_token():
    response = client.post(
        "/api/research",
        json={
            "competitors": ["OpenAI"],
            "topics": ["AI"],
            "urls": ["https://example.com"],
            "context": "test context",
        },
    )
    assert response.status_code == 401


def test_research_endpoint_with_valid_token():
    login_response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "Password123!"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/api/research",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "competitors": ["OpenAI"],
            "topics": ["AI"],
            "urls": ["https://example.com"],
            "context": "test context",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["hallucinationCheck"]["status"] in {"Supported", "Needs review"}
    assert payload["themes"][0]["title"]


def test_research_service_is_dynamic_for_any_input():
    service = ResearchService()
    payload = ResearchRequest(
        competitors=["Acme", "Globex"],
        topics=["AI assistants", "workflow automation"],
        urls=["https://blog.google/technology/ai/"],
        context="Summarize the latest developments for arbitrary competitors and topics.",
    )

    result = service.create_research(payload)

    assert result.themes
    assert result.competitorActivities or result.themes[0].summary
    assert result.hallucinationCheck.status in {"Supported", "Needs review"}


def test_research_service_explicitly_reports_missing_topics_and_competitors(monkeypatch):
    service = ResearchService()
    payload = ResearchRequest(
        competitors=["OpenAI", "Anthropic"],
        topics=["AI agents", "enterprise automation"],
        urls=["https://example.com"],
        context="Summarize only the supplied source content.",
    )

    class DummyAnalyzer:
        def analyze_articles(self, scraped_articles, competitors, topics, context):
            return (
                MarketIntelligenceReport(
                    executive_summary="No relevant information found in the provided sources.",
                    insights_grouped_by_theme=[],
                    market_trends=[],
                    competitor_activities=[],
                    business_insights=[],
                    statistics=[],
                    companies_mentioned=[],
                    source_traceability=[{"source_url": "https://example.com"}],
                ),
                JudgeResult(
                    accuracy_score=0.5,
                    completeness_score=0.5,
                    hallucination_detection="No unsupported claims detected in the generated summary.",
                    unsupported_claims=[],
                    missing_information=[],
                    overall_feedback="The report was generated from the available article analyses and presented in a structured summary.",
                ),
            )

    monkeypatch.setattr(service.scraper, "scrape_articles", lambda urls: [{"url": urls[0], "article_text": "Nothing relevant"}])
    service.analyzer = DummyAnalyzer()

    result = service.create_research(payload)

    assert len(result.themes) == len(payload.topics)
    assert all("No information found for this topic in the provided sources." in theme.summary for theme in result.themes)
    assert len(result.competitorActivities) == len(payload.competitors)
    assert all("No competitor activity found in the provided sources." in activity.activity for activity in result.competitorActivities)


def test_history_endpoint_requires_auth_token():
    response = client.get("/api/history")
    assert response.status_code == 401


def test_history_endpoint_with_valid_token():
    login_response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "Password123!"},
    )
    token = login_response.json()["access_token"]

    response = client.get("/api/history", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["title"] == "Enterprise AI Research"
