// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;

namespace GettingStarted.OpenAIResponseAgents;

/// <summary>
/// This example demonstrates using <see cref="OpenAIResponseAgent"/>.
/// </summary>
public class Step03_OpenAIResponseAgent_ReasoningModel(ITestOutputHelper output) : BaseResponsesAgentTest(output, "o4-mini")
{
    [Fact]
    public async Task UseOpenAIResponseAgentWithAReasoningModelAsync()
    {
        // Define the agent
        OpenAIResponseAgent agent = new(this.Client)
        {
            Name = "ResponseAgent",
            Instructions = "Answer all queries with a detailed response.",
        };

        // Invoke the agent and output the response
        var responseItems = agent.InvokeAsync("Which of the last four Olympic host cities has the highest average temperature?");
        await foreach (ChatMessageContent responseItem in responseItems)
        {
            WriteAgentChatMessage(responseItem);
        }
    }
}
