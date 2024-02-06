# Copyright (c) Microsoft. All rights reserved.

import os
import typing as t

import aiofiles

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.plugin_definition import kernel_function, kernel_function_context_parameter

if t.TYPE_CHECKING:
    from semantic_kernel.orchestration.kernel_context import KernelContext


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
        input_description="Path of the source file",
    )
    async def read(self, path: str) -> str:
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
    @kernel_function_context_parameter(name="path", description="Destination path")
    @kernel_function_context_parameter(name="content", description="File content")
    async def write(self, context: "KernelContext") -> None:
        """
        Write a file

        Example:
            {{file.writeAsync}}
        Args:
            Contains the 'path' for the Destination file and
            the 'content' of the file to write.
        """
        path = context.variables.get("path")
        content = context.variables.get("content")

        assert path, "Path is required"
        assert content, "Content is required"

        async with aiofiles.open(path, "w") as fp:
            await fp.write(content)
