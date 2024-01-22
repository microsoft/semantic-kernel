# Copyright (c) Microsoft. All rights reserved.


from openai.types import Completion

from semantic_kernel.models.contents import TextContent


class OpenAITextContent(TextContent):
    """This is the class for OpenAI text response content.

    Used by both OpenAI and Azure OpenAI Text Completion services.

    Args:
        inner_content: Completion - The inner content of the response,
            this should hold all the information from the response so even
            when not creating a subclass a developer can leverage the full thing.
        ai_model_id: Optional[str] - The id of the AI model that generated this response.
        metadata: Dict[str, Any] - Any metadata that should be attached to the response.
        text: Optional[str] - The text of the response.
        encoding: Optional[str] - The encoding of the text.

    Methods:
        __str__: Returns the text of the response.
    """

    inner_content: Completion
