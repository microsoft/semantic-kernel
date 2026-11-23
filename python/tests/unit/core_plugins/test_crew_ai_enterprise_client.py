# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import MagicMock

import aiohttp
import pytest
from yarl import URL

from semantic_kernel.core_plugins.crew_ai.crew_ai_enterprise_client import CrewAIEnterpriseClient
from semantic_kernel.core_plugins.crew_ai.crew_ai_models import CrewAIEnterpriseKickoffState


@pytest.fixture
def crew_ai_client():
    client = CrewAIEnterpriseClient(endpoint="https://test.com", auth_token="FakeToken")
    client.session = MagicMock(spec=aiohttp.ClientSession)
    return client


@pytest.mark.parametrize(
    "task_id",
    ["12345", "AZaz09_-", "640f9a3a-2734-4ba8-8b8a-2f796f419d03"],
)
async def test_get_status_preserves_valid_task_id(crew_ai_client, task_id):
    response = MagicMock(spec=aiohttp.ClientResponse)
    response.text.return_value = '{"state":"SUCCESS","result":"The Result"}'
    crew_ai_client.session.get.return_value.__aenter__.return_value = response

    result = await crew_ai_client.get_status(task_id)

    assert result.state == CrewAIEnterpriseKickoffState.Success
    assert result.result == "The Result"
    crew_ai_client.session.get.assert_called_once_with(
        f"https://test.com/status/{task_id}",
        headers=crew_ai_client.request_header,
    )
    request_url = crew_ai_client.session.get.call_args.args[0]
    assert URL(request_url).raw_path == f"/status/{task_id}"
    response.raise_for_status.assert_called_once()


@pytest.mark.parametrize(
    "task_id",
    [
        None,
        123,
        [],
        "",
        " ",
        "task.id",
        "task/id",
        r"task\id",
        "task%id",
        "task?id",
        "task#id",
        "task id",
        "task\n",
        "task\r\n",
        "task\t",
        "task\x00",
        "t\u00e1sk",
        "\uff11\uff12\uff13",
    ],
)
async def test_get_status_rejects_invalid_task_id_without_request(crew_ai_client, task_id):
    with pytest.raises(
        ValueError,
        match="Task ID must contain only ASCII letters, digits, underscores, or hyphens",
    ):
        await crew_ai_client.get_status(task_id)

    crew_ai_client.session.get.assert_not_called()
