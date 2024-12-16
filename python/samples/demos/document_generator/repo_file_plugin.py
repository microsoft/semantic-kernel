# Copyright (c) Microsoft. All rights reserved.

import os
from typing import Annotated

from semantic_kernel.functions import kernel_function


class RepoFilePlugin:
    """A plugin that reads files from this repository.

    This plugin assumes that the code is run within the Semantic Kernel repository.
    """

    @kernel_function(description="Read a file given a relative to the root of the repository.")
    def read_file_by_path(
        self, path: Annotated[str, "The relative path to the file."]
    ) -> Annotated[str, "Returns the file content."]:
        path = os.path.join(os.path.dirname(__file__), "..", "..", "..", path)

        try:
            with open(path) as file:
                return file.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File {path} not found in repository.")

    @kernel_function(
        description="Read a file given the name of the file. Function will search for the file in the repository."
    )
    def read_file_by_name(
        self, file_name: Annotated[str, "The name of the file."]
    ) -> Annotated[str, "Returns the file content."]:
        path = os.path.join(os.path.dirname(__file__), "..", "..", "..")
        for root, dirs, files in os.walk(path):
            if file_name in files:
                print(f"Found file {file_name} in {root}.")
                with open(os.path.join(root, file_name)) as file:
                    return file.read()
        raise FileNotFoundError(f"File {file_name} not found in repository.")
