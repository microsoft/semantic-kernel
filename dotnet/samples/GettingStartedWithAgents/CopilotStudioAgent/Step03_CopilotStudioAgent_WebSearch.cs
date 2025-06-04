// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Agents.CopilotStudio.Client;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Copilot;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted.CopilotStudioAgents;

/// <summary>
/// Demonstrates how to use a Copilot Studio Agent with a persistent conversation thread
/// to perform web search queries and retrieve responses in a .NET test scenario.
/// </summary>
/// <remarks>
/// In Copilot Studio, for the specified agent, you must enable the "Web Search" capability.
/// If not already enabled, make sure to(re-)publish the agent so the changes take effect.
/// </remarks>
public sealed class Step03_CopilotStudioAgent_WebSearch(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public async Task UseCopilotStudioAgentThread()
    {
        CopilotStudioConnectionSettings settings = new(TestConfiguration.GetSection(nameof(CopilotStudioAgent)));
        CopilotClient client = CopilotStudioAgent.CreateClient(settings);
        CopilotStudioAgent agent = new(client);
        CopilotStudioAgentThread thread = new(client);

        await InvokeAgentAsync("Which team won the 2025 NCAA Basketball championship?");
        await InvokeAgentAsync("What was the final score?");

        // Local function to invoke agent and display the response.
        async Task InvokeAgentAsync(string input)
        {
            Console.WriteLine($"\n# {AuthorRole.User}: {input}");

            await foreach (ChatMessageContent response in agent.InvokeAsync(input, thread))
            {
                WriteAgentChatMessage(response);
            }
        }
    }
}
