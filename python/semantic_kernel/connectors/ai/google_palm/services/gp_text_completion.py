# Copyright (c) Microsoft. All rights reserved.

import logging
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from typing import Annotated

=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
from typing import Annotated

=======
<<<<<<< Updated upstream
=======
<<<<<<< main
from typing import Annotated

=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
import sys
from typing import List

from semantic_kernel.contents.text_content import TextContent

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
import google.generativeai as palm
from google.generativeai.types import Completion
from google.generativeai.types.text_types import TextCompletion
from pydantic import StringConstraints, ValidationError

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from semantic_kernel.connectors.ai.google_palm.gp_prompt_execution_settings import GooglePalmTextPromptExecutionSettings
from semantic_kernel.connectors.ai.google_palm.settings.google_palm_settings import GooglePalmSettings
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
from semantic_kernel.connectors.ai.google_palm.gp_prompt_execution_settings import GooglePalmTextPromptExecutionSettings
from semantic_kernel.connectors.ai.google_palm.settings.google_palm_settings import GooglePalmSettings
=======
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
<<<<<<< main
from semantic_kernel.connectors.ai.google_palm.gp_prompt_execution_settings import GooglePalmTextPromptExecutionSettings
from semantic_kernel.connectors.ai.google_palm.settings.google_palm_settings import GooglePalmSettings
=======
from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.google_palm.gp_prompt_execution_settings import (
    GooglePalmTextPromptExecutionSettings,
)
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions import ServiceInitializationError, ServiceResponseException
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream

logger: logging.Logger = logging.getLogger(__name__)

=======

logger: logging.Logger = logging.getLogger(__name__)
>>>>>>> origin/main

class GooglePalmTextCompletion(TextCompletionClientBase):
    api_key: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

<<<<<<< head
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======

logger: logging.Logger = logging.getLogger(__name__)
>>>>>>> origin/main

logger: logging.Logger = logging.getLogger(__name__)

<<<<<<< main

class GooglePalmTextCompletion(TextCompletionClientBase):
    api_key: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

=======
class GooglePalmTextCompletion(TextCompletionClientBase):
    api_key: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
class GooglePalmTextCompletion(TextCompletionClientBase):
    api_key: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

<<<<<<< main
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    def __init__(
        self,
        ai_model_id: str,
        api_key: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ):
        """Initializes a new instance of the GooglePalmTextCompletion class.
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main

        Args:
            ai_model_id (str): GooglePalm model name, see
                https://developers.generativeai.google/models/language
            api_key (str | None): The optional API key to use. If not provided, will be
                read from either the env vars or the .env settings file.
            env_file_path (str | None): Use the environment settings file as a
                fallback to environment variables. (Optional)
            env_file_encoding (str | None): The encoding of the environment settings file. (Optional)

        Raises:
            ServiceInitializationError: When the Google Palm settings cannot be read.
        """
        try:
            google_palm_settings = GooglePalmSettings.create(
                api_key=api_key,
                text_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Google Palm settings.", ex) from ex
        if not google_palm_settings.text_model_id:
            raise ServiceInitializationError("The Google Palm text model ID is required.")

=======
=======
<<<<<<< Updated upstream
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
    def __init__(self, ai_model_id: str, api_key: str):
        """
        Initializes a new instance of the GooglePalmTextCompletion class.
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

        Args:
            ai_model_id (str): GooglePalm model name, see
                https://developers.generativeai.google/models/language
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
            api_key (str | None): The optional API key to use. If not provided, will be
                read from either the env vars or the .env settings file.
            env_file_path (str | None): Use the environment settings file as a
                fallback to environment variables. (Optional)
            env_file_encoding (str | None): The encoding of the environment settings file. (Optional)

        Raises:
            ServiceInitializationError: When the Google Palm settings cannot be read.
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
            api_key {str} -- GooglePalm API key, see
                https://developers.generativeai.google/products/palm
        """
        super().__init__(ai_model_id=ai_model_id, api_key=api_key)

    async def complete(self, prompt: str, settings: GooglePalmTextPromptExecutionSettings) -> List[TextContent]:
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        """
        try:
            google_palm_settings = GooglePalmSettings.create(
                api_key=api_key,
                text_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Google Palm settings.", ex) from ex
        if not google_palm_settings.text_model_id:
            raise ServiceInitializationError("The Google Palm text model ID is required.")

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
        super().__init__(
            ai_model_id=google_palm_settings.text_model_id,
            api_key=google_palm_settings.api_key.get_secret_value() if google_palm_settings.api_key else None,
        )

    async def get_text_contents(
        self, prompt: str, settings: GooglePalmTextPromptExecutionSettings
    ) -> list[TextContent]:
        """This is the method that is called from the kernel to get a response from a text-optimized LLM.

        Args:
            prompt (str): The prompt to send to the LLM.
            settings (GooglePalmTextPromptExecutionSettings): Settings for the request.

        Returns:
            List[TextContent]: A list of TextContent objects representing the response(s) from the LLM.
        """
        settings.prompt = prompt
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        try:
            palm.configure(api_key=self.api_key)
        except Exception as ex:
            raise PermissionError(
                "Google PaLM service failed to configure. Invalid API key provided.",
                ex,
            )
        try:
            response = palm.generate_text(**settings.prepare_settings_dict())
        except Exception as ex:
            raise ServiceResponseException(
                "Google PaLM service failed to complete the prompt",
                ex,
            ) from ex
        return [self._create_text_content(response, candidate) for candidate in response.candidates]

    def _create_text_content(self, response: Completion, candidate: TextCompletion) -> TextContent:
        """Create a text content object from a candidate."""
        return TextContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            text=candidate.get("output"),
            metadata={
                "filters": response.filters,
                "safety_feedback": response.safety_feedback,
                "citation_metadata": candidate.get("citation_metadata"),
                "safety_ratings": candidate.get("safety_ratings"),
            },
        )

    async def get_streaming_text_contents(
        self,
        prompt: str,
        settings: GooglePalmTextPromptExecutionSettings,
    ):
        """Get streaming text contents from the Google Palm API, unsupported.

        Raises:
            NotImplementedError: Google Palm API does not currently support streaming.

        """
        raise NotImplementedError("Google Palm API does not currently support streaming")

    def get_prompt_execution_settings_class(self) -> "PromptExecutionSettings":
        """Create a request settings object."""
        return GooglePalmTextPromptExecutionSettings
