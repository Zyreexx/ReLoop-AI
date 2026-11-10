"""
Location-based service for finding nearby electronics repair shops and certified e-waste recyclers.
Supports Google Places API (primary high-coverage provider) and OpenStreetMap Overpass API (mirror-resilient fallback)
with strict R2v3 / e-Stewards verification.
"""
import logging
import math
from typing import List, Optional, Tuple
import httpx

from app.config import settings
from app.knowledge.recycler_certifications import verify_facility_certification
from app.schemas.locator import CertificationStandardInfo, LocatorItem, LocatorSearchResult

logger = logging.getLogger("reloop-ai.locator")

OVERPASS_MIRRORS = [
    "https://overpass.openstreetmap.fr/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the great-circle distance between two points in kilometers."""
    R = 6371.0  # Earth's mean radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)


class LocatorService:
    def __init__(self):
        self.nominatim_url = "https://nominatim.openstreetmap.org/search"
        self.google_geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self.google_places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

    async def geocode_query(self, query: str) -> Optional[Tuple[float, float, str]]:
        """Geocodes a city, postal code, or landmark into (latitude, longitude, display_name)."""
        # Try Google Geocoding first if API key is provided
        if settings.GOOGLE_MAPS_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=6.0) as client:
                    resp = await client.get(
                        self.google_geocode_url,
                        params={"address": query, "key": settings.GOOGLE_MAPS_API_KEY},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("status") == "OK" and data.get("results"):
                            first = data["results"][0]
                            lat = float(first["geometry"]["location"]["lat"])
                            lng = float(first["geometry"]["location"]["lng"])
                            formatted = first.get("formatted_address", query)
                            return lat, lng, formatted
            except Exception as e:
                logger.warning(f"Google Geocoding request failed: {e}")

        # Fallback to OpenStreetMap Nominatim
        headers = {"User-Agent": "ReLoop-AI-CircularLocator/1.0"}
        params = {"q": query, "format": "json", "limit": "1"}
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(self.nominatim_url, params=params, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if data:
                        first = data[0]
                        return float(first["lat"]), float(first["lon"]), first.get("display_name", query)
        except Exception as e:
            logger.warning(f"Nominatim geocoding request failed: {e}")
        return None

    async def _search_google_places(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        category: str,
    ) -> List[LocatorItem]:
        """Queries Google Places Nearby Search API for verified facilities."""
        if not settings.GOOGLE_MAPS_API_KEY:
            return []

        norm_cat = (category or "ALL").upper()
        if norm_cat in ["REPAIR", "REPAIR_SHOP"]:
            keyword = "electronics repair OR computer repair OR phone repair service"
        elif norm_cat in ["RECYCLE", "RECYCLER", "RECYCLING"]:
            keyword = "e-waste recycling OR electronic recycling OR scrap electronics"
        else:
            keyword = "electronics repair OR computer repair OR e-waste recycling"

        radius_meters = min(int(radius_km * 1000), 50000)
        params = {
            "location": f"{latitude},{longitude}",
            "radius": radius_meters,
            "keyword": keyword,
            "key": settings.GOOGLE_MAPS_API_KEY,
        }

        items: List[LocatorItem] = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.google_places_url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    for place in results:
                        name = place.get("name")
                        if not name:
                            continue

                        geom = place.get("geometry", {}).get("location", {})
                        p_lat = float(geom.get("lat", latitude))
                        p_lon = float(geom.get("lng", longitude))
                        dist = haversine_distance_km(latitude, longitude, p_lat, p_lon)

                        place_id = place.get("place_id")
                        rating = place.get("rating")
                        user_ratings_total = place.get("user_ratings_total")
                        open_now = place.get("opening_hours", {}).get("open_now")

                        name_lower = name.lower()
                        is_recycling = (
                            "recycl" in name_lower
                            or "scrap" in name_lower
                            or "waste" in name_lower
                            or any("recycl" in t.lower() for t in place.get("types", []))
                        )

                        cert_data = verify_facility_certification(name)
                        if is_recycling:
                            item_cat = "CERTIFIED_RECYCLER" if cert_data else "E_WASTE_COLLECTOR"
                        else:
                            item_cat = "REPAIR_SHOP"

                        if norm_cat in ["REPAIR", "REPAIR_SHOP"] and item_cat != "REPAIR_SHOP":
                            continue
                        if norm_cat in ["RECYCLE", "RECYCLER", "RECYCLING"] and item_cat not in [
                            "CERTIFIED_RECYCLER",
                            "E_WASTE_COLLECTOR",
                        ]:
                            continue

                        badge = cert_data["standard"] if cert_data else None
                        cert_list = [badge] if badge else []
                        address = place.get("vicinity") or place.get("formatted_address") or f"{dist} km from search origin"

                        g_maps_url = (
                            f"https://www.google.com/maps/search/?api=1&query={p_lat},{p_lon}&query_place_id={place_id}"
                            if place_id
                            else f"https://www.google.com/maps/dir/?api=1&destination={p_lat},{p_lon}"
                        )

                        items.append(
                            LocatorItem(
                                id=f"gp_{place_id or abs(hash(name)) % 1000000}",
                                name=name,
                                category=item_cat,
                                address=address,
                                latitude=p_lat,
                                longitude=p_lon,
                                distance_km=dist,
                                is_certified=bool(cert_data),
                                certification_badge=badge,
                                certifications=cert_list,
                                directions_url=f"https://www.google.com/maps/dir/?api=1&destination={p_lat},{p_lon}",
                                google_maps_url=g_maps_url,
                                rating=float(rating) if rating is not None else None,
                                user_ratings_total=int(user_ratings_total) if user_ratings_total is not None else None,
                                open_now=open_now,
                                source="google_places",
                            )
                        )
        except Exception as e:
            logger.warning(f"Google Places API query failed: {e}")

        return items

    async def _search_geoapify(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        category: str,
    ) -> List[LocatorItem]:
        """Queries Geoapify Places API (100% Free tier, 3,000 requests/day, no credit card required)."""
        if not settings.GEOAPIFY_API_KEY:
            return []

        norm_cat = (category or "ALL").upper()
        if norm_cat in ["RECYCLE", "RECYCLER", "RECYCLING"]:
            categories_param = "service.recycling"
        else:
            categories_param = "service,service.recycling"

        radius_meters = int(radius_km * 1000)
        url = "https://api.geoapify.com/v2/places"
        params = {
            "categories": categories_param,
            "filter": f"circle:{longitude},{latitude},{radius_meters}",
            "bias": f"proximity:{longitude},{latitude}",
            "limit": 30,
            "apiKey": settings.GEOAPIFY_API_KEY,
        }

        items: List[LocatorItem] = []
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    features = data.get("features", [])
                    for feat in features:
                        props = feat.get("properties", {})
                        name = props.get("name") or props.get("address_line1")
                        if not name:
                            continue

                        p_lat = float(props.get("lat", latitude))
                        p_lon = float(props.get("lon", longitude))
                        dist = haversine_distance_km(latitude, longitude, p_lat, p_lon)

                        cats = props.get("categories", [])
                        name_lower = name.lower()
                        is_recycling = (
                            "waste_and_recycling" in cats
                            or "recycl" in name_lower
                            or "scrap" in name_lower
                            or "waste" in name_lower
                        )

                        cert_data = verify_facility_certification(name)
                        if is_recycling:
                            item_cat = "CERTIFIED_RECYCLER" if cert_data else "E_WASTE_COLLECTOR"
                        else:
                            item_cat = "REPAIR_SHOP"

                        if norm_cat in ["REPAIR", "REPAIR_SHOP"] and item_cat != "REPAIR_SHOP":
                            continue
                        if norm_cat in ["RECYCLE", "RECYCLER", "RECYCLING"] and item_cat not in [
                            "CERTIFIED_RECYCLER",
                            "E_WASTE_COLLECTOR",
                        ]:
                            continue

                        badge = cert_data["standard"] if cert_data else None
                        cert_list = [badge] if badge else []
                        address = (
                            props.get("formatted")
                            or f"{props.get('address_line1', '')}, {props.get('city', '')}".strip(", ")
                            or f"{dist} km from search origin"
                        )

                        contact = props.get("contact", {})
                        phone = contact.get("phone")
                        website = props.get("website") or contact.get("website")

                        items.append(
                            LocatorItem(
                                id=f"geo_{props.get('place_id') or abs(hash(name)) % 1000000}",
                                name=name,
                                category=item_cat,
                                address=address,
                                city=props.get("city"),
                                phone=phone,
                                website=website,
                                latitude=p_lat,
                                longitude=p_lon,
                                distance_km=dist,
                                is_certified=bool(cert_data),
                                certification_badge=badge,
                                certifications=cert_list,
                                directions_url=f"https://www.google.com/maps/dir/?api=1&destination={p_lat},{p_lon}",
                                google_maps_url=f"https://www.google.com/maps/dir/?api=1&destination={p_lat},{p_lon}",
                                source="geoapify",
                            )
                        )
        except Exception as e:
            logger.warning(f"Geoapify Places API query failed: {e}")

        return items

    async def _search_overpass(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        category: str,
    ) -> List[LocatorItem]:
        """Queries OpenStreetMap Overpass API using a mirror rotation strategy."""
        radius_meters = int(radius_km * 1000)
        norm_cat = (category or "ALL").upper()

        overpass_ql = f"""
        [out:json][timeout:15];
        (
          node["shop"~"electronics|computer|electronics_repair|mobile_phone"](around:{radius_meters},{latitude},{longitude});
          node["craft"="electronics_repair"](around:{radius_meters},{latitude},{longitude});
          node["amenity"~"recycling|waste_transfer_station|waste_disposal"](around:{radius_meters},{latitude},{longitude});
          way["shop"~"electronics|computer|electronics_repair|mobile_phone"](around:{radius_meters},{latitude},{longitude});
          way["craft"="electronics_repair"](around:{radius_meters},{latitude},{longitude});
          way["amenity"~"recycling|waste_transfer_station|waste_disposal"](around:{radius_meters},{latitude},{longitude});
        );
        out center 40;
        """

        items: List[LocatorItem] = []
        for mirror_url in OVERPASS_MIRRORS:
            try:
                async with httpx.AsyncClient(timeout=3.5) as client:
                    resp = await client.post(
                        mirror_url,
                        data={"data": overpass_ql},
                        headers={"User-Agent": "ReLoop-AI-CircularLocator/1.0"},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        elements = data.get("elements", [])
                        for el in elements:
                            tags = el.get("tags", {})
                            name = tags.get("name")
                            if not name:
                                continue

                            el_lat = float(el.get("lat") or el.get("center", {}).get("lat", latitude))
                            el_lon = float(el.get("lon") or el.get("center", {}).get("lon", longitude))
                            dist = haversine_distance_km(latitude, longitude, el_lat, el_lon)

                            name_lower = name.lower()
                            is_recycling = (
                                tags.get("amenity") in ["recycling", "waste_transfer_station", "waste_disposal"]
                                or tags.get("recycling:electronic_devices") == "yes"
                                or tags.get("recycling:batteries") == "yes"
                                or "recycl" in name_lower
                                or "waste" in name_lower
                                or "scrap" in name_lower
                            )

                            cert_data = verify_facility_certification(name)
                            if is_recycling:
                                item_cat = "CERTIFIED_RECYCLER" if cert_data else "E_WASTE_COLLECTOR"
                            else:
                                item_cat = "REPAIR_SHOP"

                            if norm_cat in ["REPAIR", "REPAIR_SHOP"] and item_cat != "REPAIR_SHOP":
                                continue
                            if norm_cat in ["RECYCLE", "RECYCLER", "RECYCLING"] and item_cat not in [
                                "CERTIFIED_RECYCLER",
                                "E_WASTE_COLLECTOR",
                            ]:
                                continue

                            badge = cert_data["standard"] if cert_data else None
                            cert_list = [badge] if badge else []

                            addr_parts = [
                                tags.get("addr:street"),
                                tags.get("addr:housenumber"),
                                tags.get("addr:suburb"),
                                tags.get("addr:city"),
                                tags.get("addr:postcode"),
                            ]
                            address_str = ", ".join([p for p in addr_parts if p]) or f"{dist} km from search origin"

                            items.append(
                                LocatorItem(
                                    id=f"osm_{el.get('id')}",
                                    name=name,
                                    category=item_cat,
                                    address=address_str,
                                    city=tags.get("addr:city"),
                                    phone=tags.get("phone") or tags.get("contact:phone"),
                                    website=tags.get("website") or tags.get("contact:website"),
                                    opening_hours=tags.get("opening_hours"),
                                    latitude=el_lat,
                                    longitude=el_lon,
                                    distance_km=dist,
                                    is_certified=bool(cert_data),
                                    certification_badge=badge,
                                    certifications=cert_list,
                                    directions_url=f"https://www.google.com/maps/dir/?api=1&destination={el_lat},{el_lon}",
                                    google_maps_url=f"https://www.google.com/maps/dir/?api=1&destination={el_lat},{el_lon}",
                                    source="openstreetmap",
                                )
                            )
                        # If mirror succeeded, break out
                        break
            except Exception as e:
                logger.warning(f"Overpass mirror {mirror_url} failed or timed out: {e}")
                continue

        return items

    async def search_nearby(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        query: Optional[str] = None,
        category: str = "ALL",  # "ALL", "REPAIR", "RECYCLE"
        radius_km: float = 25.0,
    ) -> LocatorSearchResult:
        resolved_name = "Custom Location"

        # Resolve coordinates from text query if lat/lon not directly provided
        if latitude is None or longitude is None:
            if not query:
                # Default to Pune, India (host city of PCCoE International Grand Challenge)
                latitude, longitude = 18.5204, 73.8567
                resolved_name = "Pune, Maharashtra, India (PCCoE Challenge Region)"
            else:
                geocoded = await self.geocode_query(query)
                if geocoded:
                    latitude, longitude, resolved_name = geocoded
                else:
                    latitude, longitude = 18.5204, 73.8567
                    resolved_name = f"{query} (Approximated)"
        elif query:
            resolved_name = query

        items: List[LocatorItem] = []
        data_source = "openstreetmap"
        google_places_configured = bool(settings.GOOGLE_MAPS_API_KEY)
        geoapify_configured = bool(settings.GEOAPIFY_API_KEY)

        # 1. Try Google Places if configured
        if google_places_configured:
            items = await self._search_google_places(latitude, longitude, radius_km, category)
            if items:
                data_source = "google_places"

        # 2. Try Geoapify Places (100% Free, no credit card) if configured and no items yet
        if not items and geoapify_configured:
            items = await self._search_geoapify(latitude, longitude, radius_km, category)
            if items:
                data_source = "geoapify"

        # 3. Fall back to OpenStreetMap Overpass (with mirror rotation) if no external items
        if not items:
            items = await self._search_overpass(latitude, longitude, radius_km, category)
            data_source = "openstreetmap"

        # Strictly enforce category filter
        norm_cat = (category or "ALL").upper()
        if norm_cat in ["REPAIR", "REPAIR_SHOP"]:
            items = [x for x in items if x.category == "REPAIR_SHOP"]
        elif norm_cat in ["RECYCLE", "RECYCLER", "RECYCLING"]:
            items = [x for x in items if x.category in ["CERTIFIED_RECYCLER", "E_WASTE_COLLECTOR"]]

        items.sort(key=lambda x: x.distance_km)
        rep_count = sum(1 for x in items if x.category == "REPAIR_SHOP")
        rec_count = sum(1 for x in items if x.category in ["CERTIFIED_RECYCLER", "E_WASTE_COLLECTOR"])

        return LocatorSearchResult(
            query_location=resolved_name,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            total_results=len(items),
            total_found=len(items),
            repair_shops_count=rep_count,
            recyclers_count=rec_count,
            data_source=data_source,
            google_places_configured=google_places_configured,
            geoapify_configured=geoapify_configured,
            results=items,
        )

    def get_certification_standards(self) -> List[CertificationStandardInfo]:
        return [
            CertificationStandardInfo(
                standard_name="SERI R2v3 (Responsible Recycling)",
                governing_body="Sustainable Electronics Recycling International (SERI)",
                description="Global gold standard for electronics refurbishing and recycling, requiring zero toxic e-waste landfill disposal, strict data sanitization, and verified downstream chain-of-custody.",
                verification_method="Third-party ANAB accredited certification audits with published SERI directory matching.",
                official_registry_url="https://sustainableelectronics.org/find-an-r2-certified-facility/",
            ),
            CertificationStandardInfo(
                standard_name="e-Stewards Standard v4.1",
                governing_body="Basel Action Network (BAN)",
                description="Strict standard prohibiting the export of toxic electronic waste from developed to developing countries, and requiring strict occupational health safeguards.",
                verification_method="Independent accredited ISO/IEC 17021 registrar auditing and tracking.",
                official_registry_url="https://e-stewards.org/find-a-recycler/",
            ),
        ]


locator_service = LocatorService()
