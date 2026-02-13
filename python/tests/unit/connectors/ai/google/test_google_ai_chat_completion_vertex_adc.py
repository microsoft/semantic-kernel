from semantic_kernel.connectors.ai.google.google_ai.google_ai_settings import GoogleAISettings
from semantic_kernel.connectors.ai.google.google_ai.services.google_ai_chat_completion import (
    GoogleAIChatCompletion,
)
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


def test_vertexai_does_not_require_api_key_when_adc_is_used():
    """
    When use_vertexai=True, GoogleAIChatCompletion should NOT require an API key,
    because authentication is handled via Application Default Credentials (ADC).
    """

    GoogleAIChatCompletion(
        gemini_model_id="models/gemini-1.5-pro",
        api_key=None,
        use_vertexai=True,
        project_id="test-project",
        region="us-central1",
    )
