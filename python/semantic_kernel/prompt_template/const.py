# Copyright (c) Microsoft. All rights reserved.

from typing import Literal, Union

KERNEL_TEMPLATE_FORMAT_NAME: Literal["semantic-kernel"] = "semantic-kernel"
HANDLEBARS_TEMPLATE_FORMAT_NAME: Literal["handlebars"] = "handlebars"

TEMPLATE_FORMAT_TYPES = Union[type(KERNEL_TEMPLATE_FORMAT_NAME), type(HANDLEBARS_TEMPLATE_FORMAT_NAME)]
