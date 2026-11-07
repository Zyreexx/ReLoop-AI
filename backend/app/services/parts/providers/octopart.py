"""
Octopart / Nexar Component Parts Provider.
Queries the Nexar / Octopart GraphQL API for electronic components, connectors, ICs, and authorized distributor stock.
Official API: https://api.nexar.com/graphql
"""
import logging
import os
import time
from typing import List, Optional
import httpx
from app.services.parts.base import BasePartsProvider, PartListing, ProviderStatus

logger = logging.getLogger("reloop-ai.parts.octopart")


class OctopartPartsProvider(BasePartsProvider):
    def __init__(self):
        self.client_id = os.getenv("NEXAR_CLIENT_ID", os.getenv("OCTOPART_API_KEY", "")).strip()
        self.client_secret = os.getenv("NEXAR_CLIENT_SECRET", "").strip()
        self.endpoint = "https://api.nexar.com/graphql"
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

    @property
    def provider_name(self) -> str:
        return "octopart"

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def get_status(self) -> ProviderStatus:
        configured = self.is_configured()
        return ProviderStatus(
            provider_name=self.provider_name,
            is_configured=configured,
            is_available=configured,
            requires_auth=True,
            notes="Configured via Nexar/Octopart GraphQL API" if configured else "Missing NEXAR_CLIENT_ID or NEXAR_CLIENT_SECRET",
        )

    async def _get_access_token(self) -> Optional[str]:
        if not self.is_configured():
            return None
        if self._token and time.time() < (self._token_expires_at - 60):
            return self._token

        token_url = "https://identity.nexar.com/connect/token"
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(
                    token_url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self._token = data.get("access_token")
                    expires_in = data.get("expires_in", 3600)
                    self._token_expires_at = time.time() + float(expires_in)
                    return self._token
                else:
                    logger.warning(f"Nexar token error: {resp.status_code} - {resp.text}")
                    return None
        except Exception as e:
            logger.error(f"Failed to fetch Nexar token: {e}")
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

        graphql_query = """
        query SearchParts($q: String!, $limit: Int!) {
          supSearch(q: $q, limit: $limit) {
            results {
              part {
                mpn
                manufacturer { name }
                shortDescription
                octopartUrl
                sellers {
                  company { name }
                  offers {
                    price
                    currency
                    inventoryLevel
                  }
                }
              }
            }
          }
        }
        """
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        query_str = f"{device_model} {component}"
        payload = {
            "query": graphql_query,
            "variables": {"q": query_str, "limit": max_results},
        }

        usd_to_inr = float(os.getenv("USD_TO_INR_RATE", "85.0"))
        listings: List[PartListing] = []

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.endpoint, json=payload, headers=headers)
                if resp.status_code != 200:
                    logger.warning(f"Octopart search error: {resp.status_code} - {resp.text}")
                    return []

                body = resp.json()
                results = body.get("data", {}).get("supSearch", {}).get("results", [])

                for item in results:
                    part = item.get("part", {})
                    mpn = part.get("mpn", "")
                    mfg = part.get("manufacturer", {}).get("name", "OEM")
                    desc = part.get("shortDescription", f"{mfg} {component}")
                    url = part.get("octopartUrl", f"https://octopart.com/search?q={query_str}")

                    # Check sellers
                    sellers = part.get("sellers", [])
                    price_val = 0.0
                    seller_name = "Authorized Distributor"
                    for s in sellers:
                        offers = s.get("offers", [])
                        if offers:
                            price_val = float(offers[0].get("price", 0.0))
                            seller_name = s.get("company", {}).get("name", seller_name)
                            break

                    price_inr = price_val * usd_to_inr if price_val > 0 else 0.0

                    listing = PartListing(
                        id=f"octopart_{mpn or hash(desc)}",
                        title=f"{mfg} {mpn}: {desc}",
                        provider="octopart",
                        component=component,
                        price=price_val,
                        currency="USD",
                        price_inr=round(price_inr, 2),
                        condition="Brand New (Authorized Distributor)",
                        item_url=url,
                        seller_name=seller_name,
                        seller_rating=99.0,
                        in_stock=True,
                        is_live=True,
                        part_number=mpn,
                        compatibility_notes=f"Authorized OEM Electronic Component ({mfg})",
                    )
                    listings.append(listing)
                return listings
        except Exception as e:
            logger.error(f"Octopart query failed: {e}")
            return []

