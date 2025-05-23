# Copyright (c) Microsoft. All rights reserved.
import asyncio

from pydantic import BaseModel

from semantic_kernel.agents import AssistantAgentThread, AzureAssistantAgent
from semantic_kernel.connectors.ai.open_ai import AzureOpenAISettings

"""
The following sample demonstrates how to create an OpenAI
assistant using either Azure OpenAI or OpenAI and leverage the
assistant's ability to returned structured outputs, based on a user-defined
Pydantic model. This could also be a non-Pydantic model. Use the convenience
method on the OpenAIAssistantAgent class to configure the response format,
as shown below.

Note, you may specify your own JSON Schema. You'll need to make sure it is correct
if not using the convenience method, per the following format:

json_schema = {
    "type": "json_schema",
    "json_schema": {
        "schema": {
            "properties": {
                "response": {"title": "Response", "type": "string"},
                "items": {"items": {"type": "string"}, "title": "Items", "type": "array"},
            },
            "required": ["response", "items"],
            "title": "ResponseModel",
            "type": "object",
            "additionalProperties": False,
        },
        "name": "ResponseModel",
        "strict": True,
    },
}

# Create the assistant definition
definition = await client.beta.assistants.create(
    model=AzureOpenAISettings().chat_deployment_name
    name="Assistant",
    instructions="You are a helpful assistant answering questions about the world in one sentence.",
    response_format=json_schema,
)
"""


# Define a Pydantic model that represents the structured output from the OpenAI service
class ResponseModel(BaseModel):
    response: str
    items: list[str]


async def main():
    # Create the client using Azure OpenAI resources and configuration
    client = AzureAssistantAgent.create_client()

    # Create the assistant definition
    definition = await client.beta.assistants.create(
        model=AzureOpenAISettings().chat_deployment_name,
        name="Assistant",
        instructions="You are a helpful assistant answering questions about the world in one sentence.",
        response_format=AzureAssistantAgent.configure_response_format(ResponseModel),
    )

    # Create the AzureAssistantAgent instance using the client and the assistant definition
    agent = AzureAssistantAgent(
        client=client,
        definition=definition,
    )

    # Create a new thread for use with the assistant
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread: AssistantAgentThread = None

    user_inputs = ["Why is the sky blue?"]

    try:
        for user_input in user_inputs:
            print(f"# User: '{user_input}'")
            async for response in agent.invoke(messages=user_input, thread=thread):
                # The response returned is a Pydantic Model, so we can validate it using the model_validate_json method
                response_model = ResponseModel.model_validate_json(str(response.content))
                print(f"# {response.role}: {response_model}")
                thread = response.thread
    finally:
        await thread.delete() if thread else None
        await client.beta.assistants.delete(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
