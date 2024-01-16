from typing import Any, Dict, List, Literal, Optional

from pydantic import Field

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings


class OllamaRequestSettings(AIRequestSettings):
    ai_model_id: str = Field("", alias="model")
    format: Optional[Literal["json"]] = None
    options: Optional[Dict[str, Any]] = None
    stream: bool = False


class OllamaTextRequestSettings(OllamaRequestSettings):
    prompt: Optional[str] = None
    context: Optional[str] = None
    system: Optional[str] = None
    template: Optional[str] = None
    raw: bool = False


class OllamaChatRequestSettings(OllamaRequestSettings):
    messages: Optional[List[Dict[str, str]]] = None
