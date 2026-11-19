# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Union

from semantic_kernel.utils.feature_stage_decorator import experimental

__all__ = [
    "MCPToolApprovalCallback",
    "MCPToolApprovalRequest",
]


@experimental
@dataclass
class MCPToolApprovalRequest:
    """A request to approve or deny a single MCP tool call.

    The Azure AI Foundry Agent Service pauses a run and asks the caller to approve
    MCP tool calls when the MCP tool is registered with `require_approval="always"`.
    One instance of this class is passed to the configured approval callback per
    pending tool call.
    """

    agent_name: str
    thread_id: str
    run_id: str
    tool_call_id: str
    server_label: str
    function_name: str
    arguments: str


MCPToolApprovalCallback = Callable[[MCPToolApprovalRequest], Union[bool, Awaitable[bool]]]
