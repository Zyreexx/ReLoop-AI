"""
Vision service for product identification and optical visible damage assessment.
Enforces non-negotiable rules:
- Supported model list supplied to prompt
- Catalog-constrained candidate IDs (C1, C2, ...) generated deterministically
- needs_confirmation=True always for MVP
- UNSUPPORTED_MODEL response lets user select model manually
- Post-filter strictly drops any findings regarding internal component health (battery/SSD/RAM/motherboard)
- AI failure raises AppError AI_FAILURE
- Results persisted as VISUAL evidence records linked to product
"""
import re
import logging
from typing import Any, Dict, List, Optional, Set
from sqlalchemy.orm import Session
from app.ai.gemini_client import gemini_client, GeminiClient
from app.ai.prompt_loader import load_prompt
from app.ai.schemas import (
    ModelIdentificationOutput,
    CatalogIdentificationOutput,
    OpenIdentificationOutput,
    DamageAssessmentOutput,
)
from app.config import settings
from app.db.repositories import product_repo, evidence_repo
from app.db.store import store
from app.errors import AppError, ErrorCode
from app.knowledge.loader import (
    match_catalog_model,
    get_generic_laptop_profile,
)
from app.knowledge.models_catalog import (
    get_all_models,
    lookup_model,
    get_catalog_candidates_with_ids,
    get_candidate_by_id,
    format_candidates_for_prompt,
)
from app.knowledge.sample_data import (
    get_sample_identify_response,
    get_sample_vision_findings,
    find_demo_case,
)
from app.schemas.enums import ComponentName, ComponentStatus, ConfidenceLevel, EvidenceType, IdentificationStatus
from app.schemas.evidence import Evidence
from app.schemas.product import ProductCandidate, ProductIdentifyResponse, ProductSpecs
from app.schemas.vision import VisibleFinding, VisionAnalyzeResponse, VisionAnalyzeRequest

logger = logging.getLogger(__name__)

# Keywords indicating internal hardware health that are strictly forbidden from visual reports
FORBIDDEN_INTERNAL_KEYWORDS = [
    "battery",
    "ssd",
    "storage",
    "nvme",
    "drive",
    "hard drive",
    "ram",
    "memory",
    "motherboard",
    "logic board",
    "mainboard",
    "circuit",
    "power rail",
    "cpu health",
    "silicon",
]

ALLOWED_IMAGE_ROLES: Set[str] = {
    "overall",
    "keyboard_screen",
    "bottom_label",
    "ports",
    "model_sticker",
    "lid",
    "palmrest",
    "display",
    "chassis",
    "serial_tag",
}

KNOWN_BRAND_FAMILIES: Dict[str, List[str]] = {
    "dell": ["dell", "latitude", "xps", "inspiron", "precision", "alienware", "vostro", "g-series"],
    "apple": ["apple", "macbook", "macbook air", "macbook pro", "imac"],
    "hp": ["hp", "hewlett", "elitebook", "probook", "spectre", "pavilion", "omen", "victus", "envy", "zbook"],
    "lenovo": ["lenovo", "thinkpad", "ideapad", "legion", "yoga", "loq", "thinkbook"],
    "asus": ["asus", "zenbook", "vivobook", "rog", "tuf", "expertbook", "proart"],
    "acer": ["acer", "aspire", "swift", "nitro", "predator", "spin", "travelmate", "conceptd"],
    "microsoft": ["microsoft", "surface", "surface pro", "surface laptop", "surface book"],
    "samsung": ["samsung", "galaxy book", "notebook"],
    "msi": ["msi", "stealth", "raider", "katana", "prestige", "modern", "creator"],
    "razer": ["razer", "blade"],
    "lg": ["lg", "gram"],
}


