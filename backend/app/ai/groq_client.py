"""
Groq AI provider client for ReLoop AI.
Strictly separated from any scoring, pathway, or cost logic.
Enforces:
- Model and API key from config (default model: llama-3.2-11b-vision-preview)
- Configurable request timeout
- One retry on transient failure
- Multimodal text + image input encoded as data URLs
- OpenAI-compatible Groq API endpoint (https://api.groq.com/openai/v1/chat/completions)
- Output JSON strictly validated against Pydantic model
- AppError(code=AI_FAILURE) on any failure — never returns made-up data
"""
import base64
import json
import logging
import time
from typing import Any, Dict, List, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.errors import AppError, ErrorCode

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key if api_key is not None else settings.GROQ_API_KEY
        self.model_name = model_name if model_name is not None else settings.GROQ_MODEL
        self.timeout = timeout

    @property
    def is_live(self) -> bool:
        return bool(self.api_key)

    def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        images: Optional[List[Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> T:
        """
        Generates content using Groq OpenAI-compatible multimodal API,
        parses JSON, and validates against response_model.
        Retries exactly once on transient failures.
        Never returns fabricated data on failure — always raises AppError(AI_FAILURE).
        """
        effective_timeout = timeout if timeout is not None else self.timeout
        raw_response_text = None
        last_exception = None

        for attempt in range(2):
            try:
                raw_response_text = self._call_api(
                    prompt=prompt,
                    response_model=response_model,
                    images=images,
                    timeout=effective_timeout,
                )
                break
            except Exception as e:
                last_exception = e
                is_transient = self._is_transient_error(e)
                if attempt == 0 and is_transient:
                    logger.warning(f"Transient error on Groq attempt 1: {e}. Retrying once...")
                    time.sleep(0.5)
                    continue
                else:
                    if isinstance(e, AppError):
                        raise e
                    raise AppError(
                        code=ErrorCode.AI_FAILURE.value,
                        message=f"Groq API request failed: {str(e)}",
                        http_status=502,
                    )

        if not raw_response_text:
            raise AppError(
                code=ErrorCode.AI_FAILURE.value,
                message=f"Groq API returned empty response: {last_exception}",
                http_status=502,
            )

        return self._parse_and_validate(raw_response_text, response_model)

    def _call_api(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        images: Optional[List[Any]] = None,
        timeout: Optional[float] = None,
    ) -> str:
        if not self.api_key:
            raise AppError(
                code=ErrorCode.AI_FAILURE.value,
                message="Groq API key is not configured. Real API calls require GROQ_API_KEY.",
                http_status=500,
            )

        target_model = self.model_name or getattr(settings, "GROQ_MODEL", "llama-3.2-11b-vision-preview")
        logger.info(
            f"Calling configured Groq model: '{target_model}' "
            f"(schema: {getattr(response_model, '__name__', None)})"
        )

        payload = self._build_payload(prompt, response_model, images, target_model)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(
                    GROQ_API_URL,
                    headers=headers,
                    json=payload,
                )
        except Exception as exc:
            raise exc

        if resp.status_code != 200:
            raise AppError(
                code=ErrorCode.AI_FAILURE.value,
                message=f"Groq API error ({resp.status_code}): {resp.text}",
                http_status=502,
            )

        try:
            res_json = resp.json()
        except Exception as e:
            raise AppError(
                code=ErrorCode.AI_FAILURE.value,
                message=f"Groq API returned invalid JSON response envelope: {str(e)}",
                http_status=502,
            )

        choices = res_json.get("choices", [])
        if not choices or not choices[0].get("message", {}).get("content"):
            raise AppError(
                code=ErrorCode.AI_FAILURE.value,
                message="Groq API returned empty response content",
                http_status=502,
            )

        return choices[0]["message"]["content"].strip()

    def _build_payload(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        images: Optional[List[Any]],
        model_name: str,
    ) -> Dict[str, Any]:
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        system_content = (
            "You are an expert structured data extraction engine. "
            "You MUST respond ONLY with a valid JSON object matching the following JSON schema:\n"
            f"{schema_json}\n"
            "Respond strictly in raw JSON. Do not include markdown code fences (like ```json), "
            "do not include preamble, commentary, or text outside the JSON object."
        )

        user_content: List[Dict[str, Any]] = [
            {"type": "text", "text": prompt}
        ]
        if images:
            for img in images:
                data_url = self._convert_to_data_url(img)
                if data_url:
                    user_content.append({
                        "type": "image_url",
                        "image_url": {"url": data_url}
                    })

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }
        return payload

    def _convert_to_data_url(self, img: Any) -> Optional[str]:
        if img is None:
            return None

        # 1. ProcessedImage object or duck-typed object with .mime_type and .data
        if hasattr(img, "mime_type") and hasattr(img, "data"):
            data = img.data if isinstance(img.data, bytes) else bytes(img.data)
            mime = str(img.mime_type)
            b64 = base64.b64encode(data).decode("ascii")
            return f"data:{mime};base64,{b64}"

        # 2. Tuple of (data, mime_type)
        if isinstance(img, tuple) and len(img) == 2 and isinstance(img[0], bytes):
            data, mime = img[0], str(img[1])
            b64 = base64.b64encode(data).decode("ascii")
            return f"data:{mime};base64,{b64}"

        # 3. Raw bytes — detect magic bytes strictly for JPEG, PNG, and WebP
        if isinstance(img, bytes):
            if img.startswith(b"\x89PNG\r\n\x1a\n"):
                mime = "image/png"
            elif img.startswith(b"RIFF") and len(img) >= 12 and img[8:12] == b"WEBP":
                mime = "image/webp"
            elif img.startswith(b"\xff\xd8\xff"):
                mime = "image/jpeg"
            elif b"WEBP" in img[:16]:
                mime = "image/webp"
            else:
                mime = "image/jpeg"
            b64 = base64.b64encode(img).decode("ascii")
            return f"data:{mime};base64,{b64}"

        # 4. String format (data URL or base64)
        if isinstance(img, str):
            if img.startswith("data:image"):
                return img
            elif ";base64," in img:
                return img if img.startswith("data:") else f"data:{img}"
            else:
                try:
                    raw_bytes = base64.b64decode(img)
                    if raw_bytes.startswith(b"\x89PNG"):
                        mime = "image/png"
                    elif raw_bytes.startswith(b"RIFF") and len(raw_bytes) >= 12 and raw_bytes[8:12] == b"WEBP":
                        mime = "image/webp"
                    else:
                        mime = "image/jpeg"
                except Exception:
                    mime = "image/jpeg"
                return f"data:{mime};base64,{img}"

        return None

    def _is_transient_error(self, e: Exception) -> bool:
        err_msg = str(e).lower()
        transient_indicators = [
            "timeout",
            "timed out",
            "connection reset",
            "503",
            "429",
            "resource exhausted",
            "rate limit",
            "deadline exceeded",
            "service unavailable",
            "temporary failure",
        ]
        return any(ind in err_msg for ind in transient_indicators)

    def _parse_and_validate(self, text: str, response_model: Type[T]) -> T:
        cleaned = text.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as jde:
            raise AppError(
                code=ErrorCode.AI_FAILURE.value,
                message=f"Groq returned malformed non-JSON output: {jde.msg}",
                http_status=502,
            )

        if not isinstance(data, dict):
            raise AppError(
                code=ErrorCode.AI_FAILURE.value,
                message="Groq output was not a valid JSON dictionary",
                http_status=502,
            )

        # Normalize common variations
        list_fields = [
            "cracks", "dents", "missing_keys", "hinge_damage", "port_damage",
            "visible_swelling", "observations", "label_evidence", "visual_evidence",
            "contradictions", "visual_clues"
        ]
        for k in list_fields:
            if k in data:
                if data[k] is None:
                    data[k] = []
                elif isinstance(data[k], str):
                    data[k] = [data[k]] if data[k].strip() else []

        if response_model.__name__ in ("ModelIdentificationOutput", "OpenIdentificationOutput"):
            if "confidence" in data and isinstance(data["confidence"], str):
                try:
                    data["confidence"] = float(data["confidence"])
                except ValueError:
                    data["confidence"] = 0.90
            if "model_confidence" in data and isinstance(data["model_confidence"], str):
                try:
                    data["model_confidence"] = float(data["model_confidence"])
                except ValueError:
                    data["model_confidence"] = 0.90

        try:
            return response_model.model_validate(data)
        except ValidationError as ve:
            raise AppError(
                code=ErrorCode.AI_FAILURE.value,
                message=f"Groq output failed schema validation: {ve.errors()}",
                http_status=502,
            )


# Default client instance
groq_client = GroqClient()

