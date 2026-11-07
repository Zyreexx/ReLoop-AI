"""
Base models and abstract interface for Live Parts Marketplace Providers.
Ensures provider-independent architecture, strict currency handling,
and explicit differentiation between live retrieved prices and catalog estimates.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class PartListing(BaseModel):
    id: str
    title: str
    provider: str  # "ebay", "ifixit", "octopart", "reloop_catalog"
    component: str  # "battery", "ssd", "ram", "display", "keyboard", "thermals", "motherboard", etc.
    price: float
    currency: str = "USD"
    price_inr: float
    condition: str = "Refurbished / Tested"  # "New", "Refurbished", "Used", "OEM Pulled"
    item_url: str
    seller_name: Optional[str] = None
    seller_rating: Optional[float] = None
    in_stock: bool = True
    is_live: bool = True  # True = live API retrieval, False = catalog estimation
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    compatibility_notes: Optional[str] = None
    part_number: Optional[str] = None


class MarketplaceSearchResult(BaseModel):
    device_model: str
    component: str
    listings: List[PartListing] = Field(default_factory=list)
    cheapest_listing: Optional[PartListing] = None
    median_price_inr: Optional[float] = None
    live_provider_count: int = 0
    is_live: bool = False
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    cache_hit: bool = False


class ProviderStatus(BaseModel):
    provider_name: str
    is_configured: bool
    is_available: bool
    requires_auth: bool
    rate_limit_remaining: Optional[int] = None
    notes: Optional[str] = None


class BasePartsProvider(ABC):
    """Abstract base class for third-party replacement parts marketplace providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'ebay', 'ifixit', 'octopart')."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if necessary API credentials / environment variables are configured."""
        pass

    @abstractmethod
    async def search_parts(
        self,
        device_model: str,
        component: str,
        max_results: int = 5,
    ) -> List[PartListing]:
        """Search replacement parts for a specific device model and component."""
        pass

    @abstractmethod
    def get_status(self) -> ProviderStatus:
        """Return provider configuration status and health."""
        pass

