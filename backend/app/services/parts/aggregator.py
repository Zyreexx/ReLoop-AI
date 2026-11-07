"""
Parts Marketplace Aggregator Service.
Aggregates listings across eBay, iFixit, and Octopart with TTL caching,
rate limiting, currency normalization, and catalog fallback.
"""
import asyncio
from datetime import datetime, timezone
import logging
import time
from typing import Dict, List, Optional, Tuple
from app.services.parts.base import (
    BasePartsProvider,
    MarketplaceSearchResult,
    PartListing,
    ProviderStatus,
)
from app.services.parts.providers.ebay import EbayPartsProvider
from app.services.parts.providers.ifixit import IFixitPartsProvider
from app.services.parts.providers.octopart import OctopartPartsProvider
from app.knowledge.loader import get_repair_cost_with_fallback

logger = logging.getLogger("reloop-ai.parts.service")


class PartsMarketplaceService:
    def __init__(self, cache_ttl_seconds: int = 3600):
        self.cache_ttl = cache_ttl_seconds
        self.providers: Dict[str, BasePartsProvider] = {
            "ifixit": IFixitPartsProvider(),
            "ebay": EbayPartsProvider(),
            "octopart": OctopartPartsProvider(),
        }
        # In-memory TTL cache: key -> (timestamp, MarketplaceSearchResult)
        self._cache: Dict[str, Tuple[float, MarketplaceSearchResult]] = {}

    def get_provider_statuses(self) -> List[ProviderStatus]:
        return [prov.get_status() for prov in self.providers.values()]

    async def search_parts(
        self,
        device_model: str,
        component: str,
        max_results_per_provider: int = 4,
        force_refresh: bool = False,
    ) -> MarketplaceSearchResult:
        cache_key = f"{device_model.lower().strip()}::{component.lower().strip()}"
        now = time.time()

        # Check Cache
        if not force_refresh and cache_key in self._cache:
            ts, cached_result = self._cache[cache_key]
            if (now - ts) < self.cache_ttl:
                # Return cached with cache_hit = True
                copy_res = cached_result.model_copy()
                copy_res.cache_hit = True
                return copy_res

        # Query live providers concurrently
        tasks = []
        for name, provider in self.providers.items():
            tasks.append(provider.search_parts(device_model, component, max_results=max_results_per_provider))

        provider_results = await asyncio.gather(*tasks, return_exceptions=True)

        all_listings: List[PartListing] = []
        live_provider_count = 0

        for res in provider_results:
            if isinstance(res, list) and res:
                all_listings.extend(res)
                live_provider_count += 1
            elif isinstance(res, Exception):
                logger.warning(f"Provider search exception: {res}")

        # If live listings were found, sort by INR price
        if all_listings:
            all_listings.sort(key=lambda x: (x.price_inr if x.price_inr > 0 else float("inf")))
            prices = [x.price_inr for x in all_listings if x.price_inr > 0]
            cheapest = all_listings[0]
            import statistics
            med_price = round(statistics.median(prices), 2) if prices else cheapest.price_inr

            search_result = MarketplaceSearchResult(
                device_model=device_model,
                component=component,
                listings=all_listings,
                cheapest_listing=cheapest,
                median_price_inr=med_price,
                live_provider_count=live_provider_count,
                is_live=True,
                cache_hit=False,
            )
        else:
            # Fallback to curated OEM catalog estimate
            cat_cost = get_repair_cost_with_fallback(device_model, component)
            min_c = float(cat_cost.get("min", 2500))
            max_c = float(cat_cost.get("max", 5000))
            avg_c = (min_c + max_c) / 2.0

            fallback_listing = PartListing(
                id=f"catalog_{device_model}_{component}",
                title=f"{device_model} Replacement {component.capitalize()} (OEM Specification)",
                provider="reloop_catalog",
                component=component,
                price=round(avg_c / 85.0, 2),
                currency="USD",
                price_inr=avg_c,
                condition="OEM Specification",
                item_url="",
                seller_name="ReLoop Hardware Specifications Catalog",
                seller_rating=None,
                in_stock=True,
                is_live=False,
                compatibility_notes=cat_cost.get("note", "Curated OEM hardware catalog estimate"),
            )

            search_result = MarketplaceSearchResult(
                device_model=device_model,
                component=component,
                listings=[fallback_listing],
                cheapest_listing=fallback_listing,
                median_price_inr=avg_c,
                live_provider_count=0,
                is_live=False,
                cache_hit=False,
            )

        # Store in cache
        self._cache[cache_key] = (now, search_result)
        return search_result

    async def get_pricing_summary(self, device_model: str) -> Dict[str, MarketplaceSearchResult]:
        """Fetch pricing across all standard repairable subsystems for a device."""
        components = ["battery", "ssd", "ram", "display", "keyboard", "thermals"]
        results: Dict[str, MarketplaceSearchResult] = {}

        tasks = [self.search_parts(device_model, comp) for comp in components]
        completed = await asyncio.gather(*tasks, return_exceptions=True)

        for comp, res in zip(components, completed):
            if isinstance(res, MarketplaceSearchResult):
                results[comp] = res
            else:
                logger.error(f"Error fetching pricing summary for {comp}: {res}")
        return results


# Global singleton instance
parts_service = PartsMarketplaceService()

