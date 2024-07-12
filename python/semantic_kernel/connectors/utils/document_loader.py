# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import Callable
from typing import Any

import httpx

from semantic_kernel.connectors.telemetry import HTTP_USER_AGENT

logger: logging.Logger = logging.getLogger(__name__)


class DocumentLoader:

    @staticmethod
    async def from_uri(
        url: str,
        http_client: httpx.AsyncClient,
        auth_callback: Callable[[Any], None] | None,
        user_agent: str | None = HTTP_USER_AGENT,
    ):
        """Load the manifest from the given URL."""
        headers = {"User-Agent": user_agent}
        async with http_client as client:
            if auth_callback:
                await auth_callback(client, url)

            logger.info(f"Importing document from {url}")

            response = await client.get(url, headers=headers)
            response.raise_for_status()

            return response.text
