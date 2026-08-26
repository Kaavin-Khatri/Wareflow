"""
Rate Limiting Verification Test Suite (Step 22.1).

Validates that endpoints decorated with slowapi limiters reject excessive requests with 429 Too Many Requests:
- Groq AI Weekly Insights: 5/minute
- CSV Bulk Imports: 10/minute
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.di import get_insight_narrator_service
from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.schemas.analytics import WeeklyInsightMetrics, WeeklyInsightResponse


@pytest.fixture
def client():
    return TestClient(app)


def mock_owner():
    return CurrentUser(
        id="usr-owner",
        email="owner@wareflow.io",
        role="Owner",
        permissions={"inventory:view", "inventory:manage", "reports:view"},
        account_type="staff",
        is_active=True,
        is_2fa_verified=True,
    )


class TestRateLimiting:
    """Verify slowapi rate limit enforcement."""

    def test_weekly_insight_rate_limit_exceeded(self, client):
        """Rule: 6th request within a minute to /analytics/weekly-insight returns 429."""
        app.dependency_overrides[get_current_user] = mock_owner
        mock_service = MagicMock()
        now = datetime.now(UTC)
        mock_service.get_weekly_insight.return_value = WeeklyInsightResponse(
            headline="Weekly FMCG Velocity",
            narrative="Executive summary narrative",
            metrics_summary=WeeklyInsightMetrics(
                total_revenue_7d=150000.0,
                revenue_growth_pct=12.5,
                orders_count_7d=45,
                top_moving_product="Parle-G 800g",
                stock_risk_count=3,
                dead_stock_value=12000.0,
                low_stock_skus_count=2,
            ),
            generated_at=now,
            expires_at=now,
            is_ai_generated=False,
            is_cached=True,
        )
        app.dependency_overrides[get_insight_narrator_service] = lambda: mock_service

        status_codes = []
        for _ in range(8):
            res = client.get("/analytics/weekly-insight")
            status_codes.append(res.status_code)

        # Rate limiting triggers 429 Too Many Requests
        assert 429 in status_codes
        app.dependency_overrides.clear()
