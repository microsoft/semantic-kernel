# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.kernel_extensions.import_skills import ImportSkills
from semantic_kernel.kernel_extensions.inline_definition import InlineDefinition
from semantic_kernel.kernel_extensions.memory_configuration import MemoryConfiguration


class KernelExtensions(
    ImportSkills,
    InlineDefinition,
    MemoryConfiguration,
):
    """
    This class is a container for all the kernel extensions.

    The kernel extensions are a set of functions that can be
    used to extend the functionality of the kernel. The way this
    is written intends to somewhat replicate C#'s extensions
    methods (while preserving some amount of type checking).
    """
