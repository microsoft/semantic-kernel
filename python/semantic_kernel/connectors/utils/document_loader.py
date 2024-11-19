# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import Awaitable, Callable
from inspect import isawaitable

from httpx import AsyncClient, HTTPStatusError, RequestError

from semantic_kernel.exceptions import ServiceInvalidRequestError
from semantic_kernel.utils.telemetry.user_agent import HTTP_USER_AGENT

logger: logging.Logger = logging.getLogger(__name__)


class DocumentLoader:
    """Utility class to load a document from a URL."""

    @staticmethod
    async def from_uri(
        url: str,
        http_client: AsyncClient,
        auth_callback: Callable[..., Awaitable[dict[str, str]] | None] | None,
        user_agent: str | None = HTTP_USER_AGENT,
    ):
        """Load the manifest from the given URL."""
        if user_agent is None:
            user_agent = HTTP_USER_AGENT

        headers = {"User-Agent": user_agent}
        try:
            async with http_client as client:
                if auth_callback:
                    callback = auth_callback(client, url)
                    if isawaitable(callback):
                        await callback

                logger.info(f"Importing document from {url}")

                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.text
        except HTTPStatusError as ex:
            logger.error(f"Failed to get document: {ex}")
            raise ServiceInvalidRequestError("Failed to get document.") from ex
        except RequestError as ex:
            logger.error(f"Client error occurred: {ex}")
            raise ServiceInvalidRequestError("A client error occurred while getting the document.") from ex
        except Exception as ex:
            logger.error(f"An unexpected error occurred: {ex}")
            raise ServiceInvalidRequestError("An unexpected error occurred while getting the document.") from ex
