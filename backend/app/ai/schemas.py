"""
Pydantic schemas for structured AI outputs from Gemini.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ModelIdentificationOutput(BaseModel):
    model_name: str = Field(..., description="Exact matched model name or 'unknown'")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    visible_label_text: Optional[str] = Field(None, description="Directly read text from stickers/chassis")
    visual_clues: List[str] = Field(default_factory=list, description="Visual characteristics observed")


class OpenIdentificationOutput(BaseModel):
    is_laptop: bool = Field(True, description="True if the device is a laptop/notebook computer. False if it is a smartphone, tablet, standalone monitor, desktop PC, or other non-laptop.")
    detected_device_type: str = Field("LAPTOP", description="'LAPTOP', 'SMARTPHONE', 'TABLET', 'MONITOR', 'DESKTOP', 'OTHER_NON_LAPTOP', or 'UNKNOWN'")
    manufacturer: str = Field("UNKNOWN", description="Identified laptop manufacturer (e.g. Dell, Lenovo, Apple, HP, Acer, ASUS) or 'UNKNOWN'")
    model: str = Field("UNKNOWN", description="Identified laptop model line and number (e.g. Latitude 5420, Aspire 5 A515-56, ThinkPad T14 Gen 1) or 'UNKNOWN'")
    model_year: Optional[int] = Field(None, description="Estimated release model year if discernible")
    label_evidence: List[str] = Field(default_factory=list, description="Text literally read from logos, badges, and labels")
    visual_evidence: List[str] = Field(default_factory=list, description="Observed visual features and design clues")
    contradictions: List[str] = Field(default_factory=list, description="Visual contradictions or mismatching indicators")
    model_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Advisory raw model confidence score")
    candidate_id: Optional[str] = Field(None, description="Optional legacy candidate ID or 'UNKNOWN'")
    display_cracks: List[str] = Field(default_factory=list, description="Directly visible display glass hairline cracks, panel fractures, shattered glass, or deep screen scratches observed in the photos")
    keyboard_faults: List[str] = Field(default_factory=list, description="Missing keycaps, loose keys, detached scissor switches, or broken keys observed in the photos")
    port_faults: List[str] = Field(default_factory=list, description="Damaged charging ports (USB-C/barrel/MagSafe), bent pins, broken tongues, debris blockage, or cracked port bezels observed in the photos")
    chassis_faults: List[str] = Field(default_factory=list, description="Structural casing cracks, corner casing splits, deep dents, hinge damage, or visible battery bulge observed in the photos")
    components_inspected_clean: List[str] = Field(default_factory=list, description="Components from ['display', 'keyboard', 'ports', 'chassis'] that are clearly visible in the photos with NO physical defects")
    components_not_assessable: List[str] = Field(default_factory=list, description="Components from ['display', 'keyboard', 'ports', 'chassis'] that are not clearly visible or too blurry in the provided photos")


# Backwards compatibility alias
CatalogIdentificationOutput = OpenIdentificationOutput


class DamageAssessmentOutput(BaseModel):
    display_cracks: List[str] = Field(default_factory=list, description="Directly visible display glass hairline cracks, panel damage, or deep screen scratches")
    chassis_cracks: List[str] = Field(default_factory=list, description="Directly visible structural fractures or cracks on the casing, chassis corners, bottom plate, or palmrest")
    cracks: List[str] = Field(default_factory=list, description="General or legacy crack observations")
    dents: List[str] = Field(default_factory=list, description="Metal/plastic lid or bottom casing dents and depressions")
    missing_keys: List[str] = Field(default_factory=list, description="Missing keycaps, loose scissor switches, or broken stabilizers")
    hinge_damage: List[str] = Field(default_factory=list, description="Misaligned hinges, cracked hinge caps, resistance damage")
    port_damage: List[str] = Field(default_factory=list, description="Bent pins, broken tongues, debris blockage, cracked port bezels")
    visible_swelling: List[str] = Field(default_factory=list, description="Visible exterior battery bulge displacing trackpad or separating casing seams")
    observations: List[str] = Field(default_factory=list, description="Factual visual observations (cosmetic scuffs, discoloration, sticker residue)")
    components_inspected_clean: List[str] = Field(default_factory=list, description="Components clearly visible in photos with NO obvious damage observed ('display', 'keyboard', 'chassis', 'ports')")
    components_not_assessable: List[str] = Field(default_factory=list, description="Components that are not visible or too blurry to assess reliably ('display', 'keyboard', 'chassis', 'ports')")


class SymptomClassificationOutput(BaseModel):
    matched_symptom_tags: List[str] = Field(default_factory=list)
    user_summary: Optional[str] = None


class ExplanationOutput(BaseModel):
    summary: str = Field(..., description="Executive narrative summary of the circular recommendation")
    details: List[str] = Field(default_factory=list, description="Supporting bullet points grounded in verified evidence")
    assumptions: List[str] = Field(default_factory=list, description="Explicit notes of key assumptions")
