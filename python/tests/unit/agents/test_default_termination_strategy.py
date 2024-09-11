# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.agents.strategies.termination.default_termination_strategy import DefaultTerminationStrategy


@pytest.mark.asyncio
async def test_should_agent_terminate_():
    strategy = DefaultTerminationStrategy(maximum_iterations=2)
    result = await strategy.should_agent_terminate(None, [])
    assert not result