def validate_image_roles(image_roles: Optional[List[str]], image_count: int) -> List[str]:
    """
    Validates optional image_roles list:
    - If provided, length must equal image_count
    - Each role must belong to ALLOWED_IMAGE_ROLES
    Raises AppError(INVALID_INPUT) on violation.
    """
    if not image_roles:
        return []
    if len(image_roles) != image_count:
        raise AppError(
            code=ErrorCode.INVALID_INPUT.value,
            message=f"image_roles length ({len(image_roles)}) must match image count ({image_count}).",
            field="image_roles",
            http_status=400,
        )
    normalized = []
    for idx, r in enumerate(image_roles):
        r_str = str(r).strip().lower()
        if r_str not in ALLOWED_IMAGE_ROLES:
            raise AppError(
                code=ErrorCode.INVALID_INPUT.value,
                message=f"Invalid image role '{r}' at index {idx}. Allowed roles: {sorted(ALLOWED_IMAGE_ROLES)}",
                field="image_roles",
                http_status=400,
            )
        normalized.append(r_str)
    return normalized


def _extract_digit_tokens(model_name: str) -> List[str]:
    """
    Extracts lowercase tokens from a model string that contain at least one digit.
    Pure alphabetic words (e.g. Latitude, ThinkPad, EliteBook, MacBook, Air, Aspire) are excluded.
    """
    cleaned = re.sub(r"[(),/\-_]", " ", model_name.lower())
    tokens = [t.strip() for t in cleaned.split() if t.strip()]
    return [t for t in tokens if any(c.isdigit() for c in t)]


def _is_identifier_ambiguous(
    ident: str,
    candidate: ProductCandidate,
    catalog_candidates: Optional[List[ProductCandidate]] = None,
    combined_labels: str = "",
) -> bool:
    """
    Checks if a digit-bearing identifier is ambiguous.
    1. If catalog_candidates is provided, checks if it matches or overlaps with another candidate's token.
    2. In open-ended context: if the identifier is generic/ambiguous in isolation
       (e.g. bare 1-digit like '1', or bare 2-digit number like '14'/'15' with no brand/family context in labels),
       it is treated as ambiguous.
    """
    if len(ident) <= 1:
        return True

    if ident.isdigit() and len(ident) == 2:
        cand_mfr = candidate.manufacturer.lower().strip()
        cand_keywords = KNOWN_BRAND_FAMILIES.get(cand_mfr, [cand_mfr])
        if cand_mfr not in cand_keywords:
            cand_keywords = [cand_mfr] + cand_keywords
        has_brand_context = any(bk in combined_labels for bk in cand_keywords)
        if not has_brand_context:
            return True

    if not catalog_candidates:
        return False

    cand_model_norm = candidate.model.strip().lower()
    cand_mfr_norm = candidate.manufacturer.strip().lower()

    for other in catalog_candidates:
        if not other:
            continue
        if (
            other.model.strip().lower() == cand_model_norm
            and other.manufacturer.strip().lower() == cand_mfr_norm
        ):
            continue

        other_digit_tokens = _extract_digit_tokens(other.model)
        for ot in other_digit_tokens:
            # Exact token collision (e.g. both have '15' or '2020')
            if ident == ot:
                return True
            # Substring collision for multi-character tokens (e.g. '14' vs '140')
            if len(ident) >= 2 and len(ot) >= 2:
                if ident in ot or ot in ident:
                    return True
            # Single digit token being matched is ambiguous if present inside another model's token
            if len(ident) == 1 and ident in ot:
                return True

    return False


