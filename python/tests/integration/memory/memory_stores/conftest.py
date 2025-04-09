# Copyright (c) Microsoft. All rights reserved.


from datetime import datetime

import numpy as np
import pytest

from semantic_kernel.memory.memory_record import MemoryRecord


@pytest.fixture(scope="module")
def memory_record1():
    return MemoryRecord(
        id="test_id1",
        text="sample text1",
        is_reference=False,
        embedding=np.array([0.5, 0.5]),
        description="description",
        external_source_name="external source",
        additional_metadata="additional metadata",
        timestamp=datetime.now(),
    )


@pytest.fixture(scope="module")
def memory_record2():
    return MemoryRecord(
        id="test_id2",
        text="sample text2",
        is_reference=False,
        embedding=np.array([0.25, 0.75]),
        description="description",
        external_source_name="external source",
        additional_metadata="additional metadata",
        timestamp=datetime.now(),
    )


@pytest.fixture(scope="module")
def memory_record3():
    return MemoryRecord(
        id="test_id3",
        text="sample text3",
        is_reference=False,
        embedding=np.array([0.25, 0.80]),
        description="description",
        additional_metadata="additional metadata",
        external_source_name="external source",
        timestamp=datetime.now(),
    )
