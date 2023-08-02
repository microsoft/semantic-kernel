import os
from datetime import datetime

import numpy as np
import pytest

import semantic_kernel as sk
from semantic_kernel.connectors.memory.sqlite import SQLiteMemoryStore
from semantic_kernel.memory.memory_record import MemoryRecord

try:
    import aiosqlite

    aiosqlite_installed = True
except ImportError:
    aiosqlite_installed = False

pytestmark = pytest.mark.skipif(
    not aiosqlite_installed, reason="aiosqlite is not installed"
)


@pytest.fixture(scope="session")
def sqlite_db_file():
    if "Python_Integration_Tests" in os.environ:
        file = os.environ["SQLITE_DB_FILE"]
    else:
        try:
            file = sk.sqlite_settings_from_dot_env()
        except Exception:
            file = "sqlite_test.db"
    return file


@pytest.fixture
def memory_record1():
    return MemoryRecord(
        id="test_id1",
        text="sample text1",
        is_reference=False,
        embedding=np.array([0.5, 0.5]),
        description="description",
        additional_metadata="additional metadata",
        external_source_name="external source",
        timestamp=datetime.now(),
    )


@pytest.fixture
def memory_record2():
    return MemoryRecord(
        id="test_id2",
        text="sample text2",
        is_reference=False,
        embedding=np.array([0.25, 0.75]),
        description="description",
        additional_metadata="additional metadata",
        external_source_name="external source",
        timestamp=datetime.now(),
    )


@pytest.fixture
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
