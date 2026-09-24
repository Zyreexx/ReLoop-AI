"""
Unit tests for AI provider layer with mocked Gemini calls.
Tests:
- Valid JSON parsing into Pydantic model
- Malformed JSON raises AppError AI_FAILURE
- Schema validation mismatch raises AppError AI_FAILURE
- Timeout / transient failure retry and eventual AI_FAILURE
- Multimodal image input handling
- Versioned prompt loading and provenance tracking
- Absence of scoring, pathway, or cost logic
"""
import inspect
from unittest.mock import MagicMock, patch
import pytest

from app.ai.gemini_client import GeminiClient
from app.ai.prompt_loader import load_prompt, LoadedPrompt
from app.ai.schemas import (
    ModelIdentificationOutput,
    DamageAssessmentOutput,
    SymptomClassificationOutput,
)
from app.errors import AppError, ErrorCode


# --- 1. Versioned Prompt Loader Tests ---

def test_prompt_loader_identify():
    prompt = load_prompt("vision_identify", version="v1")
    assert prompt.name == "vision_identify"
    assert prompt.version == "v1"
    assert "{supported_models}" in prompt.content

    formatted = prompt.format(supported_models="- Dell Latitude 5420\n- ThinkPad T490")
    assert "Dell Latitude 5420" in formatted
    assert "ThinkPad T490" in formatted
    assert "choose only from this supported model list" in formatted.lower()


def test_prompt_loader_damage():
    prompt = load_prompt("vision_damage", version="v1")
    assert prompt.name == "vision_damage"
    assert prompt.version == "v1"
    assert "cracks" in prompt.content
    assert "missing_keys" in prompt.content
    assert "port_damage" in prompt.content
    assert "internal component health" in prompt.content


def test_prompt_loader_symptoms():
    prompt = load_prompt("symptoms", version="v1")
    assert prompt.name == "symptoms"
    assert prompt.version == "v1"
    assert "BATTERY_DRAIN_FAST" in prompt.content
    assert "DO NOT DIAGNOSE" in prompt.content

    formatted = prompt.format(user_text="Laptop dies in 30 minutes and gets hot")
    assert "Laptop dies in 30 minutes and gets hot" in formatted


def test_prompt_loader_missing_file_raises_ai_failure():
    with pytest.raises(AppError) as exc_info:
        load_prompt("nonexistent_prompt", version="v99")
    assert exc_info.value.code == ErrorCode.AI_FAILURE.value
    assert "not found" in exc_info.value.message


# --- 2. Mocked Gemini SDK Tests ---

@pytest.fixture
def mock_gemini_client():
    client = GeminiClient(api_key="mock_test_key", model_name="gemini-2.5-flash", timeout=5.0)
    return client


def test_valid_json_returns_validated_pydantic_model(mock_gemini_client):
    mock_response = MagicMock()
    mock_response.text = '{"model_name": "Dell Latitude 5420", "confidence": 0.95, "visible_label_text": "Dell Latitude 5420 Regulatory Model P137G", "visual_clues": ["Dell logo", "Thunderbolt 4"]}'

    with patch.object(mock_gemini_client, "_call_sdk", return_value=mock_response.text):
        result = mock_gemini_client.generate_structured(
            prompt="Identify this laptop",
            response_model=ModelIdentificationOutput,
        )

    assert isinstance(result, ModelIdentificationOutput)
    assert result.model_name == "Dell Latitude 5420"
    assert result.confidence == 0.95
    assert result.visible_label_text == "Dell Latitude 5420 Regulatory Model P137G"
    assert len(result.visual_clues) == 2


def test_valid_json_wrapped_in_markdown_codeblock(mock_gemini_client):
    mock_response_text = """```json
    {
      "cracks": [],
      "dents": ["Minor bottom cover depression"],
      "missing_keys": ["W keycap missing"],
      "hinge_damage": [],
      "port_damage": [],
      "visible_swelling": [],
      "observations": ["Normal cosmetic wear"]
    }
    ```"""

    with patch.object(mock_gemini_client, "_call_sdk", return_value=mock_response_text):
        result = mock_gemini_client.generate_structured(
            prompt="Analyze damage",
            response_model=DamageAssessmentOutput,
        )

    assert isinstance(result, DamageAssessmentOutput)
    assert result.missing_keys == ["W keycap missing"]
    assert result.dents == ["Minor bottom cover depression"]
    assert result.cracks == []


