# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.connectors.ai.voyage_ai.voyage_ai_settings import VoyageAISettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase


class VoyageAIBase(AIServiceClientBase):
    """Base class for VoyageAI services."""

    def __init__(
        self,
        ai_model_id: str,
        service_id: str | None = None,
        api_key: str | None = None,
        client: Any | None = None,
        aclient: Any | None = None,
        env_file_path: str | None = None,
        endpoint: str | None = None,
        max_retries: int | None = None,
    ):
        """Initialize VoyageAI base service.

        Args:
            ai_model_id: The VoyageAI model ID.
            service_id: The service ID (optional, defaults to ai_model_id).
            api_key: The VoyageAI API key (optional, will use env var if not provided).
            client: A pre-configured VoyageAI client (optional).
            aclient: A pre-configured VoyageAI async client (optional).
            env_file_path: Path to .env file (optional).
            endpoint: VoyageAI API endpoint (optional).
            max_retries: Maximum number of retries for API calls (optional, defaults to 3).
        """
        # Load settings from environment if not provided
        try:
            voyage_settings = VoyageAISettings.create(
                api_key=api_key,
                env_file_path=env_file_path,
            )
        except Exception as e:
            raise ServiceInitializationError(f"Failed to load VoyageAI settings: {e}") from e

        super().__init__(
            ai_model_id=ai_model_id,
            service_id=service_id or ai_model_id,
        )

        # Store settings values as private attributes to avoid Pydantic validation
        self._voyage_settings = voyage_settings
        self._endpoint = endpoint or voyage_settings.endpoint
        self._max_retries = max_retries if max_retries is not None else voyage_settings.max_retries
        self._aclient = aclient or self._create_async_client(voyage_settings)

    @property
    def aclient(self):
        """Get the VoyageAI async client."""
        return self._aclient

    @property
    def endpoint(self):
        """Get the API endpoint."""
        return self._endpoint

    def _create_async_client(self, settings: VoyageAISettings):
        """Create VoyageAI async client.

        Args:
            settings: VoyageAI settings.

        Returns:
            VoyageAI async client instance.
        """
        try:
            import voyageai
        except ImportError as e:
            raise ServiceInitializationError(
                "The voyageai package is required to use VoyageAI services. "
                "Please install it with: pip install voyageai"
            ) from e

        return voyageai.AsyncClient(
            api_key=settings.api_key.get_secret_value(),
            max_retries=self._max_retries,
        )

    def service_url(self) -> str | None:
        """Get the service URL."""
        return self.endpoint