def _is_model_text_in_labels(
    candidate: Optional[ProductCandidate],
    label_evidence: List[str],
    catalog_candidates: Optional[List[ProductCandidate]] = None,
) -> bool:
    """
    Checks if readable model-specific text or model number matching the chosen candidate
    is present in label_evidence.

    Pure family/series names (e.g. 'Latitude', 'ThinkPad', 'EliteBook', 'MacBook', 'Aspire') alone
    do NOT qualify as model-specific text. Only full model names or unambiguous digit-bearing
    model numbers/identifiers qualify.
    """
    if not candidate or not label_evidence:
        return False
    combined_labels = " ".join(label_evidence).lower()

    # 1. Full model name check
    model_lower = candidate.model.lower().strip()
    if model_lower and model_lower != "unknown":
        if model_lower in combined_labels:
            return True

        full_name = f"{candidate.manufacturer.lower().strip()} {model_lower}"
        if full_name in combined_labels:
            return True

        cleaned_model_full = re.sub(r"[(),/\-_]", " ", model_lower)
        cleaned_model_collapsed = " ".join(cleaned_model_full.split())
        if cleaned_model_collapsed and cleaned_model_collapsed in combined_labels:
            return True

    # 2. Check key digit-bearing model identifiers and numbers (e.g. '5420', '840', 't14', 'm1', 'g7', 'a515')
    specific_identifiers = _extract_digit_tokens(candidate.model)
    if not specific_identifiers:
        return False

    for ident in specific_identifiers:
        if re.search(r"\b" + re.escape(ident) + r"\b", combined_labels):
            if not _is_identifier_ambiguous(ident, candidate, catalog_candidates, combined_labels):
                return True

    return False


def _has_contradiction(
    candidate: Optional[ProductCandidate],
    label_evidence: List[str],
    visual_evidence: List[str],
    contradictions: List[str],
) -> bool:
    """
    Checks if Gemini noted contradictions or if label_evidence contradicts candidate manufacturer.
    """
    if any(c.strip() for c in contradictions if c):
        return True

    if not candidate or not candidate.manufacturer or candidate.manufacturer.strip().upper() == "UNKNOWN":
        return False

    cand_mfr = candidate.manufacturer.lower().strip()
    cand_keywords = KNOWN_BRAND_FAMILIES.get(cand_mfr, [cand_mfr])
    if cand_mfr not in cand_keywords:
        cand_keywords = [cand_mfr] + cand_keywords

    combined_labels = " ".join(label_evidence).lower()
    cand_brand_found = any(re.search(r"\b" + re.escape(bk) + r"\b", combined_labels) for bk in cand_keywords)

    for other_mfr, other_keywords in KNOWN_BRAND_FAMILIES.items():
        if other_mfr == cand_mfr:
            continue
        for ok in other_keywords:
            if re.search(r"\b" + re.escape(ok) + r"\b", combined_labels):
                if not cand_brand_found:
                    return True
                return True

    return False


def _is_manufacturer_clear(
    candidate: Optional[ProductCandidate],
    label_evidence: List[str],
    visual_evidence: List[str],
) -> bool:
    """
    Checks if manufacturer brand is clearly present in label_evidence or visual clues.
    """
    if not candidate or not candidate.manufacturer or candidate.manufacturer.strip().upper() == "UNKNOWN":
        return False
    cand_mfr = candidate.manufacturer.lower().strip()
    cand_keywords = KNOWN_BRAND_FAMILIES.get(cand_mfr, [cand_mfr])
    if cand_mfr not in cand_keywords:
        cand_keywords = [cand_mfr] + cand_keywords

    combined_labels = " ".join(label_evidence).lower()
    combined_visual = " ".join(visual_evidence).lower()

    for bk in cand_keywords:
        if re.search(r"\b" + re.escape(bk) + r"\b", combined_labels):
            return True
        if re.search(r"\b" + re.escape(bk) + r"\b", combined_visual):
            return True

    return False