def test_malformed_json_raises_ai_failure(mock_gemini_client):
    """
    CRITICAL RULE:
    Malformed JSON must raise AppError AI_FAILURE.
    Must never return made-up data on failure.
    """
    broken_response = "I think the laptop is Dell Latitude 5420 {broken json"

    with patch.object(mock_gemini_client, "_call_sdk", return_value=broken_response):
        with pytest.raises(AppError) as exc_info:
            mock_gemini_client.generate_structured(
                prompt="Identify this laptop",
                response_model=ModelIdentificationOutput,
            )

    err = exc_info.value
    assert err.code == ErrorCode.AI_FAILURE.value
    assert "malformed" in err.message.lower() or "json" in err.message.lower()
    assert err.http_status == 502


def test_schema_mismatch_raises_ai_failure(mock_gemini_client):
    """
    Valid JSON that does not match required Pydantic schema must raise AI_FAILURE.
    """
    wrong_schema_json = '{"unrelated_field": 12345}'

    with patch.object(mock_gemini_client, "_call_sdk", return_value=wrong_schema_json):
        with pytest.raises(AppError) as exc_info:
            mock_gemini_client.generate_structured(
                prompt="Identify this laptop",
                response_model=ModelIdentificationOutput,
            )

    err = exc_info.value
    assert err.code == ErrorCode.AI_FAILURE.value
    assert "validation" in err.message.lower() or "schema" in err.message.lower()


def test_timeout_retries_once_then_succeeds(mock_gemini_client):
    """
    Transient timeout on attempt 1 triggers retry; attempt 2 succeeds.
    """
    call_count = 0

    def mock_call_sdk(contents, timeout):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise TimeoutError("Deadline exceeded: connection timed out")
        return '{"matched_symptom_tags": ["BATTERY_DRAIN_FAST"], "user_summary": "Battery drains quickly"}'

    with patch.object(mock_gemini_client, "_call_sdk", side_effect=mock_call_sdk):
        result = mock_gemini_client.generate_structured(
            prompt="Parse symptoms",
            response_model=SymptomClassificationOutput,
        )

    assert call_count == 2
    assert isinstance(result, SymptomClassificationOutput)
    assert result.matched_symptom_tags == ["BATTERY_DRAIN_FAST"]


def test_timeout_exhausted_raises_ai_failure(mock_gemini_client):
    """
    When timeout occurs on both attempts, client raises AppError AI_FAILURE.
    """
    call_count = 0

    def mock_call_sdk(contents, timeout):
        nonlocal call_count
        call_count += 1
        raise TimeoutError("Deadline exceeded: request timed out")

    with patch.object(mock_gemini_client, "_call_sdk", side_effect=mock_call_sdk):
        with pytest.raises(AppError) as exc_info:
            mock_gemini_client.generate_structured(
                prompt="Parse symptoms",
                response_model=SymptomClassificationOutput,
            )

    assert call_count == 2
    assert exc_info.value.code == ErrorCode.AI_FAILURE.value
    assert "timed out" in exc_info.value.message.lower() or "failed" in exc_info.value.message.lower()


def test_unconfigured_api_key_raises_ai_failure():
    unconfigured_client = GeminiClient(api_key="")
    with pytest.raises(AppError) as exc_info:
        unconfigured_client.generate_structured(
            prompt="Hello",
            response_model=ModelIdentificationOutput,
        )
    assert exc_info.value.code == ErrorCode.AI_FAILURE.value
    assert "GEMINI_API_KEY" in exc_info.value.message


def test_multimodal_image_input_building(mock_gemini_client):
    fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    contents = mock_gemini_client._build_contents("Check image", [fake_png])

    assert len(contents) == 2
    assert contents[0] == "Check image"
    assert hasattr(contents[1], "inline_data") or hasattr(contents[1], "mime_type") or contents[1] is not None


def test_ai_layer_has_no_scoring_or_optimizer_logic():
    """
    NON-NEGOTIABLE RULE:
    AI provider layer is strictly separated from any scoring, pathway, or cost logic.
    """
    import app.ai.prompt_loader as prompt_mod

    for obj in [GeminiClient, prompt_mod]:
        src = inspect.getsource(obj)
        assert "optimizer" not in src.lower(), f"{obj} references optimizer"
        assert "score_pathways" not in src, f"{obj} references score_pathways"
        assert "scoring" not in src.lower(), f"{obj} references scoring"
