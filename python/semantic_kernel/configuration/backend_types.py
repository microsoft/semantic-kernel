# Copyright (c) Microsoft. All rights reserved.

import enum


class BackendType(enum.Enum):
    Unknown = -1
    AzureOpenAI = 0
    OpenAI = 1
