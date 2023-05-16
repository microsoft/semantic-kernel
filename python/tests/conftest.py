import platform

import pytest


def pytest_collection_modifyitems(config, items):
    if platform.system() != "Linux":
        for item in items:
            if (
                item.parent
                and item.parent.name
                == "integration/connectors/memory/test_weaviate_memory_store.py"
            ):
                item.add_marker(
                    pytest.mark.skip(
                        reason="test_weaviate_memory_store uses embedded weaviate which only runs on Linux at the moment"
                    )
                )
