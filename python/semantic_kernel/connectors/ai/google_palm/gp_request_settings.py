from typing import Any, Dict, Optional

from google.generativeai.types import ExampleOptions, MessagePromptOptions

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings


class GooglePalmRequestSettings(AIRequestSettings):
    max_tokens: int = 256
    temperature: float = 0.0
    top_p: float = 1.0
    candidate_count: int = 1
    stop_sequences: Any = None
    token_selection_biases: Dict[int, int] = {}
    examples: Optional[ExampleOptions] = None
    context: Optional[str] = None
    prompt: Optional[MessagePromptOptions] = None

    def prepare_settings_dict(self, **kwargs) -> Dict[str, Any]:
        settings = self.model_dump(
            exclude={"service_id", "extension_data"},
            exclude_unset=True,
            exclude_none=True,
            by_alias=True,
        )
        if kwargs.get("model", False):
            settings["model"] = kwargs["model"]
        if kwargs.get("context", False):
            settings["context"] = kwargs["context"]
        if kwargs.get("messages", False):
            settings["messages"] = kwargs["messages"][-1][1]
        return settings
