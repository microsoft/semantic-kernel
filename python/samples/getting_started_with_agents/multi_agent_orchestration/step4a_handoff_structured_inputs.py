# Copyright (c) Microsoft. All rights reserved.

import asyncio
from enum import Enum

from pydantic import BaseModel

from semantic_kernel.agents import Agent, ChatCompletionAgent, HandoffOrchestration, OrchestrationHandoffs
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import AuthorRole, ChatMessageContent
from semantic_kernel.functions import kernel_function

"""
The following sample demonstrates how to create a handoff orchestration that can triage
GitHub issues based on their content. The orchestration consists of 3 agents, each
specialized in a different area.

The input to the orchestration is not longer a string or a chat message, but a Pydantic
model (i.e. structured inputs). The model will get transformed into a chat message before
being passed to the agents. This allows the orchestration to become more flexible and
easier reusable.

This sample demonstrates the basic steps of creating and starting a runtime, creating
a handoff orchestration, invoking the orchestration, and finally waiting for the results.
"""


class GitHubLabels(Enum):
    """Enum representing GitHub labels."""

    PYTHON = "python"
    DOTNET = ".NET"
    BUG = "bug"
    ENHANCEMENT = "enhancement"
    QUESTION = "question"
    VECTORSTORE = "vectorstore"
    AGENT = "agent"


class GithubIssue(BaseModel):
    """Model representing a GitHub issue."""

    id: str
    title: str
    body: str
    labels: list[str] = []


class Plan(BaseModel):
    """Model representing a plan for resolving a GitHub issue."""

    tasks: list[str]


class GithubPlugin:
    """Plugin for GitHub related operations."""

    @kernel_function
    async def add_labels(self, issue_id: str, labels: list[GitHubLabels]) -> None:
        """Add labels to a GitHub issue."""
        await asyncio.sleep(1)  # Simulate network delay
        print(f"Adding labels {labels} to issue {issue_id}")

    @kernel_function(description="Create a plan to resolve the issue.")
    async def create_plan(self, issue_id: str, plan: Plan) -> None:
        """Create tasks for a GitHub issue."""
        await asyncio.sleep(1)  # Simulate network delay
        print(f"Creating plan for issue {issue_id} with tasks:\n{plan.model_dump_json(indent=2)}")


def get_agents() -> tuple[list[Agent], OrchestrationHandoffs]:
    """Return a list of agents that will participate in the Handoff orchestration and the handoff relationships.

    Feel free to add or remove agents and handoff connections.
    """
    triage_agent = ChatCompletionAgent(
        name="TriageAgent",
        description="An agent that triages GitHub issues",
        instructions="Given a GitHub issue, triage it.",
        service=AzureChatCompletion(),
    )
    python_agent = ChatCompletionAgent(
        name="PythonAgent",
        description="An agent that handles Python related issues",
        instructions="You are an agent that handles Python related GitHub issues.",
        service=AzureChatCompletion(),
        plugins=[GithubPlugin()],
    )
    dotnet_agent = ChatCompletionAgent(
        name="DotNetAgent",
        description="An agent that handles .NET related issues",
        instructions="You are an agent that handles .NET related GitHub issues.",
        service=AzureChatCompletion(),
        plugins=[GithubPlugin()],
    )

    # Define the handoff relationships between agents
    handoffs = {
        triage_agent.name: {
            python_agent.name: "Transfer to this agent if the issue is Python related",
            dotnet_agent.name: "Transfer to this agent if the issue is .NET related",
        },
    }

    return [triage_agent, python_agent, dotnet_agent], handoffs


GithubIssueSample = GithubIssue(
    id="12345",
    title=(
        "Bug: SQLite Error 1: 'ambiguous column name:' when including VectorStoreRecordKey in "
        "VectorSearchOptions.Filter"
    ),
    body=(
        "Describe the bug"
        "When using column names marked as [VectorStoreRecordData(IsFilterable = true)] in "
        "VectorSearchOptions.Filter, the query runs correctly."
        "However, using the column name marked as [VectorStoreRecordKey] in VectorSearchOptions.Filter, the query "
        "throws exception 'SQLite Error 1: ambiguous column name: StartUTC"
        ""
        "To Reproduce"
        "Add a filter for the column marked [VectorStoreRecordKey]. Since that same column exists in both the "
        "vec_TestTable and TestTable, the data for both columns cannot be returned."
        ""
        "Expected behavior"
        "The query should explicitly list the vec_TestTable column names to retrieve and should omit the "
        "[VectorStoreRecordKey] column since it will be included in the primary TestTable columns."
        ""
        "Platform"
        ""
        "Microsoft.SemanticKernel.Connectors.Sqlite v1.46.0-preview"
        "Additional context"
        "Normal DBContext logging shows only normal context queries. Queries run by VectorizedSearchAsync() don't "
        "appear in those logs and I could not find a way to enable logging in semantic search so that I could "
        "actually see the exact query that is failing. It would have been very useful to see the failing semantic "
        "query."
    ),
    labels=[],
)


# The default input transform will attempt to serialize an object into a string by using
# `json.dump()`. However, an object of a Pydantic model type cannot be directly serialize
# by `json.dump()`. Thus, we will need a custom transform.
def custom_input_transform(input_message: GithubIssue) -> ChatMessageContent:
    return ChatMessageContent(role=AuthorRole.USER, content=input_message.model_dump_json())


async def main():
    """Main function to run the agents."""
    # 1. Create a handoff orchestration with multiple agents
    #    and a custom input transform.
    # To enable structured input, you must specify the input transform
    #   and the generic types for the orchestration,
    agents, handoffs = get_agents()
    handoff_orchestration = HandoffOrchestration[GithubIssue, ChatMessageContent](
        members=agents,
        handoffs=handoffs,
        input_transform=custom_input_transform,
    )

    # 2. Create a runtime and start it
    runtime = InProcessRuntime()
    runtime.start()

    # 3. Invoke the orchestration with a task and the runtime
    orchestration_result = await handoff_orchestration.invoke(
        task=GithubIssueSample,
        runtime=runtime,
    )

    # 4. Wait for the results
    value = await orchestration_result.get(timeout=100)
    print(value)

    # 5. Stop the runtime when idle
    await runtime.stop_when_idle()

    """
    Sample output:
    Adding labels [<GitHubLabels.BUG: 'bug'>, <GitHubLabels.DOTNET: '.NET'>, <GitHubLabels.VECTORSTORE: 'vectorstore'>]
        to issue 12345
    Creating plan for issue 12345 with tasks:
    {
    "tasks": [
        "Investigate the issue to confirm the ambiguity in the SQL query when using VectorStoreRecordKey in filters.",
        "Modify the query generation logic to explicitly list column names for vec_TestTable and prevent ambiguity.",
        "Test the solution to ensure VectorStoreRecordKey can be used in filters without causing SQLite errors.",
        "Update documentation to provide guidance on using VectorStoreRecordKey in filters to avoid similar issues.",
        "Consider adding logging capability to track semantic search queries for easier debugging in the future."
    ]
    }
    Task is completed with summary: No handoff agent name provided and no human response function set. Ending task.
    """


if __name__ == "__main__":
    asyncio.run(main())
