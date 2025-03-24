# Copyright (c) Microsoft. All rights reserved.

import os
from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from semantic_kernel.agents import OpenAIAssistantAgent
    from semantic_kernel.contents import AnnotationContent, StreamingAnnotationContent


async def download_file_content(agent: "OpenAIAssistantAgent", file_id: str, file_extension: str):
    """A sample utility method to download the content of a file."""
    try:
        # Fetch the content of the file using the provided method
        response_content = await agent.client.files.content(file_id)

        # Get the current working directory of the file
        current_directory = os.path.dirname(os.path.abspath(__file__))

        # Define the path to save the image in the current directory
        file_path = os.path.join(
            current_directory,  # Use the current directory of the file
            f"{file_id}.{file_extension}",  # You can modify this to use the actual filename with proper extension
        )

        # Save content to a file asynchronously
        with open(file_path, "wb") as file:
            file.write(response_content.content)

        print(f"\n\nFile saved to: {file_path}")
    except Exception as e:
        print(f"An error occurred while downloading file {file_id}: {str(e)}")


async def download_response_images(agent: "OpenAIAssistantAgent", file_ids: list[str]):
    """A sample utility method to download the content of a list of files."""
    if file_ids:
        # Iterate over file_ids and download each one
        for file_id in file_ids:
            await download_file_content(agent, file_id, "png")


async def download_response_files(
    agent: "OpenAIAssistantAgent", annotations: Sequence["StreamingAnnotationContent | AnnotationContent"]
):
    """A sample utility method to download the content of a file."""
    if annotations:
        # Iterate over file_ids and download each one
        for ann in annotations:
            if ann.quote is None or ann.file_id is None:
                continue
            extension = os.path.splitext(ann.quote)[1].lstrip(".")
            await download_file_content(agent, ann.file_id, extension)
