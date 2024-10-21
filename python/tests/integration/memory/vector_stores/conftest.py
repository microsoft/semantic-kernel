# Copyright (c) Microsoft. All rights reserved.

from copy import deepcopy

import pytest

RAW_RECORD = {
    "id": "e6103c03-487f-4d7d-9c23-4723651c17f4",
    "content": "test content",
    "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
}


@pytest.fixture
def record():
    return deepcopy(RAW_RECORD)
