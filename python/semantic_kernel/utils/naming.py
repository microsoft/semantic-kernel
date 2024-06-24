# Copyright (c) Microsoft. All rights reserved.

import random
import string


def generate_random_ascii_name(length: int = 16) -> str:
    """Generate a series of random ASCII characters of the specified length.

    As example, plugin/function names can contain upper/lowercase letters, and underscores

    Args:
        length (int): The length of the string to generate.

    Returns:
        A string of random ASCII characters of the specified length.
    """
    letters = string.ascii_letters
    return "".join(random.choices(letters, k=length))  # nosec
