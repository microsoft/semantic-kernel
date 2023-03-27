import os

import aiofiles
from semantic_kernel.skill_definition.sk_function_context_parameter_decorator import (
    sk_function_context_parameter,
)
from python.semantic_kernel.orchestration.sk_context import SKContext
from python.semantic_kernel.skill_definition import sk_function


class FileIOSkill:
    """
    Description: Read and write from a file.

    Usage:
        kernel.import_skill("file", FileIOSkill());

    Examples:

    {{file.readAsync $path }} => "hello world"
    {{file.writeAsync}}
    """

    @sk_function(
        description="Read a file",
        input_description="Path of the source file",
    )
    async def read_async(self, path: str) -> str:
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

    @sk_function(description="Write a file")
    @sk_function_context_parameter(name="path", description="Destination path")
    @sk_function_context_parameter(name="content", description="File content")
    async def write_async(self, context: SKContext):
        """
        Write a file

        Example:
            {{file.writeAsync}}
        Args:
            Contains the 'path' for the Destination file and 'content' of the file to write.

        Returns:
            The contents of the file
        """
        path = context.get("path")
        content = context.get("content")

        assert content is not None, "Content is required"
        assert path is not None, "Path is required"

        async with aiofiles.open(path, "w") as fp:
            await fp.write(content)
