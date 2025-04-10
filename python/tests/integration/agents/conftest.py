# Copyright (c) Microsoft. All rights reserved.

import pytest

from tests.integration.agents.agent_test_base import AgentTestBase, ChatAgentProtocol


@pytest.fixture
def agent_test_base() -> AgentTestBase[ChatAgentProtocol]:
    """Provides a single AgentTestBase instance that all tests can use.

    Typed as a Generic over any ChatAgentProtocol.
    """
    return AgentTestBase()
