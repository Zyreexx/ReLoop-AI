"""
Precomputed sample data manager for demo cases and fallback mode.
Loads fixtures from data/demo/*.json and provides labeled sample-data artifacts.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.errors import AppError, ErrorCode
from app.knowledge.loader import get_demo_data_dir
from app.knowledge.models_catalog import get_all_models, lookup_model
from app.schemas.enums import ComponentName, ComponentStatus, ConfidenceLevel, EvidenceType, IdentificationStatus
from app.schemas.evidence import Evidence
from app.schemas.product import ProductCandidate, ProductIdentifyResponse, ProductSpecs
from app.schemas.vision import VisibleFinding, VisionAnalyzeResponse

logger = logging.getLogger(__name__)

_DEMO_CASES_CACHE: Optional[Dict[str, dict]] = None


def load_demo_cases() -> Dict[str, dict]:
    """
    Loads all demo JSON cases from data/demo/*.json.
    Keyed by demo ID (e.g. 'demo-01-healthy', 'demo-02-repairable', etc.).
    """
    global _DEMO_CASES_CACHE
    if _DEMO_CASES_CACHE is not None:
        return _DEMO_CASES_CACHE

    demo_dir = get_demo_data_dir()
    cache: Dict[str, dict] = {}

    if demo_dir.exists():
        for f in sorted(demo_dir.glob("*.json")):
            try:
                with open(f, "r", encoding="utf-8") as jf:
                    data = json.load(jf)
                    case_id = data.get("id") or f.stem
                    cache[case_id] = data
            except Exception as e:
                logger.error(f"Error loading demo file {f}: {e}")

    _DEMO_CASES_CACHE = cache
    return _DEMO_CASES_CACHE


def find_demo_case(
    query_or_hint: Optional[str] = None,
    product_id: Optional[str] = None,
    allow_default: bool = False,
) -> Optional[dict]:
    """
    Matches query, hint, or product_id to one of the 4 demo cases.
    Explicitly ignores unsupported model families (e.g. victus, loq, legion, etc.).
    If allow_default is False and no match is found, returns None.
    """
    cases = load_demo_cases()
    if not cases:
        return None

    # 1. Check exact ID or product_id mapping
    if product_id:
        pid_clean = product_id.replace("prod_", "").replace("_", "-")
        for cid, case in cases.items():
            if cid in product_id or cid == pid_clean:
                return case

    text = (query_or_hint or "").lower()
    pid_text = (product_id or "").lower()
    combined = f"{text} {pid_text}".strip()

    if not combined:
        if allow_default:
            return cases.get("demo-01-healthy") or next(iter(cases.values()), None)
        return None

    # Guard: if the text mentions unsupported lines, do NOT match a supported demo case
    unsupported_signals = ["victus", "loq", "legion", "omen", "pavilion", "ideapad", "yoga", "inspiron", "vostro", "xps", "alienware", "zenbook", "aspire"]
    if any(un in combined for un in unsupported_signals):
        return None

    # 2. Check liquid / recovery / component recovery signals
    if any(w in combined for w in ["demo-04", "demo_04", "recovery", "liquid spill", "corrosion"]):
        return cases.get("demo-04-recovery") or cases.get("demo_04_component_recovery")

    # 3. Check borderline / 840 / HP EliteBook signals
    if any(w in combined for w in ["demo-03", "demo_03", "elitebook", "840 g7", "840g7", "borderline"]):
        return cases.get("demo-03-borderline")

    # 4. Check repairable / latitude / 5420 / Dell Latitude signals
    if any(w in combined for w in ["demo-02", "demo_02", "latitude 5420", "latitude5420", "repairable"]):
        return cases.get("demo-02-repairable")

    # 5. Check healthy / thinkpad / t14 / Lenovo ThinkPad signals
    if any(w in combined for w in ["demo-01", "demo_01", "thinkpad t14", "thinkpad", "t14 gen 1", "t14"]):
        return cases.get("demo-01-healthy")

    # 6. Check MacBook Air M1 signals
    if any(w in combined for w in ["macbook air", "macbook air m1", "a2337", "m1 air"]):
        for cid, case in cases.items():
            prod_mod = case.get("product", {}).get("model", "").lower()
            if "macbook air" in prod_mod:
                return case

    # Fallback to exact matching model name in demo cases
    for cid, case in cases.items():
        prod_mfg = case.get("product", {}).get("manufacturer", "").lower()
        prod_mod = case.get("product", {}).get("model", "").lower()
        full_name = f"{prod_mfg} {prod_mod}".strip()
        if full_name and full_name in combined:
            return case

    if allow_default:
        return cases.get("demo-01-healthy") or next(iter(cases.values()), None)

    return None


def get_sample_identify_response(query_or_hint: Optional[str] = None) -> ProductIdentifyResponse:
    """
    Returns ProductIdentifyResponse built from precomputed sample data.
    Clearly marked with visual clue labeling source: 'sample-data'.
    Never silently defaults to Dell Latitude 5420 or catalog[0] when demo case is not found.
    """
    demo_case = find_demo_case(query_or_hint)
    all_supported = get_all_models()

    if not demo_case:
        return ProductIdentifyResponse(
            status=IdentificationStatus.UNKNOWN,
            identified_model=None,
            candidate_id="UNKNOWN",
            is_supported=False,
            confidence=0.0,
            confidence_level=ConfidenceLevel.UNKNOWN,
            visible_label_text=None,
            visual_clues=["No matching demo case profile found."],
            label_evidence=[],
            visual_evidence=[],
            contradictions=[],
            needs_confirmation=True,
            requires_user_confirmation=True,
            supported_models=all_supported,
            message="Model could not be identified from demo sample data. Please select your device model manually.",
            source="sample-data",
        )

    prod_info = demo_case["product"]
    catalog_match = lookup_model(f"{prod_info['manufacturer']} {prod_info['model']}")
    specs = catalog_match["specs"] if catalog_match else ProductSpecs(**prod_info.get("specs", {}))
    candidate = ProductCandidate(
        manufacturer=prod_info["manufacturer"],
        model=prod_info["model"],
        model_year=prod_info.get("model_year", 2021),
        confidence=ConfidenceLevel.HIGH,
        specs=specs,
    )

    alternatives = [
        m for m in all_supported
        if not (m.manufacturer == candidate.manufacturer and m.model == candidate.model)
    ][:3]

    # Find candidate_id if available
    cand_id = None
    try:
        from app.knowledge.models_catalog import get_catalog_candidates_with_ids
        for c in get_catalog_candidates_with_ids():
            if c["manufacturer"].lower() == candidate.manufacturer.lower() and c["model"].lower() == candidate.model.lower():
                cand_id = c["candidate_id"]
                break
    except Exception:
        cand_id = None

    return ProductIdentifyResponse(
        status=IdentificationStatus.IDENTIFIED,
        identified_model=candidate,
        candidate_id=cand_id or "C1",
        is_supported=True,
        confidence=0.95,
        confidence_level=ConfidenceLevel.HIGH,
        visible_label_text=f"[Sample Data] {candidate.manufacturer} {candidate.model}",
        visual_clues=["Precomputed demo sample profile (source: sample-data)"],
        label_evidence=[f"[Sample Data] {candidate.manufacturer} {candidate.model} asset label"],
        visual_evidence=["Reference demo photo profile (source: sample-data)"],
        contradictions=[],
        needs_confirmation=True,
        requires_user_confirmation=True,
        alternative_models=alternatives,
        supported_models=all_supported,
        source="sample-data",
    )


def get_sample_vision_findings(
    product_id: str,
    query_or_notes: Optional[str] = None,
    image_names: Optional[List[str]] = None,
) -> VisionAnalyzeResponse:
    """
    Returns VisionAnalyzeResponse built from precomputed sample data.
    Creates Evidence items strictly labeled with source: 'sample-data'.
    """
    demo_case = find_demo_case(query_or_notes or (image_names[0] if image_names else None), product_id=product_id)
    raw_damages = []
    cosmetic_grade = "B"

    if demo_case and "vision_findings" in demo_case:
        vf = demo_case["vision_findings"]
        raw_damages = vf.get("visible_damages", [])
        cosmetic_grade = vf.get("cosmetic_grade", "B")

    clean_findings: List[VisibleFinding] = []
    for dmg in raw_damages:
        comp_raw = dmg.get("component", "chassis").upper()
        comp_enum = ComponentName(comp_raw) if comp_raw in ComponentName._value2member_map_ else ComponentName.HINGE_CHASSIS
        clean_findings.append(
            VisibleFinding(
                component=comp_enum,
                description=dmg.get("description", "Visible damage inspected"),
                severity=dmg.get("severity", "LOW").upper(),
                confidence=0.9,
            )
        )

    if not clean_findings:
        clean_findings.append(
            VisibleFinding(
                component=ComponentName.HINGE_CHASSIS,
                description="Sample inspection baseline; normal chassis wear.",
                severity="LOW",
                confidence=0.85,
            )
        )

    # Save evidence items with source='sample-data'
    evidence_items: List[Evidence] = []
    from app.db.store import store

    for f in clean_findings:
        ev = Evidence(
            type=EvidenceType.VISUAL,
            source="sample-data",
            component=str(getattr(f.component, "value", f.component)).lower(),
            value={
                "observation": f.description,
                "severity": f.severity,
                "confidence": f.confidence,
                "cosmetic_grade": cosmetic_grade,
                "basis": "assumption",
                "source": "sample-data",
            },
            confidence=ConfidenceLevel.HIGH,
        )
        store.add_evidence(product_id, ev)
        evidence_items.append(ev)

    has_severe = any(f.severity in ["HIGH", "CRITICAL"] for f in clean_findings)
    has_moderate = any(f.severity in ["MODERATE", "MEDIUM"] for f in clean_findings)
    overall_cond = ComponentStatus.DAMAGED if has_severe else (ComponentStatus.WEAR if has_moderate else ComponentStatus.GOOD)

    return VisionAnalyzeResponse(
        product_id=product_id,
        findings=clean_findings,
        overall_visual_condition="SERVICE_REQUIRED" if (has_severe or has_moderate) else "GOOD",
        overall_condition=overall_cond,
        evidence_items=evidence_items,
        source="sample-data",
    )
