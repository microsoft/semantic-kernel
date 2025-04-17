import asyncio

from microsoft.agents.copilotstudio.client import CopilotClient

from semantic_kernel.agents import CopilotStudioAgent


async def main() -> None:
    client: CopilotClient = CopilotStudioAgent.setup_resources()

    agent = CopilotStudioAgent(
        client=client,
        name="ContosoHelper",
        instructions="You are Contoso's support copilot. Answer politely & concisely.",
    )

    response = await agent.get_response(messages="Hello!  Who are you?")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
