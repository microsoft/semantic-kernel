# Copyright (c) Microsoft. All rights reserved.

import os

SAMPLE_PLUGIN_FOLDER = "prompt_template_samples"


def get_sample_plugin_path(max_depth: int = 10) -> str | None:
    """Find the path to the sample plugin folder.

    Args:
        max_depth (int, optional): The maximum depth to search for the sample plugin folder. Defaults to 10.
    Returns:
        str | None: The path to the sample plugin folder or None if not found.
    """
    curr_dir = os.path.dirname(os.path.abspath(__file__))

    found = False
    for _ in range(max_depth):
        if SAMPLE_PLUGIN_FOLDER in os.listdir(curr_dir):
            found = True
            break
        curr_dir = os.path.dirname(curr_dir)

    if found:
        return os.path.join(curr_dir, SAMPLE_PLUGIN_FOLDER)
    return None
