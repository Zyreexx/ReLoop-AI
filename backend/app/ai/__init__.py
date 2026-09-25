"""
AI Provider Layer for ReLoop AI.
Strictly separated from any scoring, pathway, or cost logic.
"""
from app.ai.gemini_client import GeminiClient, gemini_client
from app.ai.prompt_loader import LoadedPrompt, load_prompt
from app.ai.schemas import (
    ModelIdentificationOutput,
    DamageAssessmentOutput,
    SymptomClassificationOutput,
)

__all__ = [
    "GeminiClient",
    "gemini_client",
    "LoadedPrompt",
    "load_prompt",
    "ModelIdentificationOutput",
    "DamageAssessmentOutput",
    "SymptomClassificationOutput",
]
