# Copyright (c) Microsoft. All rights reserved.
import asyncio

from pydantic import BaseModel

from semantic_kernel.agents.open_ai import AzureAssistantAgent

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
    model=model,
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
    client, model = AzureAssistantAgent.setup_resources()

    # Create the assistant definition
    definition = await client.beta.assistants.create(
        model=model,
        name="Assistant",
        instructions="You are a helpful assistant answering questions about the world in one sentence.",
        response_format=AzureAssistantAgent.configure_response_format(ResponseModel),
    )

    # Create the AzureAssistantAgent instance using the client and the assistant definition
    agent = AzureAssistantAgent(
        client=client,
        definition=definition,
    )

    # Define a thread and invoke the agent with the user input
    thread = await agent.client.beta.threads.create()

    user_inputs = ["Why is the sky blue?"]

    try:
        for user_input in user_inputs:
            await agent.add_chat_message(thread_id=thread.id, message=user_input)
            print(f"# User: '{user_input}'")
            async for content in agent.invoke(thread_id=thread.id):
                # The response returned is a Pydantic Model, so we can validate it using the model_validate_json method
                response_model = ResponseModel.model_validate_json(content.content)
                print(f"# {content.role}: {response_model}")
    finally:
        await client.beta.threads.delete(thread.id)
        await client.beta.assistants.delete(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
