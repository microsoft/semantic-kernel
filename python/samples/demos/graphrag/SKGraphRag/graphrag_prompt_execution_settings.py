# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Literal

from semantic_kernel.connectors.ai import PromptExecutionSettings

logger = logging.getLogger(__name__)


class GraphRagPromptExecutionSettings(PromptExecutionSettings):
    """
    GraphRagPromptExecutionSettings is a class that inherits from PromptExecutionSettings
    and is used to configure the execution settings for a GraphRag prompt.

    Attributes:
        response_type: Specifies the type of response expected from the prompt. Default is "Multiple Paragraphs".
            Valid values for this can be found in the GraphRag doc.
            This value is used in a prompt to determine the format of the response, so has no fixed values.
        search_type: Specifies the type of search to be performed.
            - "global": see https://github.com/microsoft/graphrag/blob/main/docs/query/global_search.md
            - "local": see https://github.com/microsoft/graphrag/blob/main/docs/query/local_search.md
            - "drift": see https://github.com/microsoft/graphrag/blob/main/docs/query/drift_search.md
          Default is "global".
          Drift is not available for streaming completions.
    """

    response_type: str = "Multiple Paragraphs"
    search_type: Literal["local", "global", "drift"] = "global"
