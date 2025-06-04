# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.core_plugins.web_search_engine_plugin import WebSearchEnginePlugin


@pytest.fixture
def connector():
    from semantic_kernel.connectors.search_engine.connector import ConnectorBase

    class MockConnector(ConnectorBase):
        async def search(self, query: str, num_results: int, offset: int) -> list[str]:
            return ["result1", "result2"]

    return MockConnector()


def test_can_be_instantiated(connector):
    assert WebSearchEnginePlugin(connector)


async def test_search(connector):
    plugin = WebSearchEnginePlugin(connector)
    results = await plugin.search("test")
    assert results == ["result1", "result2"]
