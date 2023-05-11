# Copyright (c) Microsoft. All rights reserved.

import os
import aiohttp
import aiofiles

from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter


class WebFileDownloadSkill:

    @sk_function(description="Downloads a file to local storage", name="downloadToFile")
    @sk_function_context_parameter(name="filePath", description="Path where to save file locally")
    async def download_to_file(self, url: str, context: SKContext):
        _, file_path = context.variables.get("filePath")

        if not file_path:
            raise ValueError("File path cannot be `None` or empty")

        async with aiohttp.ClientSession() as session, \
                session.get(url, raise_for_status=True) as response:

            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(await response.read())
