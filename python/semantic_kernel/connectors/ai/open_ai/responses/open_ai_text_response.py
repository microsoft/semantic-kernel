# Copyright (c) Microsoft. All rights reserved.


from openai.types import Completion

from semantic_kernel.models.contents import TextContent


class OpenAITextContent(TextContent):
    """A text completion response from OpenAI.

    For streaming responses, make sure to async loop through parse_stream before trying anything else.
    Once that is done:
    - content: get the content of first choice of the response.
    - all_content: get the content of all choices of the response.
    - parse_stream: get the streaming content of the response.
    """

    inner_content: Completion
