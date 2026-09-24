"""
Thread-safe in-memory store for MVP product records, evidence items, condition profiles, and recommendations.
Designed to be swappable with PostgreSQL/SQLModel while preserving fast hackathon demo workflows.
"""
from threading import Lock
from typing import Dict, List, Optional
from app.schemas.product import ProductRecord
from app.schemas.evidence import EvidenceItem
from app.schemas.condition import ConditionProfile
from app.schemas.recommendation import RecommendationResponse


class MemoryStore:
    def __init__(self):
        self._lock = Lock()
        self.products: Dict[str, ProductRecord] = {}
        self.evidence: Dict[str, List[EvidenceItem]] = {}  # product_id -> list of evidence
        self.profiles: Dict[str, ConditionProfile] = {}  # product_id -> condition profile
        self.recommendations: Dict[str, RecommendationResponse] = {}  # recommendation_id or product_id -> recommendation

    def save_product(self, product: ProductRecord) -> ProductRecord:
        with self._lock:
            self.products[product.id] = product
            if product.id not in self.evidence:
                self.evidence[product.id] = []
            return product

    def get_product(self, product_id: str) -> Optional[ProductRecord]:
        with self._lock:
            return self.products.get(product_id)

    def add_evidence(self, product_id: str, item: EvidenceItem) -> EvidenceItem:
        with self._lock:
            item.product_id = product_id
            if product_id not in self.evidence:
                self.evidence[product_id] = []
            self.evidence[product_id].append(item)
            return item

    def add_evidence_batch(self, product_id: str, items: List[EvidenceItem]) -> List[EvidenceItem]:
        with self._lock:
            if product_id not in self.evidence:
                self.evidence[product_id] = []
            for item in items:
                item.product_id = product_id
                self.evidence[product_id].append(item)
            return items

    def get_evidence(self, product_id: str) -> List[EvidenceItem]:
        with self._lock:
            return list(self.evidence.get(product_id, []))

    def save_profile(self, profile: ConditionProfile) -> ConditionProfile:
        with self._lock:
            self.profiles[profile.product_id] = profile
            return profile

    def get_profile(self, product_id: str) -> Optional[ConditionProfile]:
        with self._lock:
            return self.profiles.get(product_id)

    def save_recommendation(self, rec: RecommendationResponse) -> RecommendationResponse:
        with self._lock:
            self.recommendations[rec.id] = rec
            self.recommendations[rec.product_id] = rec
            return rec

    def get_recommendation(self, identifier: str) -> Optional[RecommendationResponse]:
        with self._lock:
            return self.recommendations.get(identifier)

    def clear(self):
        with self._lock:
            self.products.clear()
            self.evidence.clear()
            self.profiles.clear()
            self.recommendations.clear()


store = MemoryStore()
