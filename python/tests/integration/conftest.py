# Copyright (c) Microsoft. All rights reserved.

from pathlib import Path

import pytest

_INTEGRATION_DIR = Path(__file__).parent
# Memory tests for Azure services (e.g. Azure AI Search, Cosmos DB) use keys, not an Azure login.
_NO_AZURE_LOGIN_DIRS = [_INTEGRATION_DIR / "memory"]


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Add the `azure` marker to integration tests that need an Azure login.

    These are found by "azure" appearing in the test id (file, test or parameter name).
    """
    for item in items:
        path = Path(item.path)
        if not path.is_relative_to(_INTEGRATION_DIR):
            continue
        if any(path.is_relative_to(d) for d in _NO_AZURE_LOGIN_DIRS):
            continue
        if "azure" in item.nodeid.lower():
            item.add_marker(pytest.mark.azure)