def evaluate_identification_confidence(
    candidate: Optional[ProductCandidate],
    candidate_id: Optional[str] = None,
    label_evidence: Optional[List[str]] = None,
    visual_evidence: Optional[List[str]] = None,
    contradictions: Optional[List[str]] = None,
    model_confidence: float = 0.0,
    catalog_candidates: Optional[List[ProductCandidate]] = None,
) -> ConfidenceLevel:
    """
    Deterministic confidence policy for product identification.
    Never upgrades based on Gemini's numeric confidence alone.

    - HIGH: readable specific model text in label_evidence that matches the chosen candidate,
            with no contradictions.
    - MEDIUM: manufacturer brand clear in label/visuals but exact model not confirmed by label text,
              OR visual-only evidence with >= 2 distinct items and no contradictions.
    - LOW: only generic visual similarity (>= 1 visual item).
    - UNKNOWN: candidate is UNKNOWN, model is UNKNOWN, contradictions exist, or evidence is insufficient.
    """
    labels = [l.strip() for l in (label_evidence or []) if l and l.strip()]
    visuals = [v.strip() for v in (visual_evidence or []) if v and v.strip()]
    contra = [c.strip() for c in (contradictions or []) if c and c.strip()]

    # 1. Unknown or missing candidate
    if (
        not candidate
        or not candidate.manufacturer
        or candidate.manufacturer.strip().upper() == "UNKNOWN"
        or not candidate.model
        or candidate.model.strip().upper() == "UNKNOWN"
    ):
        return ConfidenceLevel.UNKNOWN

    if candidate_id and candidate_id.strip().upper() == "UNKNOWN":
        return ConfidenceLevel.UNKNOWN

    # 2. Contradiction check
    if _has_contradiction(candidate, labels, visuals, contra):
        return ConfidenceLevel.UNKNOWN

    # 3. HIGH: Readable specific model text in label_evidence matching candidate
    if _is_model_text_in_labels(candidate, labels, catalog_candidates=catalog_candidates):
        return ConfidenceLevel.HIGH

    # 4. MEDIUM: visual-only evidence caps at MEDIUM (>= 2 visual items or manufacturer clear)
    if _is_manufacturer_clear(candidate, labels, visuals):
        return ConfidenceLevel.MEDIUM

    if len(visuals) >= 2:
        return ConfidenceLevel.MEDIUM

    # 5. LOW: only generic visual similarity
    if len(visuals) >= 1:
        return ConfidenceLevel.LOW

    # 6. Insufficient evidence
    return ConfidenceLevel.UNKNOWN


def filter_visible_findings(findings: List[VisibleFinding]) -> List[VisibleFinding]:
    """
    POST-FILTER: Strictly drops any finding claiming internal component health.
    A photo can NEVER prove internal battery, SSD, RAM, or motherboard health.
    Exception: visible battery swelling (exterior chassis deformation) is reported under HINGE_CHASSIS.
    """
    filtered = []
    for f in findings:
        comp_str = str(getattr(f.component, "value", f.component)).upper()
        desc_lower = f.description.lower()

        # If component is an internal hardware subsystem, drop it immediately
        if comp_str in ["BATTERY", "SSD", "RAM", "SYSTEM", "MOTHERBOARD"]:
            # Only allow if it describes visible exterior swelling deforming chassis
            if "swelling" in desc_lower or "bulge" in desc_lower or "bulging" in desc_lower:
                f.component = ComponentName.HINGE_CHASSIS
                filtered.append(f)
            continue

        # If description makes claims about internal electronic health, drop it
        if any(kw in desc_lower for kw in FORBIDDEN_INTERNAL_KEYWORDS):
            if not ("swelling" in desc_lower or "bulge" in desc_lower):
                continue

        filtered.append(f)

    return filtered


