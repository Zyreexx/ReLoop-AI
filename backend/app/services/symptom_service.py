"""
Symptom service for parsing, categorizing, and tracking user-reported hardware observations.
Preserves USER_REPORTED evidence provenance.
"""
from typing import List
from app.ai.gemini_client import gemini_client
from app.db.store import store
from app.schemas.enums import EvidenceType, ConfidenceLevel
from app.schemas.evidence import EvidenceItem
from app.schemas.symptoms import (
    SymptomInput,
    SymptomParseResult,
    ParsedSymptomItem,
)


class SymptomService:
    def parse_and_record(self, data: SymptomInput) -> SymptomParseResult:
        product_id = data.product_id or "default"
        try:
            parsed_items_raw = gemini_client.parse_symptoms(
                symptoms=data.selected_symptoms,
                notes=data.user_notes,
            )
        except Exception as e:
            # Deterministic fallback when Gemini API is unreachable or fails
            text = " ".join(data.selected_symptoms) + " " + (data.user_notes or "")
            lowered = text.lower()
            parsed_items_raw = []
            if any(w in lowered for w in ["battery", "drain", "charge"]):
                parsed_items_raw.append({"component": "battery", "symptom": "Rapid discharge", "severity": "MODERATE", "user_statement": "Battery drains quickly"})
            if any(w in lowered for w in ["fan", "loud", "heat", "hot", "thermal"]):
                parsed_items_raw.append({"component": "thermals", "symptom": "Audible fans / elevated heat", "severity": "MODERATE", "user_statement": "Elevated thermals / loud fans"})
            if not parsed_items_raw:
                parsed_items_raw.append({"component": "system", "symptom": "Lifecycle check", "severity": "LOW", "user_statement": "General operational check"})

        parsed_items: List[ParsedSymptomItem] = []
        evidence_items: List[EvidenceItem] = []

        for item in parsed_items_raw:
            parsed_obj = ParsedSymptomItem(
                component=item.get("component", "system"),
                symptom=item.get("symptom", "Reported operational behavior"),
                severity=item.get("severity", "MODERATE"),
                user_statement=item.get("user_statement", ""),
            )
            parsed_items.append(parsed_obj)

            ev = EvidenceItem(
                type=EvidenceType.USER_REPORTED,
                source="User Diagnostic Questionnaire",
                component=parsed_obj.component,
                value={
                    "symptom": parsed_obj.symptom,
                    "severity": parsed_obj.severity,
                    "user_statement": parsed_obj.user_statement,
                    "intended_use": data.intended_use,
                },
                confidence=ConfidenceLevel.HIGH,
            )
            store.add_evidence(product_id, ev)
            evidence_items.append(ev)

        return SymptomParseResult(
            parsed_symptoms=parsed_items,
            evidence_items=evidence_items,
            intended_use=data.intended_use or "daily_office_and_web",
        )


symptom_service = SymptomService()
