"""
Prompt loader for ReLoop AI.
Loads versioned prompt templates from the prompts directory and tracks prompt version provenance.
"""
from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel
from app.errors import AppError, ErrorCode

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


class LoadedPrompt(BaseModel):
    name: str
    version: str
    content: str
    file_path: str

    def format(self, **kwargs) -> str:
        """
        Formats prompt template with provided kwargs.
        Preserves JSON example braces without escaping issues.
        """
        text = self.content
        for key, val in kwargs.items():
            placeholder = f"{{{key}}}"
            text = text.replace(placeholder, str(val))
        return text


def load_prompt(name: str, version: str = "v1") -> LoadedPrompt:
    """
    Loads prompt template file named {name}_{version}.txt and records the version used.
    """
    filename = f"{name}_{version}.txt"
    filepath = PROMPTS_DIR / filename

    if not filepath.exists():
        raise AppError(
            code=ErrorCode.AI_FAILURE.value,
            message=f"Versioned prompt template '{filename}' not found in {PROMPTS_DIR}",
            http_status=500,
        )

    try:
        content = filepath.read_text(encoding="utf-8")
        return LoadedPrompt(
            name=name,
            version=version,
            content=content,
            file_path=str(filepath),
        )
    except Exception as e:
        raise AppError(
            code=ErrorCode.AI_FAILURE.value,
            message=f"Failed to read prompt template '{filename}': {str(e)}",
            http_status=500,
        )