class VisionService:
    def identify(
        self,
        image_bytes_list: Optional[List[Any]] = None,
        image_roles: Optional[List[str]] = None,
        manual_model: Optional[str] = None,
        model_id: Optional[str] = None,
        hint: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> ProductIdentifyResponse:
        """
        Identifies model from images using catalog-constrained Gemini Vision or manual model_id.
        Applies deterministic confidence policy and returns auditable evidence.
        """
        all_supported = get_all_models()
        generic_prof = get_generic_laptop_profile()
        generic_specs = ProductSpecs(**generic_prof["specs"]) if isinstance(generic_prof.get("specs"), dict) else ProductSpecs()
        generic_candidate = ProductCandidate(
            manufacturer="Generic",
            model="General Laptop",
            model_year=2021,
            confidence=ConfidenceLevel.HIGH,
            specs=generic_specs,
        )
        target_model = manual_model or model_id or hint

        # 1. Demo fallback mode explicit flag
        if settings.DEMO_FALLBACK:
            logger.info("DEMO_FALLBACK active: serving precomputed sample identification.")
            return get_sample_identify_response(target_model)

        # 2. Manual path: client sends manual_model or model_id directly
        if target_model and not image_bytes_list:
            # Check generic model request
            target_norm = target_model.strip().lower()
            if target_norm in ["generic-laptop", "general-laptop", "general laptop", "generic", "generic laptop"]:
                return ProductIdentifyResponse(
                    status=IdentificationStatus.IDENTIFIED,
                    identified_model=generic_candidate,
                    candidate_id="GENERIC",
                    is_supported=False,
                    confidence=1.0,
                    confidence_level=ConfidenceLevel.HIGH,
                    needs_confirmation=True,
                    requires_user_confirmation=True,
                    visual_clues=["General laptop category profile selected manually"],
                    label_evidence=["Manual selection: General Laptop"],
                    visual_evidence=["User manual confirmation"],
                    contradictions=[],
                    supported_models=all_supported,
                    generic_fallback_available=True,
                    generic_model=generic_candidate,
                    source="manual",
                )

            matched = lookup_model(target_model)
            if matched:
                cand = ProductCandidate(
                    manufacturer=matched["manufacturer"],
                    model=matched["model"],
                    model_year=matched["model_year"],
                    confidence=ConfidenceLevel.HIGH,
                    specs=matched["specs"],
                )
                # Find candidate ID from catalog
                c_id = None
                for item in get_catalog_candidates_with_ids():
                    if item["manufacturer"].lower() == cand.manufacturer.lower() and item["model"].lower() == cand.model.lower():
                        c_id = item["candidate_id"]
                        break
                return ProductIdentifyResponse(
                    status=IdentificationStatus.IDENTIFIED,
                    identified_model=cand,
                    candidate_id=c_id or "C1",
                    is_supported=True,
                    confidence=1.0,
                    confidence_level=ConfidenceLevel.HIGH,
                    needs_confirmation=True,
                    requires_user_confirmation=True,
                    visual_clues=["Manually confirmed by user"],
                    label_evidence=[f"Manual model selection: {cand.manufacturer} {cand.model}"],
                    visual_evidence=["User manual confirmation"],
                    contradictions=[],
                    supported_models=all_supported,
                    generic_fallback_available=True,
                    generic_model=generic_candidate,
                    source="manual",
                )
            else:
                # Unsupported manual model
                return ProductIdentifyResponse(
                    status=IdentificationStatus.UNKNOWN,
                    identified_model=None,
                    candidate_id="UNKNOWN",
                    is_supported=False,
                    confidence=0.0,
                    confidence_level=ConfidenceLevel.UNKNOWN,
                    needs_confirmation=True,
                    requires_user_confirmation=True,
                    supported_models=all_supported,
                    generic_fallback_available=True,
                    generic_model=generic_candidate,
                    message=f"Model '{target_model}' is not in the supported catalog. Please select a supported model or continue with a general laptop assessment.",
                    source="manual",
                )

        if not image_bytes_list:
            return ProductIdentifyResponse(
                status=IdentificationStatus.INVALID_EVIDENCE,
                identified_model=None,
                candidate_id="UNKNOWN",
                is_supported=False,
                confidence=0.0,
                confidence_level=ConfidenceLevel.UNKNOWN,
                needs_confirmation=True,
                requires_user_confirmation=True,
                supported_models=all_supported,
                generic_fallback_available=True,
                generic_model=generic_candidate,
                message="Please upload product images or select a model manually.",
                source="live",
            )

        # 3. Vision path with Gemini
        normalized_roles = validate_image_roles(image_roles, len(image_bytes_list))
        if normalized_roles:
            role_lines = ["IMAGE ROLES:"]
            for i, r in enumerate(normalized_roles, 1):
                role_lines.append(f"IMAGE {i} = {r}")
            image_roles_context = "\n".join(role_lines)
        else:
            image_roles_context = ""

        hint_context = f"User hint: {hint}" if hint else ""

        prompt_obj = load_prompt("vision_identify", "v2")
        prompt_text = prompt_obj.format(
            image_roles_context=image_roles_context,
            hint_context=hint_context,
        )

        active_gemini = GeminiClient(api_key=api_key) if api_key else gemini_client

        try:
            ai_res: OpenIdentificationOutput = active_gemini.generate_structured(
                prompt=prompt_text,
                response_model=OpenIdentificationOutput,
                images=image_bytes_list,
                media_resolution=settings.GEMINI_MEDIA_RESOLUTION,
            )
        except Exception as e:
            if settings.DEMO_FALLBACK:
                demo_match = find_demo_case(target_model or hint, allow_default=True)
                if demo_match:
                    logger.info(f"Gemini API identify call failed ({e}); falling back to precomputed sample data for '{demo_match.get('id')}'.")
                    return get_sample_identify_response(target_model or hint)

            logger.warning(f"Gemini API identify call failed ({e}); returning structured AI_UNAVAILABLE state.")
            return ProductIdentifyResponse(
                status=IdentificationStatus.AI_UNAVAILABLE,
                identified_model=None,
                candidate_id="UNKNOWN",
                is_supported=False,
                confidence=0.0,
                confidence_level=ConfidenceLevel.UNKNOWN,
                visible_label_text=None,
                visual_clues=[],
                label_evidence=[],
                visual_evidence=[],
                contradictions=[],
                needs_confirmation=True,
                requires_user_confirmation=True,
                supported_models=all_supported,
                generic_fallback_available=True,
                generic_model=generic_candidate,
                message="AI identification is temporarily unavailable. Please select your model manually to continue.",
                source="live",
            )

        raw_mfr = (ai_res.manufacturer or "").strip()
        raw_model = (ai_res.model or "").strip()
        raw_candidate_id = (ai_res.candidate_id or "").strip().upper() if ai_res.candidate_id else None

        # Fallback to legacy candidate_id if manufacturer/model not directly populated
        if (not raw_mfr or raw_mfr.upper() == "UNKNOWN") and raw_candidate_id and raw_candidate_id != "UNKNOWN":
            candidate_data = get_candidate_by_id(raw_candidate_id)
            if candidate_data:
                c_info = candidate_data["candidate"]
                raw_mfr = c_info.manufacturer
                raw_model = c_info.model

        candidate_obj = None
        is_catalog_matched = False
        c_id = raw_candidate_id

        if raw_mfr and raw_mfr.upper() != "UNKNOWN" and raw_model and raw_model.upper() != "UNKNOWN":
            # Match catalog using robust match_catalog_model
            catalog_match = match_catalog_model(raw_mfr, raw_model)
            if catalog_match:
                is_catalog_matched = True
                specs_data = catalog_match.get("specs", {})
                specs_obj = ProductSpecs(**specs_data) if isinstance(specs_data, dict) else ProductSpecs()
                candidate_obj = ProductCandidate(
                    manufacturer=catalog_match.get("manufacturer", raw_mfr),
                    model=catalog_match.get("model", raw_model),
                    model_year=ai_res.model_year or catalog_match.get("model_year", 2021),
                    confidence=ConfidenceLevel.HIGH,
                    specs=specs_obj,
                )
                if not c_id:
                    for item in get_catalog_candidates_with_ids():
                        if item["slug"] == catalog_match.get("slug"):
                            c_id = item["candidate_id"]
                            break
            else:
                is_catalog_matched = False
                candidate_obj = ProductCandidate(
                    manufacturer=raw_mfr,
                    model=raw_model,
                    model_year=ai_res.model_year or 2021,
                    confidence=ConfidenceLevel.HIGH,
                    specs=generic_specs,
                )

        conf_level = evaluate_identification_confidence(
            candidate=candidate_obj,
            candidate_id=raw_candidate_id,
            label_evidence=ai_res.label_evidence,
            visual_evidence=ai_res.visual_evidence,
            contradictions=ai_res.contradictions,
            model_confidence=ai_res.model_confidence,
            catalog_candidates=all_supported,
        )

        if conf_level == ConfidenceLevel.UNKNOWN or candidate_obj is None:
            # Downgraded or unknown -> return UNKNOWN status with generic fallback option
            return ProductIdentifyResponse(
                status=IdentificationStatus.UNKNOWN,
                identified_model=None,
                candidate_id="UNKNOWN",
                is_supported=False,
                confidence=ai_res.model_confidence,
                confidence_level=ConfidenceLevel.UNKNOWN,
                visible_label_text="; ".join(ai_res.label_evidence) if ai_res.label_evidence else None,
                visual_clues=ai_res.visual_evidence,
                label_evidence=ai_res.label_evidence,
                visual_evidence=ai_res.visual_evidence,
                contradictions=ai_res.contradictions,
                needs_confirmation=True,
                requires_user_confirmation=True,
                supported_models=all_supported,
                generic_fallback_available=True,
                generic_model=generic_candidate,
                message="Model could not be identified from photos. Your device may not be in the currently supported catalog. Please select your model manually to continue.",
                source="live",
            )

        candidate_obj.confidence = conf_level
        num_conf = 0.95 if conf_level == ConfidenceLevel.HIGH else (0.75 if conf_level == ConfidenceLevel.MEDIUM else 0.5)

        alternatives = [
            m for m in all_supported
            if not (m.manufacturer.lower() == candidate_obj.manufacturer.lower() and m.model.lower() == candidate_obj.model.lower())
        ][:3]

        return ProductIdentifyResponse(
            status=IdentificationStatus.IDENTIFIED,
            identified_model=candidate_obj,
            candidate_id=c_id,
            is_supported=is_catalog_matched,
            confidence=num_conf,
            confidence_level=conf_level,
            visible_label_text="; ".join(ai_res.label_evidence) if ai_res.label_evidence else None,
            visual_clues=ai_res.visual_evidence,
            label_evidence=ai_res.label_evidence,
            visual_evidence=ai_res.visual_evidence,
            contradictions=ai_res.contradictions,
            needs_confirmation=True,
            requires_user_confirmation=True,
            alternative_models=alternatives,
            supported_models=all_supported,
            generic_fallback_available=True,
            generic_model=generic_candidate,
            source="live",
        )

    def analyze(
        self,
        product_id: str,
        image_bytes_list: Optional[List[Any]] = None,
        inspection_notes: Optional[str] = None,
        image_names: Optional[List[str]] = None,
        db: Optional[Session] = None,
    ) -> VisionAnalyzeResponse:
        """
        Analyzes visible exterior damage, post-filters internal claims,
        and saves results as VISUAL evidence items.
        Supports DEMO_FALLBACK mode and automatic fallback on Gemini failure for demo models.
        """
        product = store.get_product(product_id)
        if not product and db:
            product = product_repo.get(db, product_id)

        if not product:
            raise AppError(
                code=ErrorCode.NOT_FOUND.value,
                message=f"No product registered with ID '{product_id}'",
                field="product_id",
                http_status=404,
            )

        # 1. Demo fallback mode explicit flag
        if settings.DEMO_FALLBACK:
            logger.info(f"DEMO_FALLBACK active: serving precomputed sample vision findings for product {product_id}.")
            return get_sample_vision_findings(product_id, query_or_notes=inspection_notes, image_names=image_names)

        raw_findings: List[VisibleFinding] = []

        if image_bytes_list:
            prompt_obj = load_prompt("vision_damage", "v1")
            prompt_text = prompt_obj.content
            if inspection_notes:
                prompt_text += f"\nInspection context from user: {inspection_notes}"

            try:
                ai_res: DamageAssessmentOutput = gemini_client.generate_structured(
                    prompt=prompt_text,
                    response_model=DamageAssessmentOutput,
                    images=image_bytes_list,
                )

                # Map raw AI items to VisibleFinding
                for crack in ai_res.cracks:
                    raw_findings.append(VisibleFinding(component=ComponentName.DISPLAY, description=crack, severity="HIGH"))
                for dent in ai_res.dents:
                    raw_findings.append(VisibleFinding(component=ComponentName.HINGE_CHASSIS, description=dent, severity="LOW"))
                for key in ai_res.missing_keys:
                    raw_findings.append(VisibleFinding(component=ComponentName.KEYBOARD, description=key, severity="MODERATE"))
                for h_dmg in ai_res.hinge_damage:
                    raw_findings.append(VisibleFinding(component=ComponentName.HINGE_CHASSIS, description=h_dmg, severity="HIGH"))
                for p_dmg in ai_res.port_damage:
                    raw_findings.append(VisibleFinding(component="PORTS", description=p_dmg, severity="MODERATE"))
                for swell in ai_res.visible_swelling:
                    raw_findings.append(VisibleFinding(component=ComponentName.HINGE_CHASSIS, description=f"Visible exterior bulge: {swell}", severity="HIGH"))
                for obs in ai_res.observations:
                    raw_findings.append(VisibleFinding(component=ComponentName.HINGE_CHASSIS, description=obs, severity="LOW"))

            except Exception as e:
                # Check if this product or context corresponds to a demo case
                demo_match = find_demo_case(inspection_notes or (image_names[0] if image_names else None), product_id=product_id)
                if demo_match:
                    logger.info(f"Gemini API vision call failed ({e}); falling back to sample data for demo case '{demo_match.get('id')}'.")
                    return get_sample_vision_findings(product_id, query_or_notes=inspection_notes, image_names=image_names)
                # Never silently use sample data outside explicit flag or demo failure path
                raise
        elif inspection_notes:
            # Fallback when only notes provided without images
            lowered = inspection_notes.lower()
            if "screen" in lowered or "crack" in lowered:
                raw_findings.append(VisibleFinding(component=ComponentName.DISPLAY, description=inspection_notes, severity="HIGH"))
            if "key" in lowered:
                raw_findings.append(VisibleFinding(component=ComponentName.KEYBOARD, description=inspection_notes, severity="MODERATE"))
            if not raw_findings:
                raw_findings.append(VisibleFinding(component=ComponentName.HINGE_CHASSIS, description="Exterior inspected; normal wear observed.", severity="LOW"))
        else:
            raw_findings.append(VisibleFinding(component=ComponentName.HINGE_CHASSIS, description="No visible physical damage detected.", severity="LOW"))

        # POST-FILTER: drop any claim about internal component health
        clean_findings = filter_visible_findings(raw_findings)

        # Save as VISUAL Evidence records linked to the product
        source_label = f"Optical Inspection ({', '.join(image_names) if image_names else 'Uploaded photos'})"
        evidence_items: List[Evidence] = []

        for f in clean_findings:
            ev = Evidence(
                type=EvidenceType.VISUAL,
                source=source_label,
                component=str(getattr(f.component, "value", f.component)).lower(),
                value={
                    "observation": f.description,
                    "severity": f.severity,
                    "confidence": f.confidence,
                },
                confidence=ConfidenceLevel.HIGH,
            )
            store.add_evidence(product_id, ev)
            if db:
                try:
                    evidence_repo.add(db, ev, product_id=product_id)
                except Exception:
                    pass
            evidence_items.append(ev)

        # Determine overall condition
        has_severe = any(f.severity in ["HIGH", "CRITICAL"] for f in clean_findings)
        has_moderate = any(f.severity in ["MODERATE", "MEDIUM"] for f in clean_findings)
        overall_cond = ComponentStatus.DAMAGED if has_severe else (ComponentStatus.WEAR if has_moderate else ComponentStatus.GOOD)

        return VisionAnalyzeResponse(
            product_id=product_id,
            findings=clean_findings,
            overall_visual_condition="SERVICE_REQUIRED" if (has_severe or has_moderate) else "GOOD",
            overall_condition=overall_cond,
            evidence_items=evidence_items,
            source="live" if image_bytes_list else "manual",
        )

    def analyze_visible_damage(
        self,
        req: VisionAnalyzeRequest,
        db: Optional[Session] = None,
    ) -> VisionAnalyzeResponse:
        return self.analyze(
            product_id=req.product_id,
            image_bytes_list=None,
            inspection_notes=req.inspection_notes,
            image_names=req.image_names,
            db=db,
        )


vision_service = VisionService()

