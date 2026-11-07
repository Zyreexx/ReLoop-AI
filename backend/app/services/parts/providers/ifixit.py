"""
iFixit Marketplace & Repair Guides Provider.
Uses iFixit 2.0 Public REST API to query genuine replacement parts, tools, and repairability information.
Official API: https://www.ifixit.com/api/2.0/
"""
import logging
import os
from typing import List, Optional
import httpx
from app.services.parts.base import BasePartsProvider, PartListing, ProviderStatus

logger = logging.getLogger("reloop-ai.parts.ifixit")


class IFixitPartsProvider(BasePartsProvider):
    def __init__(self):
        self.base_url = "https://www.ifixit.com/api/2.0"
        self.api_key = os.getenv("IFIXIT_API_KEY", "").strip()

    @property
    def provider_name(self) -> str:
        return "ifixit"

    def is_configured(self) -> bool:
        # Public catalog querying is available without secret API key
        return True

    def get_status(self) -> ProviderStatus:
        return ProviderStatus(
            provider_name=self.provider_name,
            is_configured=True,
            is_available=True,
            requires_auth=False,
            notes="iFixit Public Store & Guides API v2.0 (Active)",
        )

    async def search_parts(
        self,
        device_model: str,
        component: str,
        max_results: int = 5,
    ) -> List[PartListing]:
        query = f"{device_model} {component}"
        search_endpoint = f"{self.base_url}/suggest/{query}?do=products"
        headers = {
            "User-Agent": "ReLoop-AI-LifecycleEngine/1.0",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"api {self.api_key}"

        usd_to_inr = float(os.getenv("USD_TO_INR_RATE", "85.0"))
        listings: List[PartListing] = []

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(search_endpoint, headers=headers)
                if resp.status_code != 200:
                    logger.debug(f"iFixit search non-200 response: {resp.status_code}")
                    return []

                data = resp.json()
                results = data.get("results", []) if isinstance(data, dict) else []

                for r in results[:max_results]:
                    # Extract price if present
                    price_str = str(r.get("price", "0.0")).replace("$", "").strip()
                    try:
                        price_usd = float(price_str)
                    except ValueError:
                        price_usd = 0.0

                    price_inr = price_usd * usd_to_inr if price_usd > 0 else 0.0
                    item_id = str(r.get("productid", r.get("id", "")))
                    item_url = r.get("url", f"https://www.ifixit.com/Store/Parts?query={query}")

                    listing = PartListing(
                        id=f"ifixit_{item_id or hash(r.get('text', ''))}",
                        title=r.get("text", f"{device_model} {component}"),
                        provider="ifixit",
                        component=component,
                        price=price_usd,
                        currency="USD",
                        price_inr=round(price_inr, 2),
                        condition="OEM / iFixit Certified",
                        item_url=item_url,
                        seller_name="iFixit Official Store",
                        seller_rating=99.0,
                        in_stock=True,
                        is_live=True,
                        compatibility_notes="iFixit Certified Part with Step-by-Step Repair Guide",
                    )
                    listings.append(listing)
                return listings
        except Exception as e:
            logger.warning(f"iFixit API search request failed: {e}")
            return []

