# Copyright (c) Microsoft. All rights reserved.

import os
import sys
import typing as t

import aiofiles

if sys.version_info > (3, 8):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel

if t.TYPE_CHECKING:
    pass


class FileIOPlugin(KernelBaseModel):
    """
    Description: Read and write from a file.

    Usage:
        kernel.import_plugin(FileIOPlugin(), plugin_name="file")

    Examples:

    {{file.readAsync $path }} => "hello world"
    {{file.writeAsync}}
    """

    @kernel_function(
        description="Read a file",
        name="readAsync",
    )
    async def read(self, path: Annotated[str, "Path of the source file"]) -> str:
        """
        Read a file

        Example:
            {{file.readAsync $path }} => "hello world"
        Args:
            path -- The path to the file to read

        Returns:
            The contents of the file
        """

        assert os.path.exists(path), f"File {path} does not exist"

        async with aiofiles.open(path, "r", encoding="UTF-8") as fp:
            content = await fp.read()
            return content

    @kernel_function(
        description="Write a file",
        name="writeAsync",
    )
    async def write(self, path: Annotated[str, "Destination path"], content: Annotated[str, "File content"]) -> None:
        """
        Write a file

        Example:
            {{file.writeAsync path=$path content=$content}}
        Args:
            Contains the 'path' for the Destination file and
            the 'content' of the file to write.
        """
        async with aiofiles.open(path, "w") as fp:
            await fp.write(content)
