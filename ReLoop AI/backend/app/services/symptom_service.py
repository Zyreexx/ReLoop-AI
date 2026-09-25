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
        parsed_items_raw = gemini_client.parse_symptoms(
            symptoms=data.selected_symptoms,
            notes=data.user_notes,
        )

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
