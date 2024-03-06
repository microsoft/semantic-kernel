# Copyright (c) Microsoft. All rights reserved.


def read_file(file_path: str) -> str:
    """Read the given configuration or file
    related to the FunctionCallingStepwisePlanner"""
    with open(file_path, "r") as file:
        return file.read()
