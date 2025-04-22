import asyncio

from azure.identity.aio import DefaultAzureCredential
from microsoft.agents.copilotstudio.client import CopilotClient

from semantic_kernel.agents import CopilotStudioAgent


async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
    ):
        token = (
            await creds.get_token(
                "https://api.powerplatform.com/.default"  # PP runtime scope
            )
        ).token
        client: CopilotClient = CopilotStudioAgent.setup_resources(
            token=token,
            agent_identifier="",
            environment_id="",
        )

        agent = CopilotStudioAgent(
            client=client,
            name="ContosoHelper",
            instructions="You are Contoso's support copilot. Answer politely & concisely.",
        )

        response = await agent.get_response(messages="Hello!  Who are you?")
        print(response)


if __name__ == "__main__":
    asyncio.run(main())
