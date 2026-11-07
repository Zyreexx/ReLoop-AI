"""
Tests for Live Parts Marketplace API and Aggregator Service.
Validates provider registration, caching, currency handling, catalog fallback,
and live API contracts.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.services.parts.base import PartListing, MarketplaceSearchResult
from app.services.parts.aggregator import parts_service

client = TestClient(app)


def test_parts_providers_status_endpoint():
    resp = client.get("/api/parts/providers")
    assert resp.status_code == 200
    providers = resp.json()
    assert isinstance(providers, list)
    names = [p["provider_name"] for p in providers]
    assert "ifixit" in names
    assert "ebay" in names
    assert "octopart" in names


def test_parts_search_fallback_to_catalog():
    # If unconfigured or offline, fallback to curated catalog estimate
    resp = client.get("/api/parts/search", params={"device_model": "Dell Latitude 5420", "component": "battery"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["device_model"] == "Dell Latitude 5420"
    assert data["component"] == "battery"
    assert "listings" in data
    assert len(data["listings"]) >= 1
    # Check that listings have required fields
    first = data["listings"][0]
    assert "id" in first
    assert "price" in first
    assert "price_inr" in first
    assert "provider" in first
    assert "is_live" in first
    assert "retrieved_at" in first


def test_parts_search_caching():
    # First search
    resp1 = client.get(
        "/api/parts/search",
        params={"device_model": "Lenovo ThinkPad T14 Gen 1", "component": "ssd"},
    )
    assert resp1.status_code == 200
    data1 = resp1.json()

    # Second search should hit the cache
    resp2 = client.get(
        "/api/parts/search",
        params={"device_model": "Lenovo ThinkPad T14 Gen 1", "component": "ssd"},
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["cache_hit"] is True
    assert data2["median_price_inr"] == data1["median_price_inr"]


@pytest.mark.anyio
async def test_live_mocked_provider_search():
    # Test aggregator with a simulated live provider result
    mock_listing = PartListing(
        id="ebay_12345",
        title="OEM ThinkPad T14 Battery 50Wh",
        provider="ebay",
        component="battery",
        price=45.0,
        currency="USD",
        price_inr=3825.0,
        condition="New",
        item_url="https://www.ebay.com/itm/12345",
        seller_name="genuine_parts_inc",
        seller_rating=99.4,
        in_stock=True,
        is_live=True,
    )

    with patch.object(
        parts_service.providers["ebay"],
        "search_parts",
        new=AsyncMock(return_value=[mock_listing]),
    ):
        res = await parts_service.search_parts(
            device_model="ThinkPad T14",
            component="battery",
            force_refresh=True,
        )
        assert res.is_live is True
        assert res.live_provider_count >= 1
        assert res.cheapest_listing is not None
        assert res.cheapest_listing.provider == "ebay"
        assert res.cheapest_listing.price_inr == 3825.0


def test_parts_pricing_summary_endpoint():
    resp = client.get("/api/parts/pricing-summary", params={"device_model": "MacBook Air M1"})
    assert resp.status_code == 200
    summary = resp.json()
    assert isinstance(summary, dict)
    assert "battery" in summary
    assert "ssd" in summary
    assert "display" in summary
    assert summary["battery"]["component"] == "battery"

