"""
eBay Marketplace Provider for replacement laptop components.
Integrates with eBay Browse API / Finding API for live listings, seller feedback, and pricing.
"""
import logging
import os
import time
from typing import Dict, List, Optional
import httpx
from app.services.parts.base import BasePartsProvider, PartListing, ProviderStatus

logger = logging.getLogger("reloop-ai.parts.ebay")


class EbayPartsProvider(BasePartsProvider):
    def __init__(self):
        self.client_id = os.getenv("EBAY_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("EBAY_CLIENT_SECRET", "").strip()
        self.environment = os.getenv("EBAY_ENV", "PRODUCTION").upper()
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

    @property
    def provider_name(self) -> str:
        return "ebay"

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def get_status(self) -> ProviderStatus:
        configured = self.is_configured()
        return ProviderStatus(
            provider_name=self.provider_name,
            is_configured=configured,
            is_available=configured,
            requires_auth=True,
            notes="Configured with OAuth Application Credentials" if configured else "Missing EBAY_CLIENT_ID or EBAY_CLIENT_SECRET in environment",
        )

    async def _get_access_token(self) -> Optional[str]:
        if not self.is_configured():
            return None
        if self._token and time.time() < (self._token_expires_at - 60):
            return self._token

        token_url = (
            "https://api.ebay.com/identity/v1/oauth2/token"
            if self.environment == "PRODUCTION"
            else "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        )
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(
                    token_url,
                    data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"},
                    auth=(self.client_id, self.client_secret),
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self._token = data.get("access_token")
                    expires_in = data.get("expires_in", 7200)
                    self._token_expires_at = time.time() + float(expires_in)
                    return self._token
                else:
                    logger.warning(f"eBay OAuth error: {resp.status_code} - {resp.text}")
                    return None
        except Exception as e:
            logger.error(f"Failed to authenticate with eBay OAuth: {e}")
            return None

    async def search_parts(
        self,
        device_model: str,
        component: str,
        max_results: int = 5,
    ) -> List[PartListing]:
        if not self.is_configured():
            return []

        token = await self._get_access_token()
        if not token:
            return []

        query = f"{device_model} replacement {component}"
        search_url = (
            "https://api.ebay.com/buy/browse/v1/item_summary/search"
            if self.environment == "PRODUCTION"
            else "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"
        )
        params = {"q": query, "limit": str(max_results), "filter": "buyingOptions:{FIXED_PRICE}"}
        headers = {"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(search_url, params=params, headers=headers)
                if resp.status_code != 200:
                    logger.warning(f"eBay search error: {resp.status_code} - {resp.text}")
                    return []
                
                data = resp.json()
                items = data.get("itemSummaries", [])
                listings: List[PartListing] = []

                usd_to_inr = float(os.getenv("USD_TO_INR_RATE", "85.0"))

                for it in items:
                    price_info = it.get("price", {})
                    price_val = float(price_info.get("value", 0.0))
                    currency = price_info.get("currency", "USD")
                    price_inr = price_val * usd_to_inr if currency == "USD" else price_val

                    seller = it.get("seller", {})
                    condition = it.get("condition", "OEM Tested")

                    listing = PartListing(
                        id=f"ebay_{it.get('itemId')}",
                        title=it.get("title", f"{device_model} {component}"),
                        provider="ebay",
                        component=component,
                        price=price_val,
                        currency=currency,
                        price_inr=round(price_inr, 2),
                        condition=condition,
                        item_url=it.get("itemWebUrl", ""),
                        seller_name=seller.get("username"),
                        seller_rating=float(seller.get("feedbackPercentage", 98.0)) if seller.get("feedbackPercentage") else None,
                        in_stock=True,
                        is_live=True,
                        compatibility_notes=f"eBay Live Fixed-Price Listing ({condition})",
                    )
                    listings.append(listing)
                return listings
        except Exception as e:
            logger.error(f"eBay search request failed: {e}")
            return []

