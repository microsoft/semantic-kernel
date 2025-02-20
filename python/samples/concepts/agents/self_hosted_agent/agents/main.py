# Copyright (c) Microsoft. All rights reserved.

import logging
import os
from abc import ABC
from typing import Any

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv
from fastapi import FastAPI
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_system_message_param import ChatCompletionSystemMessageParam
from pydantic import BaseModel, ConfigDict

load_dotenv()

app = FastAPI()

client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(), conn_str=os.environ["AZURE_AI_AGENT_PROJECT_CONNECTION_STRING"]
)

logger = logging.getLogger("custom_agent_logger")

REVIEWER_INSTRUCTIONS = """
You are an art director who has opinions about copywriting born of a love for David Ogilvy.
The goal is to determine if the given copy is acceptable to print.
If so, state that it is approved. Only include the word "approved" if it is so.
If not, provide insight on how to refine suggested copy without example.
"""

COPYWRITER_INSTRUCTIONS = """
You are a copywriter with ten years of experience and are known for brevity and a dry humor.
The goal is to refine and decide on the single best copy as an expert in the field.
Only provide a single proposal per response.
You're laser focused on the goal at hand.
Don't waste time with chit chat.
Consider suggestions when refining an idea.
"""


class APIRequestFormat(BaseModel, ABC):
    """Specific settings for the Chat Completion endpoint."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, validate_assignment=True)

    stream: bool = False
    messages: list[dict[str, Any]]
    parallel_tool_calls: bool | None = None
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | None = None


@app.post("/agent/reviewer")
async def reviewer_agent(request: APIRequestFormat) -> ChatCompletion:
    messages = request.messages
    logger.info("Financial Coach agent")
    logger.info(messages)
    openai = await client.inference.get_azure_openai_client(api_version="2024-06-01")
    # replace the system message in messages with custom system message
    if messages[0]["role"] == "system" or messages[0]["role"] == "developer":
        messages[0]["content"] = REVIEWER_INSTRUCTIONS
    else:
        messages = [ChatCompletionSystemMessageParam(role="system", content=REVIEWER_INSTRUCTIONS), *messages]

    return await openai.chat.completions.create(
        model=os.getenv("AZURE_AI_INFERENCE_MODEL_DEPLOYMENT_NAME") or "gpt-4o",
        messages=messages,
        **request.model_dump(exclude={"messages"}, exclude_none=True),
    )


@app.post("/agent/copywriter")
async def copywriter_agent(request: APIRequestFormat) -> ChatCompletion:
    messages = request.messages
    logger.info("Guardrail agent")
    logger.info(messages)
    openai = await client.inference.get_azure_openai_client(api_version="2024-06-01")
    # replace the system message in messages with custom system message
    if messages[0]["role"] == "system" or messages[0]["role"] == "developer":
        messages[0]["content"] = COPYWRITER_INSTRUCTIONS
    else:
        messages = [ChatCompletionSystemMessageParam(role="system", content=COPYWRITER_INSTRUCTIONS), *messages]

    return await openai.chat.completions.create(
        model=os.getenv("AZURE_AI_INFERENCE_MODEL_DEPLOYMENT_NAME") or "gpt-4o",
        messages=messages,
        **request.model_dump(exclude={"messages"}, exclude_none=True),
    )
