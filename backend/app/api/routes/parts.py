"""
Parts Marketplace API endpoints for live replacement hardware and pricing.
"""
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.services.parts.aggregator import parts_service
from app.services.parts.base import MarketplaceSearchResult, ProviderStatus

router = APIRouter(prefix="/parts", tags=["Parts Marketplace"])


@router.get("/search", response_model=MarketplaceSearchResult)
async def search_replacement_parts(
    device_model: str = Query(..., description="Device model or slug (e.g. 'ThinkPad T14', 'MacBook Air M1')"),
    component: str = Query(..., description="Component identifier (e.g. 'battery', 'ssd', 'display', 'keyboard')"),
    max_results: int = Query(4, ge=1, le=20, description="Max results per provider"),
    force_refresh: bool = Query(False, description="Bypass cache and force fresh live retrieval"),
):
    """
    Search live parts across supported marketplaces (eBay, iFixit, Octopart) with automatic
    fallback to curated OEM catalog estimates when live results are unavailable.
    """
    try:
        return await parts_service.search_parts(
            device_model=device_model,
            component=component,
            max_results_per_provider=max_results,
            force_refresh=force_refresh,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query parts marketplace: {str(e)}")


@router.get("/pricing-summary", response_model=Dict[str, MarketplaceSearchResult])
async def get_device_parts_summary(
    device_model: str = Query(..., description="Device model or slug"),
):
    """
    Retrieve parts pricing and availability across all primary repairable components
    (battery, ssd, ram, display, keyboard, thermals) for a specific device.
    """
    try:
        return await parts_service.get_pricing_summary(device_model=device_model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch parts summary: {str(e)}")


@router.get("/providers", response_model=List[ProviderStatus])
def get_marketplace_providers():
    """
    Check operational status and configuration of integrated marketplace providers
    (eBay Developer API, iFixit Store & Guides, Octopart/Nexar).
    """
    return parts_service.get_provider_statuses()

