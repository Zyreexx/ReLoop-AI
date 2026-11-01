"""
Next-Life Engine Prompt Loader.
"""
from app.ai.prompt_loader import load_prompt


def get_next_life_prompt(version: str = "v1") -> str:
    prompt = load_prompt("next_life", version)
    return prompt.content
